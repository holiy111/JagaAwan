"""Input and dashboard payload validation helpers."""

import re

BUCKET_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$")


def sanitize_bucket_name(raw: str) -> str:
    if not isinstance(raw, str):
        raise TypeError("Nama bucket harus berupa string.")
    name = raw.strip().lower()
    if not name:
        raise ValueError("Nama bucket tidak boleh kosong.")
    if not 3 <= len(name) <= 63:
        raise ValueError(f"Panjang nama bucket harus 3-63 karakter (diterima: {len(name)}).")
    if not BUCKET_RE.fullmatch(name):
        raise ValueError("Nama bucket hanya boleh mengandung karakter huruf kecil, angka, dan tanda hubung.")
    if name.startswith(("goog", "google")):
        raise ValueError("Nama bucket tidak boleh diawali kata yang dicadangkan Google.")
    return name


def valid_temuan(temuan: dict) -> bool:
    if not isinstance(temuan, dict) or not isinstance(temuan.get("bucket"), str):
        return False
    try:
        kurang = int(temuan.get("kurang", -1))
    except (TypeError, ValueError):
        return False
    return bool(BUCKET_RE.fullmatch(temuan["bucket"])) and 0 <= kurang <= 100


def valid_hasil(hasil: dict) -> bool:
    return isinstance(hasil, dict) and isinstance(hasil.get("scan_id"), str) and bool(re.match(r"^\d{4}-\d{2}-\d{2}T.*Z$", hasil["scan_id"])) and isinstance(hasil.get("skor"), int) and 0 <= hasil["skor"] <= 100 and all(valid_temuan(t) for t in hasil.get("temuan", []))
