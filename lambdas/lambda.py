import io
import os
import pathlib
import tempfile
import urllib
import zipfile

import jinja2
import quilt3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities import parameters
from benchling_sdk import models as benchling_models
from benchling_sdk.auth.client_credentials_oauth2 import ClientCredentialsOAuth2
from benchling_sdk.benchling import Benchling
from benchling_sdk.helpers import serialization_helpers

logger = Logger()


BENCHLING_TENANT = os.environ["BENCHLING_TENANT"]
BENCHLING_CLIENT_ID = os.environ["BENCHLING_CLIENT_ID"]
BENCHLING_CLIENT_SECRET_ARN = os.environ["BENCHLING_CLIENT_SECRET_ARN"]
DST_BUCKET = os.environ["DST_BUCKET"]
PKG_PREFIX = os.environ["PKG_PREFIX"]
QUILT_CATALOG_URL = os.environ["QUILT_CATALOG_URL"]


benchling = Benchling(
    url=BENCHLING_TENANT,
    auth_method=ClientCredentialsOAuth2(
        client_id=BENCHLING_CLIENT_ID,
        client_secret=parameters.get_secret(BENCHLING_CLIENT_SECRET_ARN),
        token_url=f"{BENCHLING_TENANT}/api/v2/token",
    ),
)


template = jinja2.Template(
    """# [{{ entry.name }}]({{ entry.webURL }})

* id: {{ entry.id }}
* displayId: {{ entry.displayId }}
* folderId: {{ entry.folderId }}
* createdAt: {{ entry.createdAt }}
* modifiedAt: {{ entry.modifiedAt }}

## Authors
{% for author in entry.authors %}
* {{ author.name }}
  * id: {{ author.id }}
  * handle: {{ author.handle }}
{%- endfor %}

## Schema

* id: {{ entry.schema.id }}
* name: {{ entry.schema.name }}

## Fields
{% for name, value in entry.fields.items() %}
* {{ name }}: {{ value.displayValue }}
{%- endfor %}

## Custom fields
{% for name, value in entry.customFields.items() %}
* {{ name }}: {{ value.value }}
{%- endfor %}
"""
)


QUILT_SUMMARIZE = """[
    "notes.pdf"
]
"""


@logger.inject_lambda_context
def lambda_handler(event, context):
    entry = event["detail"]["entry"]
    task = benchling.tasks.wait_for_task(
        benchling.exports.export(
            benchling_models.ExportItemRequest(id=entry["id"])
        ).task_id
    )
    if task.status != benchling_models.AsyncTaskStatus.SUCCEEDED:
        raise Exception(f"Notes export failed: {task!r}")

    with urllib.request.urlopen(task.response["downloadURL"]) as src:
        buf = io.BytesIO(src.read())

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = pathlib.Path(tmpdir)

        (tmpdir_path / "README.md").write_text(template.render({"entry": entry}))

        with zipfile.ZipFile(buf) as zip_file:
            with zip_file.open(zip_file.namelist()[0]) as src:
                with (tmpdir_path / "notes.pdf").open('wb') as dst:
                    while data := src.read(4096):
                        dst.write(data)

        (tmpdir_path / "quilt_summarize.json").write_text(QUILT_SUMMARIZE)

        pkg_name = PKG_PREFIX + entry["displayId"]
        quilt3.Package().set_dir(
            ".",
            tmpdir_path,
            # This shouldn't hit 1 MB limit on metadata, because max size of EventBridge is 256 KiB.
            meta=entry,
        ).push(
            pkg_name,
            registry=f"s3://{DST_BUCKET}",
            force=True,  # FIXME
        )

        fields_values = {}
        if "Quilt+ URI" in entry["fields"]:
            fields_values["Quilt+ URI"] = f"quilt+s3://{DST_BUCKET}#package={pkg_name}"
        if "Quilt Catalog URL" in entry["fields"]:
            fields_values[
                "Quilt Catalog URL"
            ] = f"{QUILT_CATALOG_URL}/b/{DST_BUCKET}/packages/{pkg_name}"
        # TODO: check that this URL is correct
        if "Quilt DropZone URL" in entry["fields"]:
            fields_values[
                "Quilt DropZone URL"
            ] = f"{QUILT_CATALOG_URL}/b/{DST_BUCKET}/packages/{pkg_name}/?createPackage=true&dropZoneOnly=true&msg=Commit+Message"

        if fields_values:
            benchling.entries.update_entry(
                event["detail"]["entry"]["id"],
                benchling_models.EntryUpdate(
                    fields=serialization_helpers.fields(
                        {
                            name: {"value": value}
                            for name, value in fields_values.items()
                        }
                    )
                ),
            )
