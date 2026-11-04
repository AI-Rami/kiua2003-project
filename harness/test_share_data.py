"""Model-free checks for restoring a shared baseline."""

import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import share_data


def sha(data):
    return hashlib.sha256(data).hexdigest()


class SharedDataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=share_data.ROOT)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "checkout"
        self.baseline = Path(self.temp.name) / "baseline"
        self.root.mkdir()
        self.baseline.mkdir()
        review = b'{}'
        (self.root / "reviews").mkdir()
        (self.root / "reviews/current-v2.json").write_bytes(review)
        index = b'{"entries":[]}'
        relative = Path("out/current/index.json")
        source = self.baseline / "data/001"
        source.parent.mkdir(parents=True)
        source.write_bytes(index)
        database = b"synthetic database bytes"
        archive = self.baseline / "db/state.sqlite3.gz"
        archive.parent.mkdir()
        archive.write_bytes(gzip.compress(database, mtime=0))
        manifest = {"schema_version": 1, "selected_advertisements": 0,
                    "review_sha256": sha(review),
                    "files": [{"path": relative.as_posix(), "archive": "data/001", "sha256": sha(index),
                               "bytes": len(index)}],
                    "database": {"path": share_data.DB_TARGET.as_posix(),
                                 "archive": "db/state.sqlite3.gz",
                                 "sha256": sha(database), "archive_sha256": sha(archive.read_bytes())}}
        (self.baseline / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def test_fresh_restore_and_existing_data_are_preserved(self):
        state, _ = share_data.restore(self.root, self.baseline, validate=False)
        self.assertEqual(state, "restored")
        self.assertEqual((self.root / share_data.DB_TARGET).read_bytes(),
                         b"synthetic database bytes")
        index = self.root / "out/current/index.json"
        index.write_bytes(b"newer local results")
        state, _ = share_data.restore(self.root, self.baseline, validate=False)
        self.assertEqual(state, "existing")
        self.assertEqual(index.read_bytes(), b"newer local results")

    def test_partial_restore_finishes_without_overwriting(self):
        index = self.root / "out/current/index.json"
        index.parent.mkdir(parents=True)
        index.write_bytes(b'{"entries":[]}')
        state, _ = share_data.restore(self.root, self.baseline, validate=False)
        self.assertEqual(state, "restored")
        self.assertEqual(index.read_bytes(), b'{"entries":[]}')

    def test_different_partial_state_is_rejected(self):
        index = self.root / "out/current/index.json"
        index.parent.mkdir(parents=True)
        index.write_bytes(b"newer local results")
        with self.assertRaises(share_data.ShareError):
            share_data.restore(self.root, self.baseline, validate=False)
        self.assertFalse((self.root / share_data.DB_TARGET).exists())

    def test_corrupt_archive_is_rejected_before_writing(self):
        (self.baseline / "db/state.sqlite3.gz").write_bytes(b"corrupt")
        with self.assertRaises(share_data.ShareError):
            share_data.restore(self.root, self.baseline, validate=False)
        self.assertFalse((self.root / "out").exists())


if __name__ == "__main__":
    unittest.main()
