import os, json
from datetime import datetime
from decimal import Decimal
from functools import wraps
from flask import Flask, request, redirect, url_for, session, flash, abort, render_template_string
import pymysql
from pymysql.cursors import DictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()
app=Flask(__name__)
app.secret_key=os.getenv("SECRET_KEY","development-only-change-this")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE")=="1")

def conn():
    from urllib.parse import urlparse, unquote, parse_qs
    url=os.environ["DATABASE_URL"]
    p=urlparse(url)
    if p.scheme not in ("mysql","mysql+pymysql"): raise RuntimeError("DATABASE_URL precisa ser MySQL")
    ssl={"ssl":{}} if parse_qs(p.query).get("ssl",[""])[0]=="true" else {}
    return pymysql.connect(host=p.hostname,port=p.port or 3306,user=unquote(p.username or ""),password=unquote(p.password or ""),database=p.path.lstrip("/"),charset="utf8mb4",cursorclass=DictCursor,autocommit=False,connect_timeout=8,**ssl)

def query(sql, params=(), one=False):
    with conn() as db:
        with db.cursor() as cur:
            cur.execute(sql,params)
            return cur.fetchone() if one else cur.fetchall()

def execute(sql,params=()):
    with conn() as db:
        try:
            with db.cursor() as cur:
                cur.execute(sql,params); ident=cur.lastrowid; changed=cur.rowcount
            db.commit()
            return ident,changed
        except:
            db.rollback(); raise

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

@app.context_processor
def context(): return {"me":current_user(),"money":lambda v:"R$ "+f"{Decimal(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")}

BASE='''<!doctype html><html lang="pt-br"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sabor & Clic</title><link rel="stylesheet" href="/static/style.css"></head><body><header><a class="brand" href="/">SABOR <b>&</b> CLIC</a><nav><a href="/cardapio">Cardápio</a><a href="/espacos">Espaços</a><a href="/pedidos">Pedidos</a><a href="/carrinho">Carrinho <span id="count"></span></a>{% if me %}<a href="/painel">Painel</a><a href="/cozinha">Cozinha</a><a href="/entregas">Entregas</a><form action="/sair" method="post"><button>Sair</button></form>{% else %}<a href="/entrar">Entrar</a>{% endif %}</nav></header><main>{% with messages=get_flashed_messages() %}{% for m in messages %}<p class="alert">{{m}}</p>{% endfor %}{% endwith %}{{ body|safe }}</main><footer>Sabor & Clic · Gestão gastronômica</footer><script src="/static/app.js"></script></body></html>'''

def page(body,**data):
    from flask import render_template_string
    inner=render_template_string(body,**data)
    return render_template_string(BASE,body=inner)

@app.get("/")
def home():
    return page('''<section class="hero"><div><span class="eyebrow">SABOR & CLIC</span><h1>Sua cozinha.<br>Seu sabor.<br><em>Seu negócio.</em></h1><p>Peça seus pratos favoritos e reserve espaços gastronômicos em um só lugar.</p><a class="btn" href="/cardapio">VER CARDÁPIO</a> <a class="btn outline" href="/espacos">VER ESPAÇOS</a></div><div class="heroart">🍲</div></section>''')

@app.route("/cadastro",methods=["GET","POST"])
def register():
    if request.method=="POST":
        name=request.form.get("name","").strip()[:120]; email=request.form.get("email","").strip().lower()[:180]; password=request.form.get("password","")
        if not name or "@" not in email or len(password)<8: flash("Confira os dados e use senha de pelo menos 8 caracteres.")
        elif query("SELECT id FROM users WHERE email=%s",(email,),True): flash("E-mail já cadastrado.")
        else:
            execute("INSERT INTO users(name,email,password_hash,role) VALUES(%s,%s,%s,'cliente')",(name,email,generate_password_hash(password)))
            flash("Conta criada. Entre para continuar."); return redirect("/entrar")
    return page('''<div class="panel narrow"><h1>Criar conta</h1><form method="post"><label>Nome<input name="name" required maxlength="120"></label><label>E-mail<input name="email" type="email" required></label><label>Senha<input name="password" type="password" minlength="8" required></label><button class="btn">Cadastrar</button></form></div>''')

