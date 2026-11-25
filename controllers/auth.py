from functools import wraps
from flask import session, redirect, url_for, abort
from models.database import query

def current_user():
    uid=session.get("uid")
    return query("SELECT id,name,email,role FROM users WHERE id=%s AND active=1",(uid,),True) if uid else None

def restricted(*roles):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args,**kwargs):
            u=current_user()
            if not u: return redirect(url_for("login"))
            if roles and u["role"] not in roles: abort(403)
            return fn(*args,**kwargs)
        return wrapper
    return deco

