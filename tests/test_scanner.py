from unittest.mock import patch

from common.validators import valid_hasil
from scanner.scanner import hitung_skor, jalankan_pemindai, periksa_bucket


def _make_bucket(
    name="jagaawan-test-bucket",
    public=False,
    file_size_limit=None,
    allowed_mime_types=None,
):
    return {
        "id": name,
        "name": name,
        "public": public,
        "file_size_limit": file_size_limit,
        "allowed_mime_types": allowed_mime_types,
    }


def test_all_pass():
    bucket = _make_bucket(public=False, file_size_limit=5242880, allowed_mime_types=["image/jpeg"])
    hasil = periksa_bucket(bucket)
    assert hasil["risiko"] == "AMAN"
    assert hasil["kode"] == "AMAN"
    assert hasil["kurang"] == 0


def test_public_without_limits_high():
    bucket = _make_bucket(public=True)
    hasil = periksa_bucket(bucket)
    assert hasil["risiko"] == "TINGGI"
    assert hasil["kode"] == "BUCKET_PUBLIK"
    assert hasil["kurang"] == 30


def test_public_with_limits_medium():
    bucket = _make_bucket(public=True, allowed_mime_types=["image/png"])
    hasil = periksa_bucket(bucket)
    assert hasil["risiko"] == "SEDANG"
    assert hasil["kode"] == "BUCKET_PUBLIK"
    assert hasil["kurang"] == 15


def test_private_without_limits_low():
    bucket = _make_bucket(public=False)
    hasil = periksa_bucket(bucket)
    assert hasil["risiko"] == "RENDAH"
    assert hasil["kode"] == "BATAS_BELUM_ATUR"
    assert hasil["kurang"] == 5


def test_jalankan_pemindai_sesuai_kontrak():
    buckets = [
        _make_bucket(name="jagaawan-data-4827", public=True),
        _make_bucket(name="jagaawan-foto-4827", public=False, file_size_limit=2097152),
    ]
    with patch("scanner.scanner.ambil_daftar_bucket", return_value=buckets):
        hasil = jalankan_pemindai()

    assert hasil["jumlah_bucket"] == 2
    assert hasil["skor"] == 70
    assert valid_hasil(hasil) is True


def test_score_never_negative():
    assert hitung_skor([{"kurang": 30}] * 5) == 0
