-- Jalankan di Supabase SQL Editor

create extension if not exists "uuid-ossp";

create table if not exists products (
  id uuid primary key default uuid_generate_v4(),
  name text not null,
  price numeric not null,
  description text,
  thumbnail_url text,
  created_at timestamptz default now()
);

create table if not exists orders (
  id uuid primary key default uuid_generate_v4(),
  product_id uuid references products(id) on delete set null,
  buyer_name text not null,
  bank_account text not null,
  whatsapp_number text not null,
  payment_proof_url text not null,
  status text not null default 'pending', -- pending | approved | rejected
  created_at timestamptz default now()
);

create table if not exists admins (
  id uuid primary key default uuid_generate_v4(),
  username text unique not null,
  password_hash text not null
);

-- Buat admin pertama (ganti password_hash pakai hasil dari generate_admin.py)
-- insert into admins (username, password_hash) values ('admin', '<hash>');
