import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_UPLOAD_MB = 8

# Genel Başkan hesabı (yalnızca bu kullanıcı adı CMS yetkisine sahip)
CHAIRMAN_USERNAME = "genelbaskan"
CHAIRMAN_DEFAULT_PASSWORD = os.environ.get("DOP_CHAIRMAN_PASSWORD", "DomatesGB2026")

RESERVED_USERNAMES = frozenset(
    {
        "genelbaskan",
        "genel_baskan",
        "admin",
        "administrator",
        "efecan",
        "root",
        "system",
    }
)
