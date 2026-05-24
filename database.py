import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "dop.db"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'official', 'member', 'citizen')),
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS cms_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS carousel_slides (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_url TEXT NOT NULL,
                headline TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS promises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS org_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER,
                title TEXT NOT NULL,
                person_name TEXT DEFAULT '',
                description TEXT DEFAULT '',
                image_url TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0,
                FOREIGN KEY (parent_id) REFERENCES org_nodes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identity_type TEXT NOT NULL,
                priority INTEGER NOT NULL,
                body TEXT NOT NULL,
                user_id INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS admin_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                message TEXT NOT NULL,
                read INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS congress_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                active INTEGER DEFAULT 1,
                yes_votes INTEGER DEFAULT 0,
                no_votes INTEGER DEFAULT 0,
                total_members INTEGER NOT NULL,
                threshold REAL NOT NULL,
                passed INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                closed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS congress_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                vote TEXT NOT NULL CHECK(vote IN ('yes', 'no')),
                created_at TEXT NOT NULL,
                UNIQUE(session_id, user_id),
                FOREIGN KEY (session_id) REFERENCES congress_sessions(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS news_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                excerpt TEXT NOT NULL,
                image_url TEXT NOT NULL,
                category TEXT DEFAULT 'haber',
                featured INTEGER DEFAULT 0,
                sort_order INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS press_releases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                published_at TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                location TEXT NOT NULL,
                event_date TEXT NOT NULL,
                description TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS media_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                media_type TEXT NOT NULL CHECK(media_type IN ('photo', 'video')),
                image_url TEXT NOT NULL,
                video_url TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS agenda_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                image_url TEXT DEFAULT '',
                published_at TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0
            );
            """
        )


def migrate_schema():
    """Mevcut veritabanlarına yeni tablolar ve CMS anahtarları ekler."""
    with get_db() as conn:
        init_db()

        # Rütbe (role) kuralını güncelle ('official' eklendi)
        schema = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'").fetchone()[0]
        if "'official'" not in schema:
            conn.execute("ALTER TABLE users RENAME TO users_old")
            conn.execute('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('admin', 'official', 'member', 'citizen')),
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            ''')
            conn.execute("INSERT INTO users SELECT * FROM users_old")
            conn.execute("DROP TABLE users_old")
        defaults = {
            "nav_news": "Haberler ve Medya",
            "nav_admin": "Genel Başkan Paneli",
            "cta_donate": "Bağış Yap",
            "cta_volunteer": "Gönüllü Ol",
            "cta_member": "Üye Ol",
            "chairman_message_title": "Genel Başkanın Mesajı",
            "chairman_message_body": (
                "Değerli vatandaşlarım; Domates Partisi, Türkiye'yi küresel bir güce dönüştürme "
                "hedefiyle yola çıkmıştır. Birlikte, sarsılmaz vaatlerimizi hayata geçireceğiz."
            ),
            "dop_tv_title": "DOP TV",
            "dop_tv_description": "Parti tanıtım filmleri ve miting görüntüleri.",
            "section_show_hero": "1",
            "section_show_bento": "1",
            "section_show_press": "1",
            "section_show_events": "1",
            "section_show_media": "1",
            "section_show_vision": "1",
            "section_show_agenda_home": "1",
            "nav_promises": "Amaç ve Vaatler",
            "nav_org": "Kadrolar",
            "nav_members": "Üye Listesi",
        }
        for key, value in defaults.items():
            conn.execute(
                "INSERT OR IGNORE INTO cms_settings (key, value) VALUES (?, ?)",
                (key, value),
            )

        if conn.execute("SELECT COUNT(*) FROM news_articles").fetchone()[0] == 0:
            now = utc_now()
            articles = [
                ("İstanbul Mitingi Tamamlandı", "Genel Başkan Efecan Bayındır İstanbul'da binlerce vatandaşla buluştu.", "https://placehold.co/800x600/720017/F8F9FA?text=Istanbul+Miting", "haber", 1, 0, now),
                ("Ekonomi Vizyonu Açıklandı", "Yerli üretim ve ihracat odaklı yeni ekonomi paketi kamuoyuyla paylaşıldı.", "https://placehold.co/600x400/720017/F8F9FA?text=Ekonomi", "haber", 0, 1, now),
                ("Gençlik Kolları Toplantısı", "Türkiye genelinde gençlik temsilcileri Ankara'da bir araya geldi.", "https://placehold.co/600x400/720017/F8F9FA?text=Genclik", "haber", 0, 2, now),
            ]
            for a in articles:
                conn.execute(
                    "INSERT INTO news_articles (title, excerpt, image_url, category, featured, sort_order, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    a,
                )

        if conn.execute("SELECT COUNT(*) FROM press_releases").fetchone()[0] == 0:
            releases = [
                ("Parti Programı Güncellendi", "Domates Partisi 2026 seçim manifestosu yayımlandı.", utc_now(), 0),
                ("Teşkilatlanma Takvimi", "81 ilde il ve ilçe kongre takvimi netleştirildi.", utc_now(), 1),
            ]
            for r in releases:
                conn.execute(
                    "INSERT INTO press_releases (title, body, published_at, sort_order) VALUES (?, ?, ?, ?)",
                    r,
                )

        if conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0:
            events = [
                ("Ankara Büyük Miting", "Ankara", "2026-06-15", "Genel Başkan'ın katılımıyla.", 0),
                ("İzmir Teşkilat Buluşması", "İzmir", "2026-06-22", "İl teşkilatları koordinasyon toplantısı.", 1),
                ("Bursa Halk Buluşması", "Bursa", "2026-07-01", "Vatandaş talepleri dinleme programı.", 2),
            ]
            for e in events:
                conn.execute(
                    "INSERT INTO events (title, location, event_date, description, sort_order) VALUES (?, ?, ?, ?, ?)",
                    e,
                )

        if conn.execute("SELECT COUNT(*) FROM media_items").fetchone()[0] == 0:
            media = [
                ("Miting Görüntüleri", "photo", "https://placehold.co/400x300/720017/F8F9FA?text=Foto+1", "", 0),
                ("Basın Toplantısı", "photo", "https://placehold.co/400x300/720017/F8F9FA?text=Foto+2", "", 1),
                ("DOP TV: Vizyon Konuşması", "video", "https://placehold.co/400x300/720017/F8F9FA?text=DOP+TV", "https://www.youtube.com/embed/dQw4w9WgXcQ", 2),
            ]
            for m in media:
                conn.execute(
                    "INSERT INTO media_items (title, media_type, image_url, video_url, sort_order) VALUES (?, ?, ?, ?, ?)",
                    m,
                )

        try:
            conn.execute("ALTER TABLE org_nodes ADD COLUMN user_id INTEGER REFERENCES users(id)")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE org_nodes ADD COLUMN image_url TEXT DEFAULT ''")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN email TEXT DEFAULT ''")
        except Exception:
            pass

        if conn.execute("SELECT COUNT(*) FROM agenda_items").fetchone()[0] == 0:
            for i, (title, body) in enumerate(
                [
                    ("Parti Gündemi: Ekonomi Paketi", "Yeni ekonomi reformları meclis gündemine taşınacak."),
                    ("Teşkilat Toplantısı Kararı", "İl başkanları ile koordinasyon toplantısı yapılacak."),
                ]
            ):
                conn.execute(
                    "INSERT INTO agenda_items (title, body, image_url, published_at, sort_order) VALUES (?, ?, ?, ?, ?)",
                    (title, body, "", utc_now(), i),
                )

        from config import CHAIRMAN_USERNAME, CHAIRMAN_DEFAULT_PASSWORD
        from werkzeug.security import generate_password_hash

        chairman = conn.execute(
            "SELECT id, username FROM users WHERE role = 'admin' LIMIT 1"
        ).fetchone()
        if chairman and chairman["username"] != CHAIRMAN_USERNAME:
            conn.execute(
                "UPDATE users SET username = ? WHERE id = ?",
                (CHAIRMAN_USERNAME, chairman["id"]),
            )
        if not conn.execute(
            "SELECT id FROM users WHERE username = ?", (CHAIRMAN_USERNAME,)
        ).fetchone():
            conn.execute(
                "INSERT INTO users (username, password_hash, role, first_name, last_name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    CHAIRMAN_USERNAME,
                    generate_password_hash(CHAIRMAN_DEFAULT_PASSWORD),
                    "admin",
                    "Efecan",
                    "Bayındır",
                    utc_now(),
                ),
            )

        try:
            exists = conn.execute("SELECT id FROM users WHERE username = 'yetkili1'").fetchone()
            if not exists:
                conn.execute(
                    "INSERT INTO users (username, password_hash, role, first_name, last_name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    ("yetkili1", generate_password_hash("yetkili123"), "official", "Ali", "Yetkili", utc_now()),
                )
        except Exception:
            pass


def seed_if_empty():
    from werkzeug.security import generate_password_hash

    with get_db() as conn:
        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
            return

        now = utc_now()
        member_hash = generate_password_hash("uye123")

        from config import CHAIRMAN_USERNAME, CHAIRMAN_DEFAULT_PASSWORD

        conn.execute(
            "INSERT INTO users (username, password_hash, role, first_name, last_name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                CHAIRMAN_USERNAME,
                generate_password_hash(CHAIRMAN_DEFAULT_PASSWORD),
                "admin",
                "Efecan",
                "Bayındır",
                now,
            ),
        )
        conn.execute(
            "INSERT INTO users (username, password_hash, role, first_name, last_name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("uye1", member_hash, "member", "Ayşe", "Yılmaz", now),
        )
        conn.execute(
            "INSERT INTO users (username, password_hash, role, first_name, last_name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("uye2", member_hash, "member", "Mehmet", "Kara", now),
        )
        conn.execute(
            "INSERT INTO users (username, password_hash, role, first_name, last_name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("uye3", member_hash, "member", "Zeynep", "Demir", now),
        )

        default_cms = {
            "party_name": "Domates Partisi",
            "party_short": "DOP",
            "chairman": "Efecan Bayındır",
            "vision_text": (
                "Domates Partisi, Kurucu Genel Başkan Efecan Bayındır önderliğinde Türkiye Cumhuriyeti "
                "Cumhurbaşkanlığı vizyonu üzerine inşa edilmiştir. Hedefimiz; seçildiğimiz takdirde "
                "Türkiye'yi teknolojik, ekonomik ve siyasi alanda küresel bir güce dönüştürmek ve "
                "dünya sahnesinde sarsılmaz bir konuma ulaştırmaktır."
            ),
            "nav_home": "Ana Sayfa",
            "nav_complaint": "Şikayet",
            "nav_members": "Üye Listesi",
            "nav_promises": "Amaç ve Vaatler",
            "nav_org": "Kadrolar",
            "nav_admin": "Yönetim",
            "cta_member": "Üye Ol",
            "cta_volunteer": "Gönüllü Ol",
            "cta_donate": "Bağış Yap",
            "nav_news": "Haberler ve Medya",
            "nav_admin": "Genel Başkan Paneli",
            "chairman_message_title": "Genel Başkanın Mesajı",
            "chairman_message_body": (
                "Değerli vatandaşlarım; Domates Partisi, Türkiye'yi Amerika'nın ötesine taşıyacak "
                "küresel güç vizyonuyla yola çıkmıştır."
            ),
            "dop_tv_title": "DOP TV",
            "dop_tv_description": "Parti tanıtım filmleri ve canlı yayın arşivi.",
        }
        for key, value in default_cms.items():
            conn.execute(
                "INSERT INTO cms_settings (key, value) VALUES (?, ?)",
                (key, value),
            )

        slides = [
            (
                "https://placehold.co/1920x1080/720017/F8F9FA?text=DOP+Manşet+1",
                "Genel Başkan Efecan Bayındır bugün İstanbul mitingindeydi",
                0,
            ),
            (
                "https://placehold.co/1920x1080/720017/F8F9FA?text=DOP+Manşet+2",
                "Domates Partisi yeni dönem vizyonunu açıkladı",
                1,
            ),
            (
                "https://placehold.co/1920x1080/720017/F8F9FA?text=DOP+Manşet+3",
                "Üyelik kampanyası tüm illerde devam ediyor",
                2,
            ),
        ]
        for image_url, headline, sort_order in slides:
            conn.execute(
                "INSERT INTO carousel_slides (image_url, headline, sort_order) VALUES (?, ?, ?)",
                (image_url, headline, sort_order),
            )

        promises = [
            ("Teknoloji Liderliği", "Türkiye'yi yapay zeka ve savunma sanayisinde dünya lideri konumuna taşıyacağız."),
            ("Ekonomik Bağımsızlık", "Yerli üretim ve ihracat odaklı sürdürülebilir büyüme modeli kuracağız."),
            ("Adil Yönetim", "Şeffaf, hesap verebilir ve katılımcı demokrasi anlayışını hayata geçireceğiz."),
            ("Küresel Güç", "Uluslararası arenada Türkiye'nin sözünü güçlendirecek diplomatik strateji uygulayacağız."),
        ]
        for i, (title, body) in enumerate(promises):
            conn.execute(
                "INSERT INTO promises (title, body, sort_order) VALUES (?, ?, ?)",
                (title, body, i),
            )

        conn.execute(
            "INSERT INTO org_nodes (parent_id, title, person_name, description, sort_order) VALUES (?, ?, ?, ?, ?)",
            (None, "Genel Başkan", "Efecan Bayındır", "Partinin kurucu lideri ve Cumhurbaşkanı adayı.", 0),
        )
        gb_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        children = [
            ("Genel Başkan Avukatı", "", "Hukuki süreçlerin ve parti tüzüğünün korunmasından sorumludur.", 0),
            ("Özel Kalem", "", "Genel Başkanın resmi yazışma ve program koordinasyonunu yürütür.", 1),
            ("Genel Sekreter", "", "Parti teşkilat yapısının koordinasyonundan sorumludur.", 2),
        ]
        for title, person_name, description, sort_order in children:
            conn.execute(
                "INSERT INTO org_nodes (parent_id, title, person_name, description, sort_order) VALUES (?, ?, ?, ?, ?)",
                (gb_id, title, person_name, description, sort_order),
            )


def get_cms(conn) -> dict:
    rows = conn.execute("SELECT key, value FROM cms_settings").fetchall()
    return {row["key"]: row["value"] for row in rows}


def set_cms(conn, data: dict):
    for key, value in data.items():
        conn.execute(
            "INSERT INTO cms_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )


def kurultay_threshold(total_members: int) -> float:
    """%50 + %15 - %4 = %61"""
    return total_members * 0.61


def kurultay_passed(yes_votes: int, total_members: int) -> bool:
    return yes_votes >= kurultay_threshold(total_members)


def mask_surname(last_name: str) -> str:
    if not last_name:
        return ""
    return last_name[0] + "*" * max(len(last_name) - 1, 6)


def complaint_priority(identity_type: str) -> int:
    return 3 if identity_type == "anonim" else 5


def row_to_dict(row):
    return dict(row) if row else None


def cms_visible(cms: dict, key: str) -> bool:
    return str(cms.get(key, "1")).strip().lower() not in ("0", "false", "off", "hayir", "hayır", "no")


ROLE_LABELS = {
    "admin": "Genel Başkan",
    "official": "Yetkili",
    "member": "Üye",
    "citizen": "Vatandaş",
}

CHAIRMAN_ASSIGNABLE_ROLES = ("member", "official", "citizen")
