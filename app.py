import os
from functools import wraps
from datetime import datetime

import cloudinary
import cloudinary.uploader
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, abort
)
from supabase import create_client, Client
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

# --- Supabase ---
supabase: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"],
)

# --- Cloudinary ---
cloudinary.config(
    cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
    api_key=os.environ["CLOUDINARY_API_KEY"],
    api_secret=os.environ["CLOUDINARY_API_SECRET"],
    secure=True,
)

ADMIN_WA_NUMBER = os.environ.get("ADMIN_WA_NUMBER", "")


# ---------- Helpers ----------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper


def upload_image(file_storage, folder):
    if not file_storage or file_storage.filename == "":
        return None
    result = cloudinary.uploader.upload(file_storage, folder=folder)
    return result["secure_url"]


def get_settings():
    res = supabase.table("settings").select("*").eq("id", 1).execute()
    if res.data:
        return res.data[0]
    return {"orders_open": True, "closed_message": ""}


# ---------- Halaman Publik ----------
@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/katalog")
def catalog():
    res = supabase.table("products").select("*").order("created_at", desc=True).execute()
    settings = get_settings()
    return render_template("catalog.html", products=res.data, settings=settings)


@app.route("/checkout/<product_id>", methods=["GET", "POST"])
def checkout(product_id):
    settings = get_settings()
    if not settings.get("orders_open", True):
        flash(settings.get("closed_message") or "Orderan baru sedang ditutup sementara.", "error")
        return redirect(url_for("catalog"))

    res = supabase.table("products").select("*").eq("id", product_id).execute()
    if not res.data:
        abort(404)
    product = res.data[0]

    if request.method == "POST":
        buyer_name = request.form.get("buyer_name", "").strip()
        bank_account = request.form.get("bank_account", "").strip()
        whatsapp_number = request.form.get("whatsapp_number", "").strip()
        proof_file = request.files.get("payment_proof")

        if not (buyer_name and bank_account and whatsapp_number and proof_file and proof_file.filename):
            flash("Semua data wajib diisi, termasuk bukti pembayaran.", "error")
            return render_template("checkout.html", product=product)

        proof_url = upload_image(proof_file, "payment_proofs")

        order = {
            "product_id": product_id,
            "buyer_name": buyer_name,
            "bank_account": bank_account,
            "whatsapp_number": whatsapp_number,
            "payment_proof_url": proof_url,
            "status": "pending",
        }
        inserted = supabase.table("orders").insert(order).execute()
        order_id = inserted.data[0]["id"]
        return redirect(url_for("order_success", order_id=order_id))

    return render_template("checkout.html", product=product)


@app.route("/order/sukses/<order_id>")
def order_success(order_id):
    res = supabase.table("orders").select("*, products(*)").eq("id", order_id).execute()
    if not res.data:
        abort(404)
    return render_template("order_success.html", order=res.data[0], admin_wa=ADMIN_WA_NUMBER)


# ---------- Admin: Auth ----------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        res = supabase.table("admins").select("*").eq("username", username).execute()
        if res.data and check_password_hash(res.data[0]["password_hash"], password):
            session["admin_id"] = res.data[0]["id"]
            session["admin_username"] = res.data[0]["username"]
            return redirect(url_for("admin_orders"))

        flash("Username atau password salah.", "error")

    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


# ---------- Admin: Produk ----------
@app.route("/admin/produk", methods=["GET", "POST"])
@login_required
def admin_products():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price = request.form.get("price", "0")
        description = request.form.get("description", "").strip()
        thumbnail = request.files.get("thumbnail")

        thumbnail_url = upload_image(thumbnail, "product_thumbnails")

        supabase.table("products").insert({
            "name": name,
            "price": float(price),
            "description": description,
            "thumbnail_url": thumbnail_url,
        }).execute()
        flash("Produk berhasil ditambahkan.", "success")
        return redirect(url_for("admin_products"))

    res = supabase.table("products").select("*").order("created_at", desc=True).execute()
    return render_template("admin/products.html", products=res.data, active="produk")


@app.route("/admin/produk/<product_id>/hapus", methods=["POST"])
@login_required
def admin_delete_product(product_id):
    supabase.table("products").delete().eq("id", product_id).execute()
    flash("Produk dihapus.", "success")
    return redirect(url_for("admin_products"))


# ---------- Admin: Pesanan ----------
@app.route("/admin/pesanan")
@login_required
def admin_orders():
    status_filter = request.args.get("status", "pending")
    query = supabase.table("orders").select("*, products(*)").order("created_at", desc=True)
    if status_filter != "all":
        query = query.eq("status", status_filter)
    res = query.execute()
    return render_template("admin/orders.html", orders=res.data, status_filter=status_filter, active="pesanan")


@app.route("/admin/pesanan/<order_id>/approve", methods=["POST"])
@login_required
def admin_approve_order(order_id):
    supabase.table("orders").update({"status": "approved"}).eq("id", order_id).execute()
    flash("Pesanan disetujui.", "success")
    return redirect(url_for("admin_orders"))


@app.route("/admin/pesanan/<order_id>/reject", methods=["POST"])
@login_required
def admin_reject_order(order_id):
    supabase.table("orders").update({"status": "rejected"}).eq("id", order_id).execute()
    flash("Pesanan ditolak.", "success")
    return redirect(url_for("admin_orders"))


# ---------- Admin: Pengaturan ----------
@app.route("/admin/pengaturan", methods=["GET", "POST"])
@login_required
def admin_settings():
    if request.method == "POST":
        orders_open = request.form.get("orders_open") == "on"
        closed_message = request.form.get("closed_message", "").strip()
        supabase.table("settings").update({
            "orders_open": orders_open,
            "closed_message": closed_message,
        }).eq("id", 1).execute()
        flash("Pengaturan disimpan.", "success")
        return redirect(url_for("admin_settings"))

    settings = get_settings()
    return render_template("admin/settings.html", settings=settings, active="pengaturan")


if __name__ == "__main__":
    app.run(debug=True)
