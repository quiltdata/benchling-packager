import io
import json
import os
import pathlib
import tempfile
import zipfile
from urllib import request as urllib_request

import jinja2
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities import parameters
from benchling_sdk import models as benchling_models
from benchling_sdk.auth.client_credentials_oauth2 import ClientCredentialsOAuth2
from benchling_sdk.benchling import Benchling
from benchling_sdk.helpers import serialization_helpers
from botocore import exceptions as botocore_exceptions

# Must be done before importing quilt3
os.environ["QUILT_DISABLE_CACHE"] = "true"
import quilt3  # noqa: E402

logger = Logger()


class BenchlingClient:
    BENCHLING_TENANT = os.environ["BENCHLING_TENANT"]
    BENCHLING_CLIENT_ID = os.environ["BENCHLING_CLIENT_ID"]
    BENCHLING_CLIENT_SECRET_ARN = os.environ["BENCHLING_CLIENT_SECRET_ARN"]

    @classmethod
    def Default(cls):
        return cls(
            cls.BENCHLING_TENANT,
            cls.BENCHLING_CLIENT_ID,
            cls.BENCHLING_CLIENT_SECRET_ARN,
        )

    def __init__(self, tenant, id, arn):
        if not isinstance(arn, str):
            raise Exception("Failed to fetch CLIENT_SECRET_ARN")
        secret = parameters.get_secret(arn)
        if not isinstance(secret, str):
            raise Exception(f"Failed to fetch secret: {arn!r}")
        self.benchling = Benchling(
            url=f"https://{tenant}.benchling.com",
            auth_method=ClientCredentialsOAuth2(
                client_id=id,
                client_secret=secret,
            ),
        )

    def get_task(self, entry_id):
        self.task = self.benchling.tasks.wait_for_task(
            self.benchling.exports.export(
                benchling_models.ExportItemRequest(_id=entry_id)
            ).task_id
        )
        if self.task.status != benchling_models.AsyncTaskStatus.SUCCEEDED:
            raise Exception(f"Notes export failed: {self.task!r}")
        return self.task

    def update_entry(self, entry_id, fields_values):
        values = {k: {"value": v} for k, v in fields_values.items()}
        self.benchling.entries.update_entry(
            entry_id,
            benchling_models.EntryUpdate(_fields=serialization_helpers.fields(values)),
        )


class BenchlingEntry:
    QUILT_SUMMARIZE = json.dumps(
        [
            [
                {
                    "path": "entry.md",
                    "width": "calc(40% - 16px)",
                    "expand": True,
                },
                {
                    "path": "notes.pdf",
                    "width": "calc(60% - 16px)",
                    "expand": True,
                },
            ]
        ]
    )

    ENTRY_FMT = """
# [{{ entry.name }}]({{ entry.webURL }})

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

    DST_BUCKET = os.environ["DST_BUCKET"]
    PKG_PREFIX = os.environ["PKG_PREFIX"]
    QUILT_CATALOG_DOMAIN = os.environ["QUILT_CATALOG_DOMAIN"]
    QUILT_PREFIX = f"https://{QUILT_CATALOG_DOMAIN}/b/{DST_BUCKET}/packages"

    def __init__(self, entry):
        self.client = BenchlingClient.Default()
        self.entry = entry
        self.entry_id = entry["id"]
        self.fields = entry["fields"]
        self.pkg_name = self.PKG_PREFIX + entry["displayId"]

    def format(self):
        template = jinja2.Template(self.ENTRY_FMT)
        return template.render({"entry": self.entry})

    def dump(self):
        return json.dumps(self.entry)

    def write_notes(self, tmpdir_path):
        task = self.client.get_task(self.entry_id)

        with urllib_request.urlopen(task.response["downloadURL"]) as src:
            buf = io.BytesIO(src.read())

        with zipfile.ZipFile(buf) as zip_file:
            with zip_file.open(zip_file.namelist()[0]) as src:
                with (tmpdir_path / "notes.pdf").open("wb") as dst:
                    while data := src.read(4096):
                        dst.write(data)

    def write(self, tmpdir_path):
        self.write_notes(tmpdir_path)
        (tmpdir_path / "entry.md").write_text(self.format())
        (tmpdir_path / "entry.json").write_text(self.dump())
        (tmpdir_path / "quilt_summarize.json").write_text(self.QUILT_SUMMARIZE)

    def make_package(self, tmpdir_path):
        registry = f"s3://{self.DST_BUCKET}"
        pkg = quilt3.Package()
        try:
            pkg = quilt3.Package.browse(self.pkg_name, registry=registry)
        except botocore_exceptions.ClientError as e:
            # XXX: quilt3 should raise some specific exception
            # when package doesn't exist.
            if e.response["Error"]["Code"] not in ("NoSuchKey", "404"):
                raise

        pkg.set_dir(".", tmpdir_path, meta=self.entry)
        # This shouldn't hit 1 MB limit on metadata,
        # because max size of EventBridge is 256 KiB.
        pkg.push(self.pkg_name, registry=registry)

    def field_values(self):
        FIELD_URI = "Quilt+ URI"
        FIELD_CATALOG = "Quilt Catalog URL"
        FIELD_REVISE = "Quilt Revise URL"
        REVISE = "action=revisePackage"
        values = {}
        if FIELD_URI in self.fields:
            values[FIELD_URI] = f"quilt+s3://{self.DST_BUCKET}#package={self.pkg_name}"
        if FIELD_CATALOG in self.fields:
            values[FIELD_CATALOG] = f"{self.QUILT_PREFIX}/{self.pkg_name}"
        if FIELD_REVISE in self.fields:
            values[FIELD_REVISE] = f"{self.QUILT_PREFIX}/{self.pkg_name}?{REVISE}"
        return values

    def update_benchling_notebook(self):
        values = self.field_values()
        if values:
            self.client.update_entry(self.entry_id, values)
            logger.debug(f"Updated entry {self.entry_id} with package {self.pkg_name}")
        else:
            logger.warning(f"Quilt schema fields not found for entry {self.entry_id!r}")


@logger.inject_lambda_context
def lambda_handler(event, context):
    entry = BenchlingEntry(event["detail"]["entry"])

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = pathlib.Path(tmpdir)

        entry.write(tmpdir_path)
        entry.make_package(tmpdir_path)
        entry.update_benchling_notebook()

    return {
        "statusCode": 200,
    }
