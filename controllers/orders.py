import json
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal
from flask import request, redirect, url_for, session, flash, abort, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import conn, query, execute
from controllers.auth import current_user, restricted


def register_routes(app, limiter):
    @app.get("/carrinho")
    def cart():
        return render_template("cart.html")

    @app.post("/pedido/novo")
    @restricted("cliente","admin")
    def checkout():
        try:
            items=json.loads(request.form.get("items","[]"))
            quantities={}
            for item in items:
                did=int(item["id"]);qty=int(item["quantity"])
                if qty<1 or qty>50: abort(400)
                quantities[did]=min(50,quantities.get(did,0)+qty)
        except (ValueError,TypeError,KeyError): abort(400)
        address=request.form.get("address","").strip()[:350]
        if not quantities or len(address)<8: abort(400)
        placeholders=",".join(["%s"]*len(quantities))
        with conn() as db:
            try:
                with db.cursor() as cur:
                    cur.execute("SELECT id,name,price FROM dishes WHERE active=1 AND id IN ("+placeholders+")",tuple(quantities))
                    dishes=cur.fetchall()
                    if len(dishes)!=len(quantities): abort(400)
                    total=sum((d["price"]*quantities[d["id"]] for d in dishes),Decimal("0"))
                    u=current_user()
                    cur.execute("INSERT INTO orders(customer_id,name,address,notes,total,status) VALUES(%s,%s,%s,%s,%s,'recebido') RETURNING id",(u["id"],u["name"],address,request.form.get("notes","")[:500],total))
                    oid=cur.fetchone()["id"]
                    for d in dishes: cur.execute("INSERT INTO order_items(order_id,dish_id,name,quantity,unit_price) VALUES(%s,%s,%s,%s,%s)",(oid,d["id"],d["name"],quantities[d["id"]],d["price"]))
                db.commit()
            except:
                db.rollback();raise
        return redirect(url_for("order_detail",oid=oid))

    @app.get("/pedidos")
    @restricted()
    def orders():
        u=current_user()
        data=query("SELECT * FROM orders ORDER BY id DESC LIMIT 100") if u["role"]=="admin" else query("SELECT * FROM orders WHERE customer_id=%s ORDER BY id DESC",(u["id"],))
        return render_template("orders.html",orders=data)

    @app.get("/pedido/<int:oid>")
    @restricted()
    def order_detail(oid):
        o=query("SELECT * FROM orders WHERE id=%s",(oid,),True)
        if not o: abort(404)
        u=current_user()
        if u["role"] not in ("admin","cozinha") and u["id"] not in (o["customer_id"],o["courier_id"]): abort(403)
        items=query("SELECT * FROM order_items WHERE order_id=%s",(oid,))
        return render_template("order_detail.html",o=o,items=items)

