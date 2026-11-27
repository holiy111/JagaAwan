-- Jalankan query ini di Supabase Dashboard -> SQL Editor
-- ============================================================
-- 1. Buat tabel scans
-- ============================================================
create table if not exists public.scans (
  scan_id text primary key,
  timestamp timestamptz not null,
  skor integer not null check (skor >= 0 and skor <= 100),
  jumlah_bucket integer not null default 0,
  temuan jsonb not null default '[]'::jsonb
);

create index if not exists idx_scans_timestamp on public.scans (timestamp desc);

-- ============================================================
-- 2. Aktifkan Row Level Security (RLS)
--    Memblokir akses langsung dari browser (anon key).
--    Backend memakai service_role key yang otomatis bypass RLS.
-- ============================================================
alter table public.scans enable row level security;

-- Policy eksplisit untuk service_role (dokumentasi & kejelasan)
create policy "service_role: insert scans"
  on public.scans for insert to service_role with check (true);

create policy "service_role: select scans"
  on public.scans for select to service_role using (true);

-- Verifikasi: jalankan query ini untuk memastikan RLS aktif
-- select relname, relrowsecurity from pg_class where relname = 'scans';
-- Hasil yang diharapkan: relrowsecurity = true
