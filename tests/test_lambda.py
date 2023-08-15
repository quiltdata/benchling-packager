from aws_lambda_powertools.utilities import parameters
from lambdas import BenchlingClient, BenchlingEntry 


def test_import():
    assert BenchlingClient
    assert BenchlingEntry


def test_env():
    assert BenchlingClient.BENCHLING_TENANT
    assert BenchlingEntry.DST_BUCKET


def test_secret():
    arn = BenchlingClient.BENCHLING_CLIENT_SECRET_ARN
    assert arn
    assert "us-east-1" in arn
    secret = parameters.get_secret(arn)
    assert secret
    

def test_client():
    client = BenchlingClient.Default()
    assert client
