"""
Jalankan sekali secara lokal untuk generate password_hash admin pertama.
Hasilnya di-insert manual ke tabel `admins` di Supabase.

Cara pakai:
    python generate_admin.py
"""
from werkzeug.security import generate_password_hash

username = input("Username admin: ").strip()
password = input("Password admin: ").strip()

print("\nJalankan query ini di Supabase SQL Editor:\n")
print(
    f"insert into admins (username, password_hash) values "
    f"('{username}', '{generate_password_hash(password)}');"
)
