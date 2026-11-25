import json
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal
from flask import request, redirect, url_for, session, flash, abort, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import conn, query, execute
from controllers.auth import current_user, restricted


def register_routes(app, limiter):
    @app.get("/espacos")
    def spaces():
        data=query("SELECT * FROM spaces WHERE active=1 ORDER BY id")
        return render_template("spaces.html",spaces=data)

    @app.post("/espacos/reservar")
    @restricted()
    def reserve():
        try: sid=int(request.form["space_id"]);start=datetime.fromisoformat(request.form["start_at"]);end=datetime.fromisoformat(request.form["end_at"])
        except (ValueError,KeyError): abort(400)
        if start>=end or start<datetime.now(ZoneInfo('America/Sao_Paulo')).replace(tzinfo=None) or (end-start).total_seconds()>86400: abort(400)
        with conn() as db:
            try:
                with db.cursor() as cur:
                    cur.execute("SELECT * FROM spaces WHERE id=%s AND active=1 FOR UPDATE",(sid,))
                    if not cur.fetchone(): abort(404)
                    cur.execute("SELECT id FROM bookings WHERE space_id=%s AND status='confirmada' AND start_at<%s AND end_at>%s LIMIT 1",(sid,end,start))
                    if cur.fetchone(): flash("Horário indisponível.");return redirect("/espacos")
                    cur.execute("INSERT INTO bookings(space_id,user_id,start_at,end_at,status) VALUES(%s,%s,%s,%s,'confirmada')",(sid,session["uid"],start,end))
                db.commit()
            except:
                db.rollback();raise
        flash("Reserva confirmada.");return redirect("/minhas-reservas")

    @app.get("/minhas-reservas")
    @restricted()
    def my_bookings():
        u=current_user()
        sql="SELECT b.*,s.name AS space_name FROM bookings b JOIN spaces s ON s.id=b.space_id"
        data=query(sql+" ORDER BY b.start_at DESC") if u["role"]=="admin" else query(sql+" WHERE b.user_id=%s ORDER BY b.start_at DESC",(u["id"],))
        return render_template("my_bookings.html",bookings=data)

