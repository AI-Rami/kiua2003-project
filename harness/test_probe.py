"""Synthetic, isolated tests; never writes to eval/ or the real forecast cache."""

import gzip
import io
import json
import tempfile
import unittest
import zlib
from email.message import Message
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

import probe


RAW = json.dumps({"properties": {"timeseries": [
    {"time": "2026-10-12T10:00:00Z", "data": {"instant": {"details": {"air_temperature": 7.5}}}}
]}})


class Response(io.BytesIO):
    code = 200

    def __init__(self):
        super().__init__(gzip.compress(RAW.encode("utf-8")))
        self.headers = Message()
        self.headers["Content-Encoding"] = "gzip"
        self.headers["Expires"] = "Tue, 01 Jan 2100 00:00:00 GMT"
        self.headers["Last-Modified"] = "Mon, 12 Oct 2026 10:00:00 GMT"


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        self.source = root / "fixtures/met_hamar.json"
        self.metadata = root / "fixtures/met_hamar.metadata.json"
        self.output = root / "out/probe.json"
        for name, value in (("SOURCE_PATH", self.source), ("METADATA_PATH", self.metadata),
                            ("OUTPUT_PATH", self.output)):
            patcher = patch.object(probe, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def download(self):
        with patch.object(probe, "urlopen", return_value=Response()) as network:
            raw, mode = probe.retrieve()
        request = network.call_args.args[0]
        self.assertEqual(request.full_url, probe.SOURCE_URL)
        self.assertEqual(request.get_header("User-agent"), probe.USER_AGENT)
        self.assertEqual(request.get_header("Accept-encoding"), "gzip, deflate")
        self.assertEqual(network.call_args.kwargs["timeout"], 30)
        self.assertEqual(raw, RAW)
        self.assertEqual(mode, "downloaded")
        self.assertEqual(self.source.read_bytes(), RAW.encode("utf-8"))

    def test_download_cache_and_offline(self):
        self.download()
        with patch.object(probe, "urlopen", side_effect=AssertionError("Network forbidden")):
            self.assertEqual(probe.retrieve()[1], "cached (before Expires)")
            self.assertEqual(probe.retrieve(True), (RAW, "offline"))
        metadata = json.loads(self.metadata.read_text(encoding="utf-8"))
        self.assertEqual(metadata["source_url"], probe.SOURCE_URL)
        self.assertEqual(metadata["license"], "CC BY 4.0")
        self.assertIn("retrieved_at", metadata)
        output = probe.transform(RAW)
        probe.write_json(self.output, output)
        self.assertEqual(json.loads(self.output.read_text(encoding="utf-8")), output)
        self.assertEqual(output["items"][0]["date"], "2026-10-12T10:00:00Z")
        self.assertEqual(output["items"][0]["temperature_c"], 7.5)

    def test_expired_cache_and_304(self):
        self.download()
        metadata = json.loads(self.metadata.read_text(encoding="utf-8"))
        retrieved_at = metadata["retrieved_at"]
        metadata["expires"] = "Mon, 01 Jan 2001 00:00:00 GMT"
        probe.write_json(self.metadata, metadata)
        headers = Message()
        headers["Expires"] = "Tue, 01 Jan 2100 00:00:00 GMT"
        response = HTTPError(probe.SOURCE_URL, 304, "Not Modified", headers, io.BytesIO())
        with patch.object(probe, "urlopen", side_effect=response) as network:
            self.assertEqual(probe.retrieve(), (RAW, "cached (304 Not Modified)"))
        self.assertEqual(network.call_args.args[0].get_header("If-modified-since"),
                         metadata["last_modified"])
        updated = json.loads(self.metadata.read_text(encoding="utf-8"))
        self.assertEqual(updated["retrieved_at"], retrieved_at)
        self.assertEqual(updated["expires"], headers["Expires"])
        self.assertEqual(self.source.read_bytes(), RAW.encode("utf-8"))

    def test_missing_offline_cache_never_uses_network(self):
        with patch.object(probe, "urlopen", side_effect=AssertionError("Network forbidden")):
            with self.assertRaisesRegex(ValueError, "Offline response unavailable"):
                probe.retrieve(True)

    def test_missing_required_fields(self):
        with self.assertRaisesRegex(ValueError, "missing required source field"):
            probe.transform('{"properties":{"timeseries":[{"time":"2026-10-12T10:00:00Z"}]}}')

    def test_offline_cli_output_matches_saved_source(self):
        self.download()
        with patch.object(probe, "urlopen", side_effect=AssertionError("Network forbidden")), \
                patch("sys.argv", ["probe.py", "--offline"]):
            self.assertEqual(probe.main(), 0)
        source = json.loads(self.source.read_text(encoding="utf-8"))
        output = json.loads(self.output.read_text(encoding="utf-8"))
        entries = source["properties"]["timeseries"]
        self.assertEqual(len(output["items"]), len(entries))
        for item, entry in zip(output["items"], entries):
            self.assertEqual(item["date"], entry["time"])
            self.assertEqual(item["temperature_c"], entry["data"]["instant"]["details"]["air_temperature"])

    def test_compression(self):
        raw = RAW.encode("utf-8")
        for body, encoding in ((raw, "identity"), (gzip.compress(raw), "gzip"),
                               (zlib.compress(raw), "deflate"),
                               (zlib.compress(raw)[2:-4], "deflate")):
            self.assertEqual(probe.decode_response(body, encoding), RAW)


if __name__ == "__main__":
    unittest.main()
