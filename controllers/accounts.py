import json
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal
from flask import request, redirect, url_for, session, flash, abort, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import conn, query, execute
from controllers.auth import current_user, restricted


def register_routes(app, limiter):
    @app.route("/cadastro",methods=["GET","POST"])
    @limiter.limit("5 per hour", methods=["POST"])
    def register():
        if request.method=="POST":
            name=request.form.get("name","").strip()[:120]; email=request.form.get("email","").strip().lower()[:180]; password=request.form.get("password","")
            if not name or "@" not in email or len(password)<8: flash("Confira os dados e use senha de pelo menos 8 caracteres.")
            elif query("SELECT id FROM users WHERE email=%s",(email,),True): flash("E-mail já cadastrado.")
            else:
                execute("INSERT INTO users(name,email,password_hash,role) VALUES(%s,%s,%s,'cliente')",(name,email,generate_password_hash(password)))
                flash("Conta criada. Entre para continuar."); return redirect("/entrar")
        return render_template("register.html")

    @app.route("/entrar",methods=["GET","POST"])
    @limiter.limit("10 per minute", methods=["POST"])
    def login():
        if request.method=="POST":
            u=query("SELECT * FROM users WHERE email=%s AND active=1",(request.form.get("email","").lower().strip(),),True)
            if u and check_password_hash(u["password_hash"],request.form.get("password","")):
                session.clear();session["uid"]=u["id"];return redirect({"admin":"/painel","cozinha":"/cozinha","entregador":"/entregas"}.get(u["role"],"/"))
            flash("E-mail ou senha incorretos.")
        return render_template("login.html")

    @app.post("/sair")
    def logout(): session.clear();return redirect("/")

