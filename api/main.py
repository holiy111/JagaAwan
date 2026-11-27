"""HTTP endpoints for scheduled scans, dashboard results, and Signed URLs via Supabase."""

import json

import functions_framework
import requests

from common import config, logging as app_log
from common.validators import sanitize_bucket_name, valid_hasil
from scanner.scanner import jalankan_pemindai


def _rest_headers() -> dict[str, str]:
    if not config.SUPABASE_URL or not config.SUPABASE_KEY:
        raise ValueError("SUPABASE_URL dan SUPABASE_KEY wajib diisi.")
    return {
        "Authorization": f"Bearer {config.SUPABASE_KEY}",
        "apikey": config.SUPABASE_KEY,
        "Content-Type": "application/json",
    }


@functions_framework.http
def scan(request):
    headers = {"Content-Type": "application/json"}
    try:
        hasil = jalankan_pemindai()
        if not valid_hasil(hasil):
            raise ValueError("Format hasil pemindaian tidak valid.")
        resp = requests.post(
            f"{config.SUPABASE_URL}/rest/v1/{config.SUPABASE_TABLE}",
            headers={**_rest_headers(), "Prefer": "return=minimal"},
            json=hasil,
            timeout=15,
        )
        resp.raise_for_status()
        app_log.info(f"Scan selesai & tersimpan ke Supabase: {hasil['scan_id']} (skor={hasil['skor']})")
        return json.dumps({"status": "ok", "scan_id": hasil["scan_id"]}), 200, headers
    except Exception as exc:
        app_log.error(f"Gagal menjalankan scan: {exc}")
        return json.dumps({"status": "error", "pesan": "Terjadi kesalahan internal saat memindai."}), 500, headers


@functions_framework.http
def results(request):
    headers = {"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"}
    if request.method == "OPTIONS":
        return "", 204, {**headers, "Access-Control-Allow-Methods": "GET"}
    try:
        resp = requests.get(
            f"{config.SUPABASE_URL}/rest/v1/{config.SUPABASE_TABLE}",
            headers=_rest_headers(),
            params={"select": "*", "order": "timestamp.desc", "limit": "1"},
            timeout=15,
        )
        resp.raise_for_status()
        rows = resp.json()
        if not rows:
            return json.dumps({"status": "belum_ada_data"}), 404, headers
        return json.dumps(rows[0], ensure_ascii=False), 200, headers
    except Exception as exc:
        app_log.error(f"Gagal mengambil hasil scan: {exc}")
        return json.dumps({"status": "error", "pesan": "Terjadi kesalahan internal saat mengambil data."}), 500, headers


@functions_framework.http
def signed_url(request):
    headers = {"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"}
    if request.method == "OPTIONS":
        return "", 204, {**headers, "Access-Control-Allow-Methods": "GET"}
    try:
        raw_bucket = request.args.get("bucket", "")
        object_path = str(request.args.get("path", "")).lstrip("/")
        if not object_path or ".." in object_path:
            return json.dumps({"status": "error", "pesan": "Parameter path tidak valid."}), 400, headers

        bucket = sanitize_bucket_name(raw_bucket)
        resp = requests.post(
            f"{config.SUPABASE_URL}/storage/v1/object/sign/{bucket}/{object_path}",
            headers=_rest_headers(),
            json={"expiresIn": 300},
            timeout=15,
        )
        resp.raise_for_status()
        signed_path = resp.json().get("signedURL", "")
        if not signed_path:
            raise ValueError("Supabase tidak mengembalikan signedURL.")
        full_url = signed_path if signed_path.startswith("http") else f"{config.SUPABASE_URL}/storage/v1{signed_path}"
        return json.dumps({"signed_url": full_url}, ensure_ascii=False), 200, headers
    except (TypeError, ValueError) as exc:
        return json.dumps({"status": "error", "pesan": str(exc)}), 400, headers
    except Exception as exc:
        app_log.error(f"Gagal membuat Signed URL: {exc}")
        return json.dumps({"status": "error", "pesan": "Gagal membuat Signed URL."}), 500, headers
