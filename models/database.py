import os
import psycopg
from psycopg.rows import dict_row

def conn():
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row, connect_timeout=10, options="-c timezone=America/Sao_Paulo")


def query(sql, params=(), one=False):
    with conn() as db:
        with db.cursor() as cur:
            cur.execute(sql,params)
            return cur.fetchone() if one else cur.fetchall()

def execute(sql,params=()):
    with conn() as db:
        try:
            with db.cursor() as cur:
                cur.execute(sql,params); changed=cur.rowcount
            db.commit()
            return None,changed
        except:
            db.rollback(); raise

