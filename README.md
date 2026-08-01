# Jasa Pembuatan Website

Flask + Supabase + Cloudinary, deploy ke Vercel.

## Setup

1. **Supabase**: buat project baru, jalankan isi `schema.sql` di SQL Editor.
2. **Admin pertama**: jalankan `python generate_admin.py` secara lokal, lalu jalankan query `insert` yang dihasilkan di Supabase SQL Editor.
3. **Cloudinary**: buat account, ambil `cloud_name`, `api_key`, `api_secret` dari dashboard.
4. **QRIS**: upload gambar QRIS kamu ke Cloudinary (manual lewat dashboard atau lewat panel admin produk sementara), lalu isi URL-nya ke env `QRIS_IMAGE_URL`.
5. Copy `.env.example` ke `.env` dan isi semua value. Untuk lokal, install `python-dotenv` dan load manual jika perlu.
6. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
7. Jalankan lokal:
   ```
   python app.py
   ```

## Deploy ke Vercel

1. Push project ini ke GitHub.
2. Import repo di Vercel.
3. Di Vercel dashboard → Settings → Environment Variables, isi semua variabel dari `.env.example`.
4. Deploy.

## Alur

- `/` — landing page
- `/katalog` — daftar paket
- `/checkout/<product_id>` — form order + upload bukti bayar (wajib)
- `/admin/login` — login admin
- `/admin/produk` — tambah/hapus produk & thumbnail
- `/admin/pesanan` — approve/reject pesanan masuk

## Catatan

- Bukti pembayaran wajib diupload sebelum order tersimpan.
- Setelah admin approve/reject, status order berubah tapi user **tidak otomatis dapat notifikasi** — mereka bisa klik tombol WhatsApp di halaman sukses untuk konfirmasi manual. Kalau mau notif otomatis ke user, perlu integrasi WA API (WABlas, Fonnte, dll) — belum termasuk di sini.
