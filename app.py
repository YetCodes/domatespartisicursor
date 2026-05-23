import json
import re
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from PIL import Image

import database as db
from config import (
    ALLOWED_EXTENSIONS,
    CHAIRMAN_USERNAME,
    MAX_UPLOAD_MB,
    RESERVED_USERNAMES,
    UPLOAD_FOLDER,
)

app = Flask(__name__)
app.secret_key = "dop-domates-partisi-dev-key-change-in-production"
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(UserMixin):
    def __init__(self, row):
        self.id = row["id"]
        self.username = row["username"]
        self.role = row["role"]
        self.first_name = row["first_name"]
        self.last_name = row["last_name"]

    @property
    def is_chairman(self):
        """Yalnızca Genel Başkan (admin) CMS ve kadro düzenleyebilir."""
        return self.role == "admin"

    @property
    def is_admin(self):
        return self.is_chairman

    @property
    def is_official(self):
        return self.role == "official"

    @property
    def is_member(self):
        return self.role in ("admin", "member")

    @property
    def can_vote_congress(self):
        return self.role in ("admin", "member")

    @property
    def role_label(self):
        if self.role == "admin":
            return "Genel Başkan"
        if self.role == "official":
            return "Yetkili"
        if self.role == "member":
            return "Üye"
        return "Vatandaş"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


@login_manager.user_loader
def load_user(user_id):
    with db.get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return User(row) if row else None


