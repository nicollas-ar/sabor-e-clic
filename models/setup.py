import os
from werkzeug.security import generate_password_hash
from models.database import conn

def init_db():
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)),"schema.sql"),encoding="utf-8") as f: statements=f.read().split(";")
    with conn() as db:
        with db.cursor() as cur:
            for statement in statements:
                if statement.strip():cur.execute(statement)
            cur.execute("SELECT COUNT(*) AS n FROM dishes")
            if not cur.fetchone()["n"]:
                for name,category,price in [("Lasanha da casa","Pratos","29.99"),("Prato especial","Pratos","34.90"),("Combo executivo","Combos","39.90"),("Limonada natural","Bebidas","14.99")]:
                    cur.execute("INSERT INTO dishes(name,category,price) VALUES(%s,%s,%s)",(name,category,price))
            cur.execute("SELECT COUNT(*) AS n FROM spaces")
            if not cur.fetchone()["n"]:
                for name in ("Bancada 01","Bancada 02","Bancada Premium"):cur.execute("INSERT INTO spaces(name) VALUES(%s)",(name,))
            email=os.getenv("ADMIN_EMAIL","").strip().lower();password=os.getenv("ADMIN_PASSWORD","")
            if email and len(password)>=12:
                cur.execute("SELECT id FROM users WHERE email=%s",(email,))
                existing_admin = cur.fetchone()
                password_hash = generate_password_hash(password)
                if existing_admin:
                    cur.execute(
                        "UPDATE users SET password_hash=%s, role='admin', active=1 WHERE id=%s",
                        (password_hash, existing_admin["id"])
                    )
                else:
                    cur.execute(
                        "INSERT INTO users(name,email,password_hash,role,active) VALUES('Administrador',%s,%s,'admin',1)",
                        (email, password_hash)
                    )
        db.commit()
    print("Banco inicializado.")

