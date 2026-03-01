"""
Sweet Berry Photography — Flask Server
========================================
PUBLIC  routes: /  →  static HTML/CSS/JS/images (read-only)
ADMIN   routes: /admin/  →  requires password login
API     routes: /api/  →  public read-only data (galleries, content)
ADMIN API:      /admin/api/  →  authenticated CRUD
"""

import os
import json
import hashlib
import shutil
from pathlib import Path
from flask import (
    Flask, request, session, redirect,
    send_from_directory, jsonify, abort
)

# ─────────────────────────────────────────────
# CONFIG  ← Change password before deploying!
# ─────────────────────────────────────────────
ADMIN_PASSWORD = "sweetberry2025"
SITE_ROOT      = Path(__file__).parent
IMAGES_DIR     = SITE_ROOT / "images"
DATA_DIR       = SITE_ROOT / "data"
GALLERIES_FILE = DATA_DIR / "galleries.json"
PAGES_FILE     = DATA_DIR / "pages.json"
ALLOWED_EXT    = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_UPLOAD_MB  = 30

_ADMIN_HASH = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()

app = Flask(__name__, static_folder=str(SITE_ROOT), static_url_path="")
app.secret_key = os.urandom(32)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024


# ─────────────────────────────────────────────
# DATA HELPERS
# ─────────────────────────────────────────────
def load_galleries():
    with open(GALLERIES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_galleries(data):
    with open(GALLERIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_pages():
    with open(PAGES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_pages(data):
    with open(PAGES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def find_gallery(data, gallery_id):
    for g in data["galleries"]:
        if g["id"] == gallery_id:
            return g
    return None

def safe_filename(name: str):
    """Return sanitized filename or None if disallowed."""
    p = Path(name)
    if p.suffix.lower() not in ALLOWED_EXT:
        return None
    # Strip path traversal — take basename only
    return Path(p.name).name

def unique_filename(dest_dir: Path, name: str) -> str:
    """If name already exists in dest_dir, add numeric suffix."""
    p = Path(name)
    stem, ext = p.stem, p.suffix
    candidate = name
    counter = 1
    while (dest_dir / candidate).exists():
        candidate = f"{stem}_{counter}{ext}"
        counter += 1
    return candidate


# ─────────────────────────────────────────────
# AUTH HELPERS
# ─────────────────────────────────────────────
def is_admin():
    return session.get("authenticated") is True

def admin_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not is_admin():
            if request.is_json or request.path.startswith("/admin/api/"):
                return jsonify({"error": "Unauthorized"}), 401
            return redirect("/admin/login")
        return fn(*args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────
# PUBLIC — Static site
# ─────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(SITE_ROOT, "index.html")

@app.route("/<path:filename>")
def public_static(filename):
    if filename.startswith("admin") or filename.startswith("data/"):
        abort(403)
    return send_from_directory(SITE_ROOT, filename)


# ─────────────────────────────────────────────
# PUBLIC API — Read-only data for the live site
# ─────────────────────────────────────────────
@app.route("/api/galleries")
def api_galleries():
    """List all galleries (IDs + names only — no sensitive info)."""
    data = load_galleries()
    return jsonify([{"id": g["id"], "name": g["name"]} for g in data["galleries"]])

@app.route("/api/gallery/<gallery_id>")
def api_gallery(gallery_id):
    """Return images for a specific gallery (for dynamic portfolio loading)."""
    data = load_galleries()
    g = find_gallery(data, gallery_id)
    if not g:
        return jsonify({"error": "Gallery not found"}), 404
    return jsonify({"id": g["id"], "name": g["name"], "images": g["images"]})

@app.route("/api/content/<page_id>")
def api_content(page_id):
    """Return content fields for a page."""
    data = load_pages()
    if page_id not in data["pages"]:
        return jsonify({"error": "Page not found"}), 404
    return jsonify(data["pages"][page_id]["fields"])


# ─────────────────────────────────────────────
# ADMIN — Login / Logout
# ─────────────────────────────────────────────
@app.route("/admin/", methods=["GET"])
@app.route("/admin", methods=["GET"])
def admin_home():
    if not is_admin():
        return redirect("/admin/login")
    return send_from_directory(SITE_ROOT / "admin", "index.html")

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        pw = request.form.get("password", "")
        if hashlib.sha256(pw.encode()).hexdigest() == _ADMIN_HASH:
            session["authenticated"] = True
            session.permanent = False
            return redirect("/admin/")
        return redirect("/admin/login?error=1")
    return send_from_directory(SITE_ROOT / "admin", "login.html")

@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.clear()
    return redirect("/admin/login")


# ─────────────────────────────────────────────
# ADMIN — Static assets for admin UI
# ─────────────────────────────────────────────
@app.route("/admin/<path:filename>")
@admin_required
def admin_static(filename):
    if filename in ("index.html", "login.html") or filename.startswith("assets/"):
        return send_from_directory(SITE_ROOT / "admin", filename)
    abort(404)


# ─────────────────────────────────────────────
# ADMIN API — Galleries CRUD
# ─────────────────────────────────────────────
@app.route("/admin/api/galleries", methods=["GET"])
@admin_required
def admin_list_galleries():
    data = load_galleries()
    # Enrich with image count
    result = []
    for g in data["galleries"]:
        result.append({
            "id":           g["id"],
            "name":         g["name"],
            "description":  g.get("description", ""),
            "page":         g.get("page", ""),
            "single_image": g.get("single_image", False),
            "image_count":  len(g.get("images", []))
        })
    return jsonify(result)

@app.route("/admin/api/gallery/<gallery_id>", methods=["GET"])
@admin_required
def admin_get_gallery(gallery_id):
    data = load_galleries()
    g = find_gallery(data, gallery_id)
    if not g:
        return jsonify({"error": "Gallery not found"}), 404
    return jsonify(g)

@app.route("/admin/api/gallery/<gallery_id>/upload", methods=["POST"])
@admin_required
def admin_upload_to_gallery(gallery_id):
    """Upload one or more images to a gallery."""
    data = load_galleries()
    g = find_gallery(data, gallery_id)
    if not g:
        return jsonify({"error": "Gallery not found"}), 404

    files = request.files.getlist("images")
    if not files or not files[0].filename:
        return jsonify({"error": "No files provided"}), 400

    # For single-image galleries, clear existing images first
    if g.get("single_image"):
        # Delete old files from disk
        for old in g.get("images", []):
            old_path = IMAGES_DIR / old["filename"]
            # Only delete if not shared with another gallery
            shared = any(
                img["filename"] == old["filename"]
                for other in data["galleries"]
                if other["id"] != gallery_id
                for img in other.get("images", [])
            )
            if not shared and old_path.exists():
                old_path.unlink()
        g["images"] = []

    saved = []
    for file in files:
        clean = safe_filename(file.filename)
        if not clean:
            continue
        fname = unique_filename(IMAGES_DIR, clean)
        file.save(IMAGES_DIR / fname)
        alt = request.form.get("alt", "")
        g["images"].append({"filename": fname, "alt": alt})
        saved.append(fname)

    save_galleries(data)
    return jsonify({"success": True, "saved": saved, "gallery": g})

@app.route("/admin/api/gallery/<gallery_id>/image/<filename>", methods=["DELETE"])
@admin_required
def admin_delete_from_gallery(gallery_id, filename):
    """Remove an image from a gallery (and delete from disk if not used elsewhere)."""
    data = load_galleries()
    g = find_gallery(data, gallery_id)
    if not g:
        return jsonify({"error": "Gallery not found"}), 404

    original_count = len(g["images"])
    g["images"] = [img for img in g["images"] if img["filename"] != filename]
    if len(g["images"]) == original_count:
        return jsonify({"error": "Image not found in this gallery"}), 404

    # Delete file if not used in any other gallery
    shared = any(
        img["filename"] == filename
        for other in data["galleries"]
        if other["id"] != gallery_id
        for img in other.get("images", [])
    )
    file_path = IMAGES_DIR / filename
    if not shared and file_path.exists():
        file_path.unlink()

    save_galleries(data)
    return jsonify({"success": True})

@app.route("/admin/api/gallery/<gallery_id>/image/<filename>/replace", methods=["POST"])
@admin_required
def admin_replace_in_gallery(gallery_id, filename):
    """Replace an existing gallery image with a new upload, keeping the same filename."""
    data = load_galleries()
    g = find_gallery(data, gallery_id)
    if not g:
        return jsonify({"error": "Gallery not found"}), 404

    img_entry = next((img for img in g["images"] if img["filename"] == filename), None)
    if not img_entry:
        return jsonify({"error": "Image not in this gallery"}), 404

    file = request.files.get("image")
    if not file or not file.filename:
        return jsonify({"error": "No file provided"}), 400

    dest = IMAGES_DIR / filename
    file.save(dest)
    if "alt" in request.form:
        img_entry["alt"] = request.form["alt"]

    save_galleries(data)
    return jsonify({"success": True, "filename": filename})

@app.route("/admin/api/gallery/<gallery_id>/reorder", methods=["POST"])
@admin_required
def admin_reorder_gallery(gallery_id):
    """Reorder images. Body: { order: ['file1.jpg', 'file2.jpg', ...] }"""
    data = load_galleries()
    g = find_gallery(data, gallery_id)
    if not g:
        return jsonify({"error": "Gallery not found"}), 404

    order = request.json.get("order", [])
    indexed = {img["filename"]: img for img in g["images"]}
    g["images"] = [indexed[f] for f in order if f in indexed]
    save_galleries(data)
    return jsonify({"success": True})


# ─────────────────────────────────────────────
# ADMIN API — All Images (file browser)
# ─────────────────────────────────────────────
@app.route("/admin/api/images", methods=["GET"])
@admin_required
def admin_all_images():
    imgs = []
    for f in sorted(IMAGES_DIR.iterdir()):
        if f.is_file() and f.suffix.lower() in ALLOWED_EXT:
            imgs.append({"name": f.name, "size": f.stat().st_size})
    return jsonify(imgs)

@app.route("/admin/api/image", methods=["POST"])
@admin_required
def admin_upload_image():
    """Upload a standalone image (not assigned to any gallery)."""
    file = request.files.get("image")
    if not file or not file.filename:
        return jsonify({"error": "No file provided"}), 400
    clean = safe_filename(file.filename)
    if not clean:
        return jsonify({"error": "Invalid file type"}), 400
    fname = unique_filename(IMAGES_DIR, clean)
    file.save(IMAGES_DIR / fname)
    return jsonify({"success": True, "filename": fname})

@app.route("/admin/api/image/<filename>", methods=["DELETE"])
@admin_required
def admin_delete_image(filename):
    clean = safe_filename(filename)
    if not clean:
        return jsonify({"error": "Invalid filename"}), 400
    path = IMAGES_DIR / clean
    if not path.exists():
        return jsonify({"error": "File not found"}), 404
    path.unlink()
    # Also remove from all gallery records
    data = load_galleries()
    for g in data["galleries"]:
        g["images"] = [img for img in g.get("images", []) if img["filename"] != clean]
    save_galleries(data)
    return jsonify({"success": True})


# ─────────────────────────────────────────────
# ADMIN API — Content CRUD
# ─────────────────────────────────────────────
@app.route("/admin/api/pages", methods=["GET"])
@admin_required
def admin_list_pages():
    data = load_pages()
    return jsonify([
        {"id": pid, "name": p["name"], "url": p["url"]}
        for pid, p in data["pages"].items()
    ])

@app.route("/admin/api/page/<page_id>", methods=["GET"])
@admin_required
def admin_get_page(page_id):
    data = load_pages()
    if page_id not in data["pages"]:
        return jsonify({"error": "Page not found"}), 404
    return jsonify(data["pages"][page_id])

@app.route("/admin/api/page/<page_id>/save", methods=["POST"])
@admin_required
def admin_save_page(page_id):
    data = load_pages()
    if page_id not in data["pages"]:
        return jsonify({"error": "Page not found"}), 404
    updates = request.json.get("fields", {})
    page_fields = data["pages"][page_id]["fields"]
    for key, value in updates.items():
        if key in page_fields:  # Only update known keys
            page_fields[key] = value
    save_pages(data)
    return jsonify({"success": True, "fields": page_fields})


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  Sweet Berry Photography — Admin Server")
    print("  Public site:  http://localhost:5000/")
    print("  Admin panel:  http://localhost:5000/admin/")
    print(f"  Password:     {ADMIN_PASSWORD}  ← CHANGE BEFORE DEPLOY")
    print("=" * 55)
    app.run(debug=False, port=5000, host="0.0.0.0")