def chairman_required(f):
    """CMS / kadro / haber — sadece Genel Başkan."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_chairman:
            flash("Bu işlem yalnızca Genel Başkan hesabıyla yapılabilir.", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated


admin_required = chairman_required


def get_site_context(conn):
    cms = db.get_cms(conn)
    active_congress = conn.execute(
        "SELECT * FROM congress_sessions WHERE active = 1 AND passed = 0 ORDER BY id DESC LIMIT 1"
    ).fetchone()
    notifications = []
    if current_user.is_authenticated and current_user.is_chairman:
        notifications = conn.execute(
            "SELECT * FROM admin_notifications WHERE read = 0 ORDER BY id DESC LIMIT 20"
        ).fetchall()
    return {
        "cms": cms,
        "active_congress": dict(active_congress) if active_congress else None,
        "admin_notifications": [dict(n) for n in notifications],
        "is_chairman": current_user.is_authenticated and current_user.is_chairman,
    }


@app.context_processor
def inject_globals():
    with db.get_db() as conn:
        ctx = get_site_context(conn)
    ctx["current_user"] = current_user
    ctx["cms_visible"] = lambda key: db.cms_visible(ctx["cms"], key)
    return ctx


def _fetch_home_content(conn):
    return {
        "slides": [dict(r) for r in conn.execute("SELECT * FROM carousel_slides ORDER BY sort_order, id").fetchall()],
        "news": [dict(r) for r in conn.execute("SELECT * FROM news_articles ORDER BY featured DESC, sort_order, id").fetchall()],
        "press": [dict(r) for r in conn.execute("SELECT * FROM press_releases ORDER BY sort_order, id LIMIT 5").fetchall()],
        "events": [dict(r) for r in conn.execute("SELECT * FROM events ORDER BY event_date, sort_order").fetchall()],
        "media": [dict(r) for r in conn.execute("SELECT * FROM media_items ORDER BY sort_order, id").fetchall()],
        "agenda": [dict(r) for r in conn.execute("SELECT * FROM agenda_items ORDER BY sort_order, id").fetchall()],
    }


def _member_options(conn):
    rows = conn.execute(
        "SELECT id, first_name, last_name, username FROM users WHERE role IN ('member', 'official') ORDER BY first_name"
    ).fetchall()
    return [
        {
            "id": r["id"],
            "label": f"{r['first_name']} {r['last_name']} (@{r['username']})",
            "name": f"{r['first_name']} {r['last_name']}",
        }
        for r in rows
    ]


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename):
        return None
    name = secure_filename(file_storage.filename)
    stamp = db.utc_now().replace(":", "").replace("-", "")[:15]
    dest = UPLOAD_FOLDER / f"{stamp}_{name}"
    
    try:
        img = Image.open(file_storage)
        img.thumbnail((1920, 1080), Image.Resampling.LANCZOS)
        # Convert to RGB if necessary before saving as JPEG/WEBP
        if img.mode in ('RGBA', 'P') and dest.suffix.lower() in ('.jpg', '.jpeg'):
            img = img.convert('RGB')
        img.save(dest, optimize=True, quality=70)
    except Exception as e:
        return None

    return url_for("static", filename=f"uploads/{dest.name}")


@app.route("/")
def index():
    with db.get_db() as conn:
        content = _fetch_home_content(conn)
        ctx = get_site_context(conn)
    return render_template("index.html", **content, **ctx)


@app.route("/haberler")
def news_media():
    with db.get_db() as conn:
        ctx = get_site_context(conn)
        return render_template(
            "haberler.html",
            news=[dict(r) for r in conn.execute("SELECT * FROM news_articles ORDER BY created_at DESC").fetchall()],
            press=[dict(r) for r in conn.execute("SELECT * FROM press_releases ORDER BY sort_order").fetchall()],
            events=[dict(r) for r in conn.execute("SELECT * FROM events ORDER BY event_date").fetchall()],
            media=[dict(r) for r in conn.execute("SELECT * FROM media_items ORDER BY sort_order").fetchall()],
            agenda=[dict(r) for r in conn.execute("SELECT * FROM agenda_items ORDER BY sort_order, id").fetchall()],
            **ctx,
        )


@app.route("/sikayet")
def complaint():
    with db.get_db() as conn:
        ctx = get_site_context(conn)
    return render_template("complaint.html", **ctx)


@app.route("/uyeler")
def members():
    with db.get_db() as conn:
        chairman = conn.execute(
            "SELECT id, first_name, last_name, username, role FROM users WHERE role = 'admin' LIMIT 1"
        ).fetchone()
        rows = conn.execute(
            """SELECT id, first_name, last_name, username, role, created_at FROM users
               WHERE role != 'admin' ORDER BY first_name, last_name"""
        ).fetchall()
        members_list = []
        if chairman:
            members_list.append(
                {
                    "id": chairman["id"],
                    "first_name": chairman["first_name"],
                    "last_name": chairman["last_name"],
                    "username": chairman["username"],
                    "role": chairman["role"],
                    "role_label": db.ROLE_LABELS["admin"],
                    "created_at": "",
                    "is_chairman_row": True,
                }
            )
        for r in rows:
            members_list.append(
                {
                    "id": r["id"],
                    "first_name": r["first_name"],
                    "last_name": r["last_name"],
                    "username": r["username"],
                    "role": r["role"],
                    "role_label": db.ROLE_LABELS.get(r["role"], "Üye"),
                    "created_at": r["created_at"],
                    "is_chairman_row": False,
                }
            )
        ctx = get_site_context(conn)
    return render_template("members.html", members_list=members_list, **ctx)


@app.route("/amac-vaatler")
def promises_page():
    with db.get_db() as conn:
        promises = conn.execute("SELECT * FROM promises ORDER BY sort_order, id").fetchall()
        ctx = get_site_context(conn)
    return render_template(
        "promises.html",
        promises=[dict(p) for p in promises],
        **ctx,
    )


@app.route("/kadrolar")
def org_chart():
    with db.get_db() as conn:
        nodes = conn.execute("SELECT * FROM org_nodes ORDER BY sort_order, id").fetchall()
        ctx = get_site_context(conn)
        member_options = _member_options(conn)
    tree = build_org_tree([dict(n) for n in nodes])
    return render_template(
        "org.html",
        tree=tree,
        nodes=[dict(n) for n in nodes],
        member_options=member_options,
        **ctx,
    )


def build_org_tree(nodes):
    by_id = {n["id"]: {**n, "children": []} for n in nodes}
    roots = []
    for node in by_id.values():
        pid = node.get("parent_id")
        if pid and pid in by_id:
            by_id[pid]["children"].append(node)
        else:
            roots.append(node)
    return roots


@app.route("/uye-ol", methods=["GET", "POST"])
def register_member():
    if current_user.is_authenticated:
        flash("Zaten giriş yaptınız.", "success")
        return redirect(url_for("index"))

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        username = request.form.get("username", "").strip().lower()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password_confirm", "")

        if not all([first_name, last_name, username, password]):
            flash("Lütfen zorunlu alanları doldurun.", "error")
        elif len(password) < 6:
            flash("Şifre en az 6 karakter olmalıdır.", "error")
        elif password != password2:
            flash("Şifreler eşleşmiyor.", "error")
        elif not re.match(r"^[a-z0-9_]{3,32}$", username):
            flash("Kullanıcı adı 3-32 karakter; yalnızca harf, rakam ve alt çizgi.", "error")
        elif username in RESERVED_USERNAMES:
            flash("Bu kullanıcı adı kullanılamaz.", "error")
        else:
            row = None
            with db.get_db() as conn:
                exists = conn.execute(
                    "SELECT id FROM users WHERE username = ?", (username,)
                ).fetchone()
                if exists:
                    flash("Bu kullanıcı adı zaten kayıtlı. Giriş yapmayı deneyin.", "error")
                else:
                    conn.execute(
                        """INSERT INTO users (username, password_hash, role, first_name, last_name, created_at, email)
                           VALUES (?, ?, 'member', ?, ?, ?, ?)""",
                        (
                            username,
                            generate_password_hash(password),
                            first_name,
                            last_name,
                            db.utc_now(),
                            email,
                        ),
                    )
                    row = conn.execute(
                        "SELECT * FROM users WHERE username = ?", (username,)
                    ).fetchone()
            if row is not None:
                login_user(User(row))
                flash(
                    f"Hoş geldiniz {first_name}! Üyeliğiniz oluşturuldu ve giriş yaptınız.",
                    "success",
                )
                return redirect(url_for("index"))

    with db.get_db() as conn:
        ctx = get_site_context(conn)
    return render_template("register.html", **ctx)


@app.route("/gonullu-ol")
def join_volunteer():
    with db.get_db() as conn:
        ctx = get_site_context(conn)
    return render_template("cta.html", title="Gönüllü Ol", **ctx)


@app.route("/bagis")
def donate():
    with db.get_db() as conn:
        ctx = get_site_context(conn)
    return render_template("cta.html", title="Bağış Yap", subtitle="Partimize destek olun.", **ctx)


@app.route("/giris", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        with db.get_db() as conn:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if row and check_password_hash(row["password_hash"], password):
            login_user(User(row))
            if row["role"] == "admin":
                flash("Genel Başkan olarak giriş yaptınız.", "success")
            else:
                flash(f"Hoş geldiniz, {row['first_name']}!", "success")
            next_url = request.args.get("next") or url_for("index")
            return redirect(next_url)
        flash("Kullanıcı adı veya şifre hatalı.", "error")
    return render_template("login.html")


@app.route("/cikis")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/yonetim")
@chairman_required
def admin_panel():
    with db.get_db() as conn:
        content = _fetch_home_content(conn)
        promises = conn.execute("SELECT * FROM promises ORDER BY sort_order").fetchall()
        complaints = conn.execute(
            "SELECT * FROM complaints ORDER BY priority DESC, created_at DESC LIMIT 50"
        ).fetchall()
        notifications = conn.execute(
            "SELECT * FROM admin_notifications ORDER BY id DESC LIMIT 30"
        ).fetchall()
        cms = db.get_cms(conn)
        ctx = get_site_context(conn)
        member_options = _member_options(conn)
        all_users = conn.execute(
            """SELECT id, first_name, last_name, username, role, created_at FROM users
               ORDER BY CASE role WHEN 'admin' THEN 0 WHEN 'official' THEN 1 ELSE 2 END, first_name"""
        ).fetchall()
    return render_template(
        "admin.html",
        promises=[dict(p) for p in promises],
        complaints=[dict(c) for c in complaints],
        notifications=[dict(n) for n in notifications],
        member_options=member_options,
        all_users=[dict(u) for u in all_users],
        assignable_roles=db.CHAIRMAN_ASSIGNABLE_ROLES,
        role_labels=db.ROLE_LABELS,
        **content,
        **ctx,
    )


# --- API ---


@app.route("/api/complaint", methods=["POST"])
def api_complaint():
    data = request.get_json() or {}
    identity = data.get("identity_type", "anonim")
    body = (data.get("body") or "").strip()
    if not body:
        return jsonify({"error": "Şikayet metni boş olamaz."}), 400

    priority = db.complaint_priority(identity)
    user_id = current_user.id if current_user.is_authenticated else None

    with db.get_db() as conn:
        conn.execute(
            "INSERT INTO complaints (identity_type, priority, body, user_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (identity, priority, body, user_id, db.utc_now()),
        )
        complaint_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    show_congress_modal = identity == "uye"
    return jsonify(
        {
            "ok": True,
            "id": complaint_id,
            "priority": priority,
            "show_congress_modal": show_congress_modal,
        }
    )


@app.route("/api/congress/ask-chairman", methods=["POST"])
def api_ask_chairman():
    data = request.get_json() or {}
    msg = data.get("message", "Üye şikayeti sonrası Genel Başkana soruldu.")
    with db.get_db() as conn:
        conn.execute(
            "INSERT INTO admin_notifications (type, message, created_at) VALUES (?, ?, ?)",
            ("genel_baskan", msg, db.utc_now()),
        )
    return jsonify({"ok": True})


@app.route("/api/congress/start", methods=["POST"])
@login_required
def api_congress_start():
    if not current_user.can_vote_congress:
        return jsonify({"error": "Kurultay yalnızca üyeler tarafından başlatılabilir."}), 403

    with db.get_db() as conn:
        conn.execute("UPDATE congress_sessions SET active = 0 WHERE active = 1")
        total = conn.execute(
            "SELECT COUNT(*) FROM users WHERE role IN ('member', 'admin')"
        ).fetchone()[0]
        threshold = db.kurultay_threshold(total)
        conn.execute(
            """INSERT INTO congress_sessions
               (active, yes_votes, no_votes, total_members, threshold, created_at)
               VALUES (1, 0, 0, ?, ?, ?)""",
            (total, threshold, db.utc_now()),
        )
        session_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    return jsonify({"ok": True, "session_id": session_id, "threshold_percent": 61, "required_yes": threshold})


@app.route("/api/congress/active")
def api_congress_active():
    with db.get_db() as conn:
        row = conn.execute(
            "SELECT * FROM congress_sessions WHERE active = 1 ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if not row:
            return jsonify({"active": False})
        voted = False
        if current_user.is_authenticated and current_user.can_vote_congress:
            v = conn.execute(
                "SELECT vote FROM congress_votes WHERE session_id = ? AND user_id = ?",
                (row["id"], current_user.id),
            ).fetchone()
            voted = v is not None
        return jsonify(
            {
                "active": True,
                "session": dict(row),
                "voted": voted,
                "passed": bool(row["passed"]),
            }
        )


@app.route("/api/congress/vote", methods=["POST"])
@login_required
def api_congress_vote():
    if not current_user.can_vote_congress:
        return jsonify({"error": "Yalnızca üyeler oy kullanabilir."}), 403

    data = request.get_json() or {}
    vote = data.get("vote")
    if vote not in ("yes", "no"):
        return jsonify({"error": "Geçersiz oy."}), 400

    with db.get_db() as conn:
        session_row = conn.execute(
            "SELECT * FROM congress_sessions WHERE active = 1 ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if not session_row:
            return jsonify({"error": "Aktif kurultay yok."}), 404

        try:
            conn.execute(
                "INSERT INTO congress_votes (session_id, user_id, vote, created_at) VALUES (?, ?, ?, ?)",
                (session_row["id"], current_user.id, vote, db.utc_now()),
            )
        except Exception:
            return jsonify({"error": "Zaten oy kullandınız."}), 400

        yes_count = conn.execute(
            "SELECT COUNT(*) FROM congress_votes WHERE session_id = ? AND vote = 'yes'",
            (session_row["id"],),
        ).fetchone()[0]
        no_count = conn.execute(
            "SELECT COUNT(*) FROM congress_votes WHERE session_id = ? AND vote = 'no'",
            (session_row["id"],),
        ).fetchone()[0]

        passed = db.kurultay_passed(yes_count, session_row["total_members"])
        conn.execute(
            "UPDATE congress_sessions SET yes_votes = ?, no_votes = ?, passed = ? WHERE id = ?",
            (yes_count, no_count, 1 if passed else 0, session_row["id"]),
        )
        if passed:
            conn.execute(
                "UPDATE congress_sessions SET active = 0, closed_at = ? WHERE id = ?",
                (db.utc_now(), session_row["id"]),
            )

    return jsonify(
        {
            "ok": True,
            "yes_votes": yes_count,
            "no_votes": no_count,
            "passed": passed,
            "threshold": session_row["threshold"],
        }
    )


@app.route("/api/admin/cms", methods=["POST"])
@admin_required
def api_admin_cms():
    data = request.get_json() or {}
    with db.get_db() as conn:
        db.set_cms(conn, data)
    return jsonify({"ok": True})


@app.route("/api/admin/carousel", methods=["POST"])
@admin_required
def api_admin_carousel():
    data = request.get_json() or {}
    action = data.get("action")
    with db.get_db() as conn:
        if action == "add":
            conn.execute(
                "INSERT INTO carousel_slides (image_url, headline, sort_order) VALUES (?, ?, ?)",
                (
                    data.get("image_url", "https://placehold.co/1200x500/722F37/F8F6F0?text=Placeholder"),
                    data.get("headline", "Yeni haber"),
                    data.get("sort_order", 0),
                ),
            )
        elif action == "delete":
            conn.execute("DELETE FROM carousel_slides WHERE id = ?", (data.get("id"),))
        elif action == "update":
            conn.execute(
                "UPDATE carousel_slides SET image_url = ?, headline = ?, sort_order = ? WHERE id = ?",
                (data["image_url"], data["headline"], data.get("sort_order", 0), data["id"]),
            )
    return jsonify({"ok": True})


@app.route("/api/admin/promises", methods=["POST"])
@admin_required
def api_admin_promises():
    data = request.get_json() or {}
    action = data.get("action")
    with db.get_db() as conn:
        if action == "add":
            conn.execute(
                "INSERT INTO promises (title, body, sort_order) VALUES (?, ?, ?)",
                (data["title"], data["body"], data.get("sort_order", 0)),
            )
        elif action == "delete":
            conn.execute("DELETE FROM promises WHERE id = ?", (data.get("id"),))
        elif action == "update":
            conn.execute(
                "UPDATE promises SET title = ?, body = ?, sort_order = ? WHERE id = ?",
                (data["title"], data["body"], data.get("sort_order", 0), data["id"]),
            )
    return jsonify({"ok": True})


@app.route("/api/admin/org", methods=["POST"])
@admin_required
def api_admin_org():
    data = request.get_json() or {}
    action = data.get("action")
    with db.get_db() as conn:
        user_id = data.get("user_id")
        person_name = data.get("person_name", "")
        if user_id:
            u = conn.execute(
                "SELECT first_name, last_name FROM users WHERE id = ? AND role IN ('member', 'official')",
                (user_id,),
            ).fetchone()
            if u:
                person_name = f"{u['first_name']} {u['last_name']}"

        if action == "add":
            conn.execute(
                """INSERT INTO org_nodes (parent_id, title, person_name, description, sort_order, user_id, image_url)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    data.get("parent_id"),
                    data.get("title", "Yeni Makam"),
                    person_name,
                    data.get("description", ""),
                    data.get("sort_order", 0),
                    user_id,
                    data.get("image_url", "")
                ),
            )
        elif action == "delete":
            conn.execute("DELETE FROM org_nodes WHERE id = ?", (data.get("id"),))
        elif action == "update":
            conn.execute(
                """UPDATE org_nodes SET parent_id = ?, title = ?, person_name = ?,
                   description = ?, sort_order = ?, user_id = ?, image_url = ? WHERE id = ?""",
                (
                    data.get("parent_id"),
                    data["title"],
                    person_name,
                    data.get("description", ""),
                    data.get("sort_order", 0),
                    user_id,
                    data.get("image_url", ""),
                    data["id"],
                ),
            )
    return jsonify({"ok": True})