@app.route("/entrar",methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=query("SELECT * FROM users WHERE email=%s AND active=1",(request.form.get("email","").lower().strip(),),True)
        if u and check_password_hash(u["password_hash"],request.form.get("password","")):
            session.clear();session["uid"]=u["id"];return redirect({"admin":"/painel","cozinha":"/cozinha","entregador":"/entregas"}.get(u["role"],"/"))
        flash("E-mail ou senha incorretos.")
    return page('''<div class="panel narrow"><h1>Entrar</h1><form method="post"><label>E-mail<input name="email" type="email" required></label><label>Senha<input name="password" type="password" required></label><button class="btn">Entrar</button></form><p>Não tem conta? <a href="/cadastro">Cadastre-se</a></p></div>''')

@app.post("/sair")
def logout(): session.clear();return redirect("/")

@app.get("/cardapio")
def menu():
    dishes=query("SELECT * FROM dishes WHERE active=1 ORDER BY category,name")
    return page('''<h1>Nosso <em>cardápio</em></h1><div class="cards">{% for d in dishes %}<article class="panel dish"><div class="food">{% if d.image %}<img src="{{d.image}}" alt="{{d.name}}">{% else %}🍽️{% endif %}</div><small>{{d.category}}</small><h2>{{d.name}}</h2><p>{{d.description}}</p><strong>{{money(d.price)}}</strong><button class="btn" onclick='addDish({{d.id}},{{d.name|tojson}},{{d.price|float}})'>Adicionar</button></article>{% else %}<p>Cardápio em preparação.</p>{% endfor %}</div>''',dishes=dishes)

@app.get("/carrinho")
def cart():
    return page('''<h1>Seu <em>pedido</em></h1><div class="panel"><div id="cartItems"></div><h2>Total: <span id="cartTotal">R$ 0,00</span></h2><form action="/pedido/novo" method="post" onsubmit="return prepareOrder(this)"><input type="hidden" name="items" id="itemsInput"><label>Endereço completo<input name="address" minlength="8" required></label><label>Observações<textarea name="notes"></textarea></label><button class="btn">Confirmar pedido (sem pagamento)</button></form></div>''')

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
                cur.execute("INSERT INTO orders(customer_id,name,address,notes,total,status) VALUES(%s,%s,%s,%s,%s,'recebido')",(u["id"],u["name"],address,request.form.get("notes","")[:500],total))
                oid=cur.lastrowid
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
    return page('''<h1>Meus pedidos</h1><div class="cards">{% for o in orders %}<a class="panel" href="/pedido/{{o.id}}"><h2>Pedido #{{o.id}}</h2><p>{{o.status}}</p><strong>{{money(o.total)}}</strong></a>{% else %}<p>Nenhum pedido ainda.</p>{% endfor %}</div>''',orders=data)

@app.get("/pedido/<int:oid>")
@restricted()
def order_detail(oid):
    o=query("SELECT * FROM orders WHERE id=%s",(oid,),True)
    if not o: abort(404)
    u=current_user()
    if u["role"] not in ("admin","cozinha") and u["id"] not in (o["customer_id"],o["courier_id"]): abort(403)
    items=query("SELECT * FROM order_items WHERE order_id=%s",(oid,))
    return page('''<div class="panel"><h1>Pedido #{{o.id}}</h1><p>Estado: <b>{{o.status}}</b></p><p>Entrega: {{o.address}}</p>{% for i in items %}<p>{{i.quantity}}x {{i.name}} — {{money(i.unit_price)}}</p>{% endfor %}<h2>Total {{money(o.total)}}</h2></div>''',o=o,items=items)

@app.get("/espacos")
def spaces():
    data=query("SELECT * FROM spaces WHERE active=1 ORDER BY id")
    return page('''<h1>Espaços <em>gastronômicos</em></h1><div class="cards">{% for s in spaces %}<div class="panel"><h2>{{s.name}}</h2><p>{{s.description}}</p><form action="/espacos/reservar" method="post"><input type="hidden" name="space_id" value="{{s.id}}"><label>Início<input name="start_at" type="datetime-local" required></label><label>Fim<input name="end_at" type="datetime-local" required></label><button class="btn">Reservar</button></form></div>{% endfor %}</div>''',spaces=data)

@app.post("/espacos/reservar")
@restricted()
def reserve():
    try: sid=int(request.form["space_id"]);start=datetime.fromisoformat(request.form["start_at"]);end=datetime.fromisoformat(request.form["end_at"])
    except (ValueError,KeyError): abort(400)
    if start>=end or start<datetime.now() or (end-start).total_seconds()>86400: abort(400)
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
    return page('''<h1>Minhas reservas</h1><div class="cards">{% for b in bookings %}<div class="panel"><h2>{{b.space_name}}</h2><p>{{b.start_at}} até {{b.end_at}}</p><strong>{{b.status}}</strong></div>{% else %}<p>Sem reservas.</p>{% endfor %}</div>''',bookings=data)

@app.get("/painel")
@restricted("admin")
def dashboard():
    counts={key:query("SELECT COUNT(*) AS n FROM "+table,one=True)["n"] for key,table in [("pedidos","orders"),("pratos","dishes"),("bancadas","spaces"),("reservas","bookings")]}
    return page('''<h1>Painel <em>administrativo</em></h1><div class="cards">{% for k,v in counts.items() %}<div class="panel"><h2>{{v}}</h2><p>{{k|capitalize}}</p></div>{% endfor %}</div><div class="links"><a class="btn" href="/painel/pratos">Gerenciar cardápio</a><a class="btn" href="/painel/espacos">Gerenciar espaços</a><a class="btn" href="/painel/equipe">Equipe</a><a class="btn" href="/pedidos">Pedidos</a><a class="btn" href="/minhas-reservas">Reservas</a></div>''',counts=counts)

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
    return page('''<h1>Gerenciar cardápio</h1><div class="panel"><form method="post"><label>Nome<input name="name" required></label><label>Descrição<input name="description"></label><label>Categoria<select name="category"><option>Pratos</option><option>Combos</option><option>Bebidas</option></select></label><label>Preço<input type="number" name="price" min="0.01" step="0.01" required></label><label>Imagem HTTPS<input name="image"></label><button class="btn">Novo prato</button></form></div><div class="cards">{% for d in dishes %}<div class="panel"><h2>{{d.name}}</h2><p>{{money(d.price)}} · {{'Ativo' if d.active else 'Inativo'}}</p><form action="/painel/pratos/{{d.id}}/alternar" method="post"><button>Ativar / desativar</button></form></div>{% endfor %}</div>''',dishes=data)

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
    return page('''<h1>Gerenciar bancadas</h1><div class="panel"><form method="post"><label>Nome<input name="name" required></label><label>Descrição<input name="description"></label><button class="btn">Adicionar</button></form></div><div class="cards">{% for s in spaces %}<div class="panel"><h2>{{s.name}}</h2><p>{{s.description}} · {{'Disponível' if s.active else 'Inativa'}}</p><form method="post" action="/painel/espacos/{{s.id}}/alternar"><button>Ativar / desativar</button></form></div>{% endfor %}</div>''',spaces=data)

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
    return page('''<h1>Equipe e permissões</h1><div class="panel"><form method="post"><label>E-mail de usuário cadastrado<input name="email" type="email" required></label><label>Perfil<select name="role"><option>cliente</option><option>cozinha</option><option>entregador</option></select></label><button class="btn">Atualizar perfil</button></form></div><div class="panel">{% for u in users %}<p>{{u.name}} · {{u.email}} · <b>{{u.role}}</b></p>{% endfor %}</div>''',users=users)

@app.get("/cozinha")
@restricted("admin","cozinha")
def kitchen():
    orders=query("SELECT * FROM orders WHERE status IN ('recebido','preparo','pronto') ORDER BY id")
    bookings=query("SELECT b.*,s.name AS space_name,u.name AS responsible FROM bookings b JOIN spaces s ON s.id=b.space_id JOIN users u ON u.id=b.user_id WHERE b.status='confirmada' AND b.end_at>=NOW() ORDER BY b.start_at LIMIT 40")
    return page('''<h1>Central da <em>cozinha</em></h1><div class="cards">{% for o in orders %}<div class="panel"><h2>Pedido #{{o.id}}</h2><p>{{o.status}} · {{o.name}}</p><form method="post" action="/cozinha/{{o.id}}/avancar"><button class="btn" {% if o.status=='pronto' %}disabled{% endif %}>{{'Iniciar preparo' if o.status=='recebido' else 'Marcar pronto' if o.status=='preparo' else 'Aguardando entregador'}}</button></form></div>{% else %}<p>Nenhum pedido pendente.</p>{% endfor %}</div><h2>Bancadas reservadas</h2><div class="cards">{% for b in bookings %}<div class="panel"><b>{{b.space_name}}</b><p>{{b.responsible}}</p><p>{{b.start_at}} — {{b.end_at}}</p></div>{% endfor %}</div>''',orders=orders,bookings=bookings)

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
    return page('''<h1>Área do <em>entregador</em></h1><div class="cards">{% for o in orders %}<div class="panel"><h2>Pedido #{{o.id}}</h2><p>{{o.address}}</p><p>{{money(o.total)}}</p>{% if o.status=='pronto' %}<form action="/entregas/{{o.id}}/aceitar" method="post"><button class="btn">Aceitar entrega</button></form>{% else %}<form action="/entregas/{{o.id}}/concluir" method="post"><button class="btn">Marcar entregue</button></form>{% endif %}</div>{% else %}<p>Sem entregas disponíveis.</p>{% endfor %}</div>''',orders=orders)

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

@app.get("/saude")
def health():return {"ok":True}

@app.cli.command("init-db")
def init_db():
    with open(os.path.join(os.path.dirname(__file__),"schema.sql"),encoding="utf-8") as f: statements=f.read().split(";")
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
                cur.execute("INSERT IGNORE INTO users(name,email,password_hash,role) VALUES('Administrador',%s,%s,'admin')",(email,generate_password_hash(password)))
        db.commit()
    print("Banco inicializado.")

if __name__=="__main__":app.run(debug=os.getenv("FLASK_DEBUG")=="1")
