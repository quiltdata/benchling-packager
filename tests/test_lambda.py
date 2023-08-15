from lambdas import BenchlingClient, BenchlingEntry 

def test_import():
    assert BenchlingClient
    assert BenchlingEntry

def test_env():
    assert BenchlingClient.BENCHLING_TENANT
    assert BenchlingEntry.DST_BUCKET

def test_client():
    client = BenchlingClient.Default()
    assert client