@app.route("/api/admin/upload", methods=["POST"])
@chairman_required
def api_admin_upload():
    f = request.files.get("file")
    url = save_upload(f)
    if not url:
        return jsonify({"error": "Geçersiz dosya. PNG, JPG, WEBP yükleyin."}), 400
    return jsonify({"ok": True, "url": url})


@app.route("/api/admin/agenda", methods=["POST"])
@chairman_required
def api_admin_agenda():
    data = request.get_json() or {}
    action = data.get("action")
    with db.get_db() as conn:
        if action == "add":
            conn.execute(
                "INSERT INTO agenda_items (title, body, image_url, published_at, sort_order) VALUES (?, ?, ?, ?, ?)",
                (
                    data["title"],
                    data.get("body", ""),
                    data.get("image_url", ""),
                    db.utc_now(),
                    data.get("sort_order", 0),
                ),
            )
        elif action == "delete":
            conn.execute("DELETE FROM agenda_items WHERE id = ?", (data.get("id"),))
        elif action == "update":
            conn.execute(
                "UPDATE agenda_items SET title=?, body=?, image_url=?, sort_order=? WHERE id=?",
                (data["title"], data.get("body", ""), data.get("image_url", ""), data.get("sort_order", 0), data["id"]),
            )
    return jsonify({"ok": True})


