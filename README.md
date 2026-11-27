# JagaAwan

Pemindai otomatis misconfiguration **Supabase Storage** untuk UMKM (gratis tanpa kartu kredit). Scanner hanya membaca metadata bucket (read-only); perubahan konfigurasi dilakukan oleh pemilik project melalui Supabase Dashboard.

## Struktur proyek

```text
jagaawan/
├── main.py              # entrypoint HTTP handlers (re-export dari api.main)
├── scanner/             # pemindai read-only bucket Supabase Storage
├── api/                 # endpoint scan, results, dan signed_url (Supabase REST)
├── dashboard/           # frontend dashboard dan data contoh lokal
├── toko_uji/            # website uji katalog (mendukung public URL & Signed URL)
├── common/              # validators.py, config.py, logging.py
├── tests/               # pengujian scanner, API, dan validasi
├── docs/                # aturan pemindaian, kontrak payload, dan SQL tabel scans
├── requirements.txt     # dependensi runtime
├── requirements-dev.txt # dependensi pengembangan & pengujian (pytest)
└── .gitignore           # .env, key, dan service-account JSON
```

## Setup Supabase (Gratis Tanpa Kartu Kredit)

1. Buat project gratis di [Supabase](https://supabase.com).
2. Buka **SQL Editor** dan jalankan isi [docs/init_supabase.sql](docs/init_supabase.sql) untuk membuat tabel `scans`.
3. Buka **Storage** → buat bucket (misal `jagaawan-foto-4827`), buat folder `produk`, lalu upload 6 foto katalog untuk `toko_uji/index.html`.
4. Buka **Project Settings → API**, salin **Project URL** (`SUPABASE_URL`) dan **`service_role` key** (`SUPABASE_KEY`).

## Menjalankan lokal

1. Pasang dependensi:
   ```bash
   pip install -r requirements-dev.txt
   ```
2. Salin `.env.example` menjadi `.env` lalu isi `SUPABASE_URL` dan `SUPABASE_KEY`.
3. Jalankan scanner langsung dari terminal:
   ```bash
   python -m scanner.scanner
   ```
4. Jalankan endpoint API lokal (Python 3.12):
   ```bash
   functions-framework --target=results --debug
   ```
5. Buka `dashboard/index.html` (default memakai `dashboard/data-contoh.json`, atau tambahkan `?api=http://localhost:8080` untuk membaca hasil live).
6. Buka `toko_uji/index.html`, isi `SUPABASE_URL` dan `BUCKET` di bagian `<script>` (tambahkan `?signed_api=http://localhost:8080` jika bucket disetel privat dan ingin memakai endpoint `signed_url`).
7. Jalankan pengujian:
   ```bash
   python -m pytest tests/ -v
   ```
