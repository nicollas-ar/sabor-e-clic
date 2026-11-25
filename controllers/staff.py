import json
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal
from flask import request, redirect, url_for, session, flash, abort, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import conn, query, execute
from controllers.auth import current_user, restricted


def register_routes(app, limiter):
    @app.get("/cozinha")
    @restricted("admin","cozinha")
    def kitchen():
        orders=query("SELECT * FROM orders WHERE status IN ('recebido','preparo','pronto') ORDER BY id")
        bookings=query("SELECT b.*,s.name AS space_name,u.name AS responsible FROM bookings b JOIN spaces s ON s.id=b.space_id JOIN users u ON u.id=b.user_id WHERE b.status='confirmada' AND b.end_at>=LOCALTIMESTAMP ORDER BY b.start_at LIMIT 40")
        return render_template("kitchen.html",orders=orders,bookings=bookings)

    @app.post("/cozinha/<int:oid>/avancar")
    @restricted("admin","cozinha")
    def kitchen_advance(oid):
        execute("UPDATE orders SET status=CASE WHEN status='recebido' THEN 'preparo' WHEN status='preparo' THEN 'pronto' ELSE status END WHERE id=%s AND status IN ('recebido','preparo')",(oid,))
        return redirect("/cozinha")

    @app.get("/entregas")
    @restricted("admin","entregador")
    def deliveries():
        uid=session["uid"]
        orders=query("SELECT * FROM orders WHERE (status='pronto' AND courier_id IS NULL) OR (courier_id=%s AND status='em_rota') ORDER BY id",(uid,))
        return render_template("deliveries.html",orders=orders)

    @app.post("/entregas/<int:oid>/aceitar")
    @restricted("admin","entregador")
    def accept(oid):
        execute("UPDATE orders SET courier_id=%s,status='em_rota' WHERE id=%s AND status='pronto' AND courier_id IS NULL",(session["uid"],oid))
        return redirect("/entregas")

    @app.post("/entregas/<int:oid>/concluir")
    @restricted("admin","entregador")
    def complete(oid):
        execute("UPDATE orders SET status='entregue' WHERE id=%s AND courier_id=%s AND status='em_rota'",(oid,session["uid"]))
        return redirect("/entregas")

