# Aturan Pemeriksaan dan Penilaian Risiko JagaAwan (Supabase Storage)

Dokumen ini menjelaskan aturan pemeriksaan postur keamanan **Supabase Storage** serta rumus perhitungan skor keamanan untuk UMKM.

---

## 1. Konsep yang Diperiksa

Pemindai memeriksa 2 elemen konfigurasi utama pada setiap bucket Supabase Storage:
1. **Visibilitas Bucket (`public`)**: Apakah bucket disetel publik (`true` = siapa saja di internet bisa mengakses URL objek) atau privat (`false` = membutuhkan JWT / Signed URL).
2. **Pembatasan File (`file_size_limit` / `allowed_mime_types`)**: Apakah pemilik project sudah membatasi ukuran maksimal file atau tipe MIME yang diizinkan di bucket.

---

## 2. Matriks Risiko per Bucket

| Visibilitas (`public`) | Pembatasan Ukuran / MIME | Status Risiko | Kode Temuan | Pengurang Skor (`kurang`) |
| :--- | :--- | :--- | :--- | :--- |
| **Publik (`true`)** | **Belum Diatur** | **TINGGI** | `BUCKET_PUBLIK` | **-30** |
| **Publik (`true`)** | **Sudah Diatur** | **SEDANG** | `BUCKET_PUBLIK` | **-15** |
| **Privat (`false`)** | **Belum Diatur** | **RENDAH** | `BATAS_BELUM_ATUR` | **-5** |
| **Privat (`false`)** | **Sudah Diatur** | **AMAN** | `AMAN` | **0** |

---

## 3. Rumus Perhitungan Skor

$$\text{Skor Akhir} = \max\left(0, 100 - \sum \text{Pengurang Skor Seluruh Bucket}\right)$$

- **Skor Awal**: 100
- **Skor Minimal**: 0 (tidak bisa bernilai negatif)
- **Kategori Skor**:
  - `80 - 100`: **Aman / Sehat (Hijau)**
  - `50 - 79` : **Perlu Perhatian (Kuning)**
  - `< 50`    : **Bahaya / Kritis (Merah)**
