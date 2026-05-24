import sqlite3
from werkzeug.security import generate_password_hash
import database as db

def setup_admin():
    username = "genelbaskan"
    password = "efecan123+"
    hashed = generate_password_hash(password)
    
    # Veritabanını hazırla
    db.init_db()
    
    with db.get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user:
            print("Admin hesabı zaten var, şifre güncelleniyor...")
            conn.execute("UPDATE users SET password_hash = ? WHERE username = ?", (hashed, username))
        else:
            print("Admin hesabı oluşturuluyor...")
            conn.execute(
                "INSERT INTO users (username, password_hash, role, first_name, last_name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (username, hashed, "admin", "Efecan", "Bayındır", db.utc_now())
            )
        print("\nİşlem başarılı!")
        print(f"Kullanıcı adı: {username}")
        print(f"Şifre: {password}")

if __name__ == "__main__":
    setup_admin()
