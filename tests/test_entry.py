import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import quilt3
from lambdas import BenchlingEntry, main

SKIP_PARTIALS = os.environ.get("SKIP_PARTIALS", True)

try:
    BENCHLING_ENTRY_ID = os.environ["BENCHLING_ENTRY_ID"]
except KeyError:
    pytest.skip(allow_module_level=True)

ENTRY_DATA = {
    "id": BENCHLING_ENTRY_ID,
    "displayId": "test_entry",
    "name": "test_entry",
    "folderId": "test_folder",
    "createdAt": "2021-01-01T00:00:00.000Z",
    "modifiedAt": "2021-01-01T00:00:00.000Z",
    "schema": {
        "id": "test_schema",
        "name": "test_schema",
    },
    "fields": {},
    "customFields": {},
    "authors": [
        {
            "id": "test_author",
            "name": "test_author",
            "handle": "test_author",
        }
    ],
    "days": [],
    "webURL": "https://example.com",
}


@pytest.fixture
def entry():
    return BenchlingEntry(ENTRY_DATA)


def test_entry(entry):
    assert entry
    assert entry.entry_id == BENCHLING_ENTRY_ID
    assert entry.fields == {}
    assert entry.pkg_name
    assert BenchlingEntry.PKG_PREFIX in entry.pkg_name
    assert "/" in entry.pkg_name


def test_format(entry):
    fmt = entry.format()
    assert fmt
    assert "test_entry" in fmt


def test_dump(entry):
    dmp = entry.dump()
    assert dmp
    assert "days" in dmp


@pytest.mark.skipif(SKIP_PARTIALS, reason="Only do end-to-end test")
def test_write(entry):
    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        entry.write_files(tmpdir_path)
        fn = {f.name: f for f in tmpdir_path.glob("*")}
        assert "entry.json" in fn
        assert "notes.pdf" in fn
        notes = fn["notes.pdf"]
        assert isinstance(notes, Path)
        assert notes.exists()


@pytest.mark.skipif(SKIP_PARTIALS, reason="Only do end-to-end test")
def test_push(entry):
    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        (tmpdir_path / "README.md").write_text("test_push")
        rc = entry.push_package(tmpdir_path)
        assert rc

        pkg = quilt3.Package.browse(entry.pkg_name, registry=entry.registry)
        assert pkg
        readme = pkg["README.md"]
        assert readme
        assert readme() == "test_push"


@pytest.mark.skipif(SKIP_PARTIALS, reason="Only do end-to-end test")
def test_update(entry):
    rc = entry.update_benchling_notebook()
    assert rc


@pytest.mark.skipif(SKIP_PARTIALS is False, reason="Only do partial tests")
def test_handler():
    entry = main(ENTRY_DATA)
    assert isinstance(entry, BenchlingEntry)