@app.route("/api/admin/news", methods=["POST"])
@chairman_required
def api_admin_news():
    data = request.get_json() or {}
    action = data.get("action")
    with db.get_db() as conn:
        if action == "add":
            conn.execute(
                """INSERT INTO news_articles (title, excerpt, image_url, category, featured, sort_order, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["title"],
                    data.get("excerpt", ""),
                    data.get("image_url", "https://placehold.co/800x600/720017/F8F9FA?text=Haber"),
                    data.get("category", "haber"),
                    int(data.get("featured", 0)),
                    data.get("sort_order", 0),
                    db.utc_now(),
                ),
            )
        elif action == "delete":
            conn.execute("DELETE FROM news_articles WHERE id = ?", (data.get("id"),))
        elif action == "update":
            conn.execute(
                """UPDATE news_articles SET title=?, excerpt=?, image_url=?, category=?, featured=?, sort_order=? WHERE id=?""",
                (
                    data["title"],
                    data.get("excerpt", ""),
                    data["image_url"],
                    data.get("category", "haber"),
                    int(data.get("featured", 0)),
                    data.get("sort_order", 0),
                    data["id"],
                ),
            )
    return jsonify({"ok": True})


@app.route("/api/admin/press", methods=["POST"])
@chairman_required
def api_admin_press():
    data = request.get_json() or {}
    action = data.get("action")
    with db.get_db() as conn:
        if action == "add":
            conn.execute(
                "INSERT INTO press_releases (title, body, published_at, sort_order) VALUES (?, ?, ?, ?)",
                (data["title"], data["body"], db.utc_now(), data.get("sort_order", 0)),
            )
        elif action == "delete":
            conn.execute("DELETE FROM press_releases WHERE id = ?", (data.get("id"),))
        elif action == "update":
            conn.execute(
                "UPDATE press_releases SET title=?, body=?, sort_order=? WHERE id=?",
                (data["title"], data["body"], data.get("sort_order", 0), data["id"]),
            )
    return jsonify({"ok": True})


@app.route("/api/admin/events", methods=["POST"])
@chairman_required
def api_admin_events():
    data = request.get_json() or {}
    action = data.get("action")
    with db.get_db() as conn:
        if action == "add":
            conn.execute(
                "INSERT INTO events (title, location, event_date, description, sort_order) VALUES (?, ?, ?, ?, ?)",
                (data["title"], data["location"], data["event_date"], data.get("description", ""), data.get("sort_order", 0)),
            )
        elif action == "delete":
            conn.execute("DELETE FROM events WHERE id = ?", (data.get("id"),))
        elif action == "update":
            conn.execute(
                "UPDATE events SET title=?, location=?, event_date=?, description=?, sort_order=? WHERE id=?",
                (data["title"], data["location"], data["event_date"], data.get("description", ""), data.get("sort_order", 0), data["id"]),
            )
    return jsonify({"ok": True})


@app.route("/api/admin/media", methods=["POST"])
@chairman_required
def api_admin_media():
    data = request.get_json() or {}
    action = data.get("action")
    with db.get_db() as conn:
        if action == "add":
            conn.execute(
                "INSERT INTO media_items (title, media_type, image_url, video_url, sort_order) VALUES (?, ?, ?, ?, ?)",
                (data["title"], data.get("media_type", "photo"), data.get("image_url", ""), data.get("video_url", ""), data.get("sort_order", 0)),
            )
        elif action == "delete":
            conn.execute("DELETE FROM media_items WHERE id = ?", (data.get("id"),))
        elif action == "update":
            conn.execute(
                "UPDATE media_items SET title=?, media_type=?, image_url=?, video_url=?, sort_order=? WHERE id=?",
                (data["title"], data.get("media_type", "photo"), data["image_url"], data.get("video_url", ""), data.get("sort_order", 0), data["id"]),
            )
    return jsonify({"ok": True})


@app.route("/api/admin/user-role", methods=["POST"])
@chairman_required
def api_admin_user_role():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    new_role = data.get("role")
    if new_role not in db.CHAIRMAN_ASSIGNABLE_ROLES:
        return jsonify({"error": "Geçersiz rütbe. Genel Başkan atanamaz."}), 400
    with db.get_db() as conn:
        target = conn.execute("SELECT id, role FROM users WHERE id = ?", (user_id,)).fetchone()
        if not target:
            return jsonify({"error": "Kullanıcı bulunamadı."}), 404
        if target["role"] == "admin":
            return jsonify({"error": "Genel Başkan rütbesi değiştirilemez."}), 403
        conn.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
    return jsonify({"ok": True, "role": new_role, "role_label": db.ROLE_LABELS.get(new_role)})


@app.route("/api/admin/notifications/read", methods=["POST"])
@chairman_required
def api_notifications_read():
    nid = (request.get_json() or {}).get("id")
    with db.get_db() as conn:
        if nid:
            conn.execute("UPDATE admin_notifications SET read = 1 WHERE id = ?", (nid,))
        else:
            conn.execute("UPDATE admin_notifications SET read = 1")
    return jsonify({"ok": True})


if __name__ == "__main__":
    db.init_db()
    db.seed_if_empty()
    db.migrate_schema()
    app.run(debug=True, port=5000)
