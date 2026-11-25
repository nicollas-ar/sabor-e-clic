import os, json
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal
from functools import wraps
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import Flask, request, redirect, url_for, session, flash, abort, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()
app=Flask(__name__)
app.secret_key=os.environ["SECRET_KEY"]
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE")=="1", MAX_CONTENT_LENGTH=1024*1024)
csrf = CSRFProtect(app)
limiter = Limiter(get_remote_address, app=app, default_limits=[], storage_uri="memory://")

@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'; connect-src 'self' https://viacep.com.br; img-src 'self' https: data:; style-src 'self' https://fonts.googleapis.com 'unsafe-inline'; font-src 'self' https://fonts.gstatic.com; script-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
    return response


from controllers.auth import current_user
from models.setup import init_db
@app.context_processor
def context(): return {"me":current_user(),"money":lambda v:"R$ "+f"{Decimal(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")}


from controllers import public
public.register_routes(app, limiter)
from controllers import accounts
accounts.register_routes(app, limiter)
from controllers import orders
orders.register_routes(app, limiter)
from controllers import reservations
reservations.register_routes(app, limiter)
from controllers import admin
admin.register_routes(app, limiter)
from controllers import staff
staff.register_routes(app, limiter)

app.cli.command("init-db")(init_db)

if __name__=="__main__":app.run(debug=os.getenv("FLASK_DEBUG")=="1")
