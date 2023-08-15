import os

from aws_lambda_powertools.utilities import parameters
from benchling_sdk import models as benchling_models
from benchling_sdk.auth.client_credentials_oauth2 import ClientCredentialsOAuth2
from benchling_sdk.benchling import Benchling
from benchling_sdk.helpers import serialization_helpers

class BenchlingClient():
    @classmethod
    def MakeProxy(cls):
        BENCHLING_TENANT = os.environ["BENCHLING_TENANT"]
        BENCHLING_CLIENT_ID = os.environ["BENCHLING_CLIENT_ID"]
        BENCHLING_CLIENT_SECRET_ARN = os.environ["BENCHLING_CLIENT_SECRET_ARN"]
        return cls(BENCHLING_TENANT, BENCHLING_CLIENT_ID, BENCHLING_CLIENT_SECRET_ARN)

    def __init__(self, tenant, id, arn):
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
            benchling_models.EntryUpdate(
                _fields=serialization_helpers.fields(values)
            ),
        )
