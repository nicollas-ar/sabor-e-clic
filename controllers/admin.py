import json
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal
from flask import request, redirect, url_for, session, flash, abort, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import conn, query, execute
from controllers.auth import current_user, restricted


def register_routes(app, limiter):
    @app.get("/painel")
    @restricted("admin")
    def dashboard():
        counts={key:query("SELECT COUNT(*) AS n FROM "+table,one=True)["n"] for key,table in [("pedidos","orders"),("pratos","dishes"),("bancadas","spaces"),("reservas","bookings")]}
        return render_template("dashboard.html",counts=counts)

    @app.route("/painel/pratos",methods=["GET","POST"])
    @restricted("admin")
    def manage_dishes():
        if request.method=="POST":
            name=request.form.get("name","").strip()[:130]
            try: price=Decimal(request.form.get("price","0"))
            except: price=Decimal("0")
            if not name or not (0<price<100000): abort(400)
            image=request.form.get("image","")[:500]
            if image and not image.startswith("https://"): image=""
            execute("INSERT INTO dishes(name,description,category,price,image,active) VALUES(%s,%s,%s,%s,%s,1)",(name,request.form.get("description","")[:400],request.form.get("category","Pratos")[:30],price,image))
            return redirect("/painel/pratos")
        data=query("SELECT * FROM dishes ORDER BY id DESC")
        return render_template("manage_dishes.html",dishes=data)

    @app.post("/painel/pratos/<int:did>/alternar")
    @restricted("admin")
    def toggle_dish(did): execute("UPDATE dishes SET active=1-active WHERE id=%s",(did,));return redirect("/painel/pratos")

    @app.route("/painel/espacos",methods=["GET","POST"])
    @restricted("admin")
    def manage_spaces():
        if request.method=="POST":
            name=request.form.get("name","").strip()[:120]
            if name: execute("INSERT INTO spaces(name,description,active) VALUES(%s,%s,1)",(name,request.form.get("description","")[:300]))
            return redirect("/painel/espacos")
        data=query("SELECT * FROM spaces")
        return render_template("manage_spaces.html",spaces=data)

    @app.post("/painel/espacos/<int:sid>/alternar")
    @restricted("admin")
    def toggle_space(sid):execute("UPDATE spaces SET active=1-active WHERE id=%s",(sid,));return redirect("/painel/espacos")

    @app.route("/painel/equipe",methods=["GET","POST"])
    @restricted("admin")
    def team():
        if request.method=="POST":
            email=request.form.get("email","").lower().strip();role=request.form.get("role")
            if role not in ("cliente","cozinha","entregador"): abort(400)
            execute("UPDATE users SET role=%s WHERE email=%s AND id<>%s",(role,email,session["uid"]))
            return redirect("/painel/equipe")
        users=query("SELECT id,name,email,role FROM users ORDER BY id DESC")
        return render_template("team.html",users=users)

