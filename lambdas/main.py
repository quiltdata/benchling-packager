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
            self.benchling.exports.export(benchling_models.ExportItemRequest(id=entry_id)).task_id  # type: ignore
        )
        if self.task.status != benchling_models.AsyncTaskStatus.SUCCEEDED:
            raise Exception(f"Notes export failed: {self.task!r}")
        return self.task

    def update_entry(self, entry_id, fields_values):
        values = {k: {"value": v} for k, v in fields_values.items()}
        fields = serialization_helpers.fields(values)
        self.benchling.entries.update_entry(
            entry_id,
            benchling_models.EntryUpdate(fields=fields),  # type: ignore
        )


class BenchlingEntry:
    REVISE = "action=revisePackage"

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

    FIELDS = {
        "QUILT_URI": "Quilt+ URI",
        "CATALOG_URL": "Quilt Catalog URL",
        "REVISE_URL": "Quilt Revise URL",
    }

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
        self.fields = entry.get("fields", {})
        self.pkg_name = self.name()
        self.registry = f"s3://{self.DST_BUCKET}"

    def name(self):
        SEP = "/"
        if SEP not in self.PKG_PREFIX:
            self.PKG_PREFIX += SEP
        return self.PKG_PREFIX + self.entry.get("displayId", self.entry_id)

    def format(self):
        template = jinja2.Template(self.ENTRY_FMT)
        return template.render({"entry": self.entry})

    def dump(self):
        return json.dumps(self.entry)

    def write_notes(self, tmpdir_path):
        outfile = tmpdir_path / "notes.pdf"
        task = self.client.get_task(self.entry_id)

        with urllib_request.urlopen(task.response["downloadURL"]) as src:
            buf = io.BytesIO(src.read())

        with zipfile.ZipFile(buf) as zip_file:
            with zip_file.open(zip_file.namelist()[0]) as src:
                with outfile.open("wb") as dst:
                    while data := src.read(4096):
                        dst.write(data)
        return outfile

    def write_files(self, tmpdir_path):
        self.write_notes(tmpdir_path)
        (tmpdir_path / "entry.md").write_text(self.format())
        (tmpdir_path / "entry.json").write_text(self.dump())
        (tmpdir_path / "quilt_summarize.json").write_text(self.QUILT_SUMMARIZE)

    def push_package(self, tmpdir_path):
        pkg = quilt3.Package()
        try:
            pkg = quilt3.Package.browse(self.pkg_name, registry=self.registry)
            # see if package name already exists; otherwise use default
        except botocore_exceptions.ClientError as e:
            if e.response["Error"]["Code"] not in ("NoSuchKey", "404"):
                raise

        pkg.set_dir(".", tmpdir_path, meta=self.entry)
        # This shouldn't hit 1 MB limit on metadata,
        # because max size of EventBridge is 256 KiB.
        return pkg.push(self.pkg_name, registry=self.registry)

    def field_values(self):
        values = {
            "QUILT_URI": f"quilt+s3://{self.DST_BUCKET}#package={self.pkg_name}",
            "CATALOG_URL": f"{self.QUILT_PREFIX}/{self.pkg_name}",
            "REVISE_URL": f"{self.QUILT_PREFIX}/{self.pkg_name}?{self.REVISE}",
        }
        return {f: values.get(k) for k, f in self.FIELDS.items()}

    def update_benchling_notebook(self) -> bool:
        values = self.field_values()
        if values:
            self.client.update_entry(self.entry_id, values)
            logger.debug(f"Updated entry {self.entry_id} with package {self.pkg_name}")
            return True
        else:
            logger.warning(f"Quilt schema fields not found for entry {self.entry_id!r}")
            return False


def main(entry_dict):
    entry = BenchlingEntry(entry_dict)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = pathlib.Path(tmpdir)

        entry.write_files(tmpdir_path)
        entry.push_package(tmpdir_path)
        entry.update_benchling_notebook()
    return entry


@logger.inject_lambda_context
def lambda_handler(event, context):
    main(event["detail"]["entry"])

    return {
        "statusCode": 200,
    }
