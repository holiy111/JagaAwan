import json
import sys
import types
from unittest.mock import MagicMock, patch

try:
    import functions_framework  # noqa: F401
except ImportError:
    stub = types.ModuleType("functions_framework")
    stub.http = lambda fn: fn
    sys.modules["functions_framework"] = stub

from api.main import results, scan, signed_url


def _mock_request(method="GET", args=None):
    req = MagicMock()
    req.method = method
    req.args = args or {}
    return req


def test_scan_success(monkeypatch):
    monkeypatch.setattr("common.config.SUPABASE_URL", "https://demo.supabase.co")
    monkeypatch.setattr("common.config.SUPABASE_KEY", "service-role-key")
    sample = {
        "scan_id": "2026-11-27T13:00:00Z",
        "timestamp": "2026-11-27T13:00:00+00:00",
        "skor": 70,
        "jumlah_bucket": 1,
        "temuan": [
            {
                "bucket": "jagaawan-data-4827",
                "risiko": "TINGGI",
                "kode": "BUCKET_PUBLIK",
                "penjelasan": "Publik",
                "saran": "Tutup",
                "kurang": 30,
            }
        ],
    }
    mock_resp = MagicMock()
    with patch("api.main.jalankan_pemindai", return_value=sample), patch("api.main.requests.post", return_value=mock_resp) as mock_post:
        body, status, _ = scan(_mock_request("POST"))

    assert status == 200
    assert json.loads(body) == {"status": "ok", "scan_id": "2026-11-27T13:00:00Z"}
    mock_post.assert_called_once()


def test_scan_error_does_not_leak_exception():
    with patch("api.main.jalankan_pemindai", side_effect=RuntimeError("rahasia-internal")):
        body, status, _ = scan(_mock_request("POST"))

    assert status == 500
    payload = json.loads(body)
    assert payload["status"] == "error"
    assert "rahasia-internal" not in payload["pesan"]


def test_results_options():
    body, status, headers = results(_mock_request("OPTIONS"))
    assert status == 204
    assert body == ""
    assert headers["Access-Control-Allow-Methods"] == "GET"


def test_results_empty_returns_404(monkeypatch):
    monkeypatch.setattr("common.config.SUPABASE_URL", "https://demo.supabase.co")
    monkeypatch.setattr("common.config.SUPABASE_KEY", "service-role-key")
    mock_resp = MagicMock()
    mock_resp.json.return_value = []
    with patch("api.main.requests.get", return_value=mock_resp):
        body, status, _ = results(_mock_request("GET"))

    assert status == 404
    assert json.loads(body)["status"] == "belum_ada_data"


def test_results_returns_latest_row(monkeypatch):
    monkeypatch.setattr("common.config.SUPABASE_URL", "https://demo.supabase.co")
    monkeypatch.setattr("common.config.SUPABASE_KEY", "service-role-key")
    mock_resp = MagicMock()
    mock_resp.json.return_value = [{"scan_id": "2026-11-27T13:00:00Z", "skor": 100, "temuan": []}]
    with patch("api.main.requests.get", return_value=mock_resp):
        body, status, _ = results(_mock_request("GET"))

    assert status == 200
    assert json.loads(body)["skor"] == 100


def test_signed_url_success(monkeypatch):
    monkeypatch.setattr("common.config.SUPABASE_URL", "https://demo.supabase.co")
    monkeypatch.setattr("common.config.SUPABASE_KEY", "service-role-key")
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"signedURL": "/object/sign/jagaawan-foto-4827/produk/a.jpg?token=abc"}
    req = _mock_request("GET", args={"bucket": "jagaawan-foto-4827", "path": "produk/a.jpg"})
    with patch("api.main.requests.post", return_value=mock_resp):
        body, status, _ = signed_url(req)

    assert status == 200
    assert json.loads(body)["signed_url"] == "https://demo.supabase.co/storage/v1/object/sign/jagaawan-foto-4827/produk/a.jpg?token=abc"


def test_signed_url_rejects_path_traversal():
    req = _mock_request("GET", args={"bucket": "jagaawan-foto-4827", "path": "../secret.txt"})
    body, status, _ = signed_url(req)
    assert status == 400
    assert json.loads(body)["status"] == "error"
