import json
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal
from flask import request, redirect, url_for, session, flash, abort, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import conn, query, execute
from controllers.auth import current_user, restricted


def register_routes(app, limiter):
    @app.get("/")
    def home():
        return render_template("home.html")

    @app.get("/cardapio")
    def menu():
        dishes=query("SELECT * FROM dishes WHERE active=1 ORDER BY category,name")
        return render_template("menu.html",dishes=dishes)

    @app.get("/saude")
    def health():return {"ok":True}

