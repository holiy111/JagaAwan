"""Read-only Supabase Storage configuration scanner."""

from datetime import datetime, timezone
import json

import requests

from common import config, logging as app_log

RISK_RULES = {
    "TINGGI": {
        "pengurang": 30,
        "kode": "BUCKET_PUBLIK",
        "penjelasan": "Bucket bersifat publik dan belum memiliki pembatasan ukuran atau tipe file.",
    },
    "SEDANG": {
        "pengurang": 15,
        "kode": "BUCKET_PUBLIK",
        "penjelasan": "Bucket bersifat publik sehingga semua file dapat diunduh tanpa autentikasi, meski sudah ada batas tipe/ukuran.",
    },
    "RENDAH": {
        "pengurang": 5,
        "kode": "BATAS_BELUM_ATUR",
        "penjelasan": "Bucket sudah privat, namun batas ukuran file atau tipe MIME belum dikonfigurasi.",
    },
    "AMAN": {
        "pengurang": 0,
        "kode": "AMAN",
        "penjelasan": "Bucket privat dan sudah memiliki pembatasan file. Konfigurasi sudah baik.",
    },
}

SARAN = {
    "TINGGI": "Ubah bucket menjadi privat (public=false), gunakan Signed URL untuk akses file, serta atur file_size_limit dan allowed_mime_types.",
    "SEDANG": "Pertimbangkan mengubah bucket menjadi privat (public=false) dan gunakan Signed URL jika file bersifat sensitif.",
    "RENDAH": "Atur file_size_limit dan allowed_mime_types pada bucket untuk mencegah unggahan file berbahaya atau berukuran berlebih.",
    "AMAN": "Pertahankan konfigurasi saat ini dan lakukan pemindaian secara berkala.",
}


def _supabase_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "apikey": api_key,
    }


def ambil_daftar_bucket(supabase_url: str, supabase_key: str) -> list[dict]:
    """Fetch bucket metadata from Supabase Storage API (read-only)."""
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL dan SUPABASE_KEY wajib diisi di environment.")
    resp = requests.get(
        f"{supabase_url.rstrip('/')}/storage/v1/bucket",
        headers=_supabase_headers(supabase_key),
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list):
        raise ValueError("Respons daftar bucket Supabase tidak valid.")
    return data


def periksa_bucket(bucket: dict) -> dict:
    """Evaluate a single Supabase bucket metadata dict against security rules."""
    nama = str(bucket.get("name") or bucket.get("id") or "")
    publik = bool(bucket.get("public", False))
    terbatas = bool(bucket.get("file_size_limit")) or bool(bucket.get("allowed_mime_types"))

    if publik and not terbatas:
        risiko = "TINGGI"
    elif publik:
        risiko = "SEDANG"
    elif not terbatas:
        risiko = "RENDAH"
    else:
        risiko = "AMAN"

    aturan = RISK_RULES[risiko]
    return {
        "bucket": nama,
        "risiko": risiko,
        "kode": aturan["kode"],
        "kurang": aturan["pengurang"],
        "penjelasan": aturan["penjelasan"],
        "saran": SARAN[risiko],
        "publik": publik,
        "terbatas": terbatas,
    }


def hitung_skor(temuan: list[dict]) -> int:
    return max(0, 100 - sum(int(t.get("kurang", 0)) for t in temuan))


def jalankan_pemindai() -> dict:
    """Scan every bucket in the configured Supabase project; never mutates buckets."""
    buckets = ambil_daftar_bucket(config.SUPABASE_URL, config.SUPABASE_KEY)
    temuan = [periksa_bucket(bucket) for bucket in buckets]
    app_log.info(f"Memindai {len(temuan)} bucket Supabase Storage.")
    now = datetime.now(timezone.utc)
    return {
        "scan_id": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "timestamp": now.isoformat(),
        "skor": hitung_skor(temuan),
        "jumlah_bucket": len(temuan),
        "temuan": temuan,
    }


if __name__ == "__main__":
    print(json.dumps(jalankan_pemindai(), indent=2, ensure_ascii=False))
