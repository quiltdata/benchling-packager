import os
import pytest

from lambdas import BenchlingEntry

try:
    BENCHLING_ENTRY_ID=os.environ["BENCHLING_ENTRY_ID"]
except KeyError:
    pytest.skip(allow_module_level=True)

@pytest.fixture
def entry():
    entry_dict = {
        "id": BENCHLING_ENTRY_ID,
    }
    return BenchlingEntry(entry_dict)

def test_entry(entry):
    assert entry
    assert entry.entry_id == BENCHLING_ENTRY_ID
    assert entry.fields == {}
    assert entry.pkg_name
    assert BenchlingEntry.PKG_PREFIX in entry.pkg_name

