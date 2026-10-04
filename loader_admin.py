"""
HAMSE CHEATS VIP LOADER ADMIN
Website-ka loader-kaaga maamula
"""
import os, sqlite3, secrets, json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, session, redirect, url_for, render_template_string, g

APP = Flask(__name__)
APP.secret_key = "hamse_loader_admin_2026_vip"
DB = os.path.join(os.path.dirname(__file__), "loader.db")

# ============================================================
# DATABASE
# ============================================================
def init():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS admin(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        created TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS config(
        id INTEGER PRIMARY KEY,
        key TEXT UNIQUE,
        value TEXT,
        updated TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS announcements(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        message TEXT,
        active INTEGER DEFAULT 1,
        created TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS game_list(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        region TEXT,
        package TEXT,
        version TEXT,
        active INTEGER DEFAULT 1)""")
    c.commit(); c.close()
init()

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB); g.db.row_factory = sqlite3.Row
    return g.db

@APP.teardown_appcontext
def close(e=None):
    d = g.pop("db", None)
    if d: d.close()

# ============================================================
# DEFAULT ADMIN (haddii uusan jirin)
# ============================================================
def ensure_admin():
    d = db()
    row = d.execute("SELECT * FROM admin").fetchone()
    if not row:
        d.execute("INSERT INTO admin(username,password,created) VALUES(?,?,?)",
                  ("hamsecheatsvip","Hamse@2026VIP",datetime.now().isoformat()))
        d.commit()

# ============================================================
# DEFAULT CONFIG
# ============================================================
def ensure_config():
    d = db()
    row = d.execute("SELECT * FROM config").fetchone()
    if not row:
        defaults = {
            "loader_name": "Hamse Cheats vip loader",
            "loader_version": "1.0.0",
            "telegram": "HAMSECHEATS",
            "owner": "@hamsecheatsvip",
            "api_url": "https://hamse-panel-production.up.railway.app",
            "maintenance": "0",
            "force_update": "0",
        }
        for k,v in defaults.items():
            d.execute("INSERT INTO config(key,value,updated) VALUES(?,?,?)",
                      (k,v,datetime.now().isoformat()))
        d.commit()

# ============================================================
# ADMIN PANEL ROUTES
# ============================================================
@APP.route("/")
def home():
    if "admin" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login_page"))

@APP.route("/login", methods=["GET","POST"])
def login_page():
    if request.method == "POST":
        u = request.form.get("u","").strip()
        p = request.form.get("p","").strip()
        d = db()
        row = d.execute("SELECT * FROM admin WHERE username=? AND password=?", (u,p)).fetchone()
        if row:
            session["admin"] = u
            return redirect(url_for("dashboard"))
        return render_template_string(LOGIN_HTML, error="Khalad: Username ama Password")
    return render_template_string(LOGIN_HTML, error=None)

@APP.route("/dashboard")
def dashboard():
    if "admin" not in session: return redirect(url_for("login_page"))
    d = db()
    config = {r["key"]: r["value"] for r in d.execute("SELECT * FROM config").fetchall()}
    anns = [dict(r) for r in d.execute("SELECT * FROM announcements ORDER BY id DESC").fetchall()]
    games = [dict(r) for r in d.execute("SELECT * FROM game_list ORDER BY id DESC").fetchall()]
    return render_template_string(DASH_HTML, u=session["admin"], config=config, anns=anns, games=games)

@APP.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))

# ============================================================
# API — APP-KA WUXUU U SOO DIRAA
# ============================================================
@APP.route("/api/loader/config", methods=["GET","POST"])
def api_loader_config():
    """Loader-ku wuxuu u soo diraa — website-ku wuxuu ku soo celiyaa config-ka."""
    d = db()
    config = {r["key"]: r["value"] for r in d.execute("SELECT * FROM config").fetchall()}
    anns = [dict(r) for r in d.execute("SELECT * FROM announcements WHERE active=1").fetchall()]
    games = [dict(r) for r in d.execute("SELECT * FROM game_list WHERE active=1").fetchall()]
    return jsonify({
        "status": "ok",
        "config": config,
        "announcements": anns,
        "game_list": games
    })

@APP.route("/api/loader/update", methods=["POST"])
def api_loader_update():
    """Loader-ku wuxuu u soo diraa version-ka — website-ku wuxuu hubiyaa haddii update loo baahan yahay."""
    data = request.get_json() or {}
    client_version = data.get("version","0.0.0")
    d = db()
    server_version = d.execute("SELECT value FROM config WHERE key='loader_version'").fetchone()
    server_version = server_version["value"] if server_version else "1.0.0"
    force = d.execute("SELECT value FROM config WHERE key='force_update'").fetchone()
    force = force["value"] == "1" if force else False
    need_update = (client_version != server_version)
    return jsonify({
        "status": "ok",
        "need_update": need_update,
        "force_update": force,
        "server_version": server_version,
        "download_url": "https://hamse-panel-production.up.railway.app/loader.apk"
    })

@APP.route("/api/loader/announcement", methods=["GET"])
def api_loader_announcement():
    d = db()
    anns = [dict(r) for r in d.execute("SELECT * FROM announcements WHERE active=1").fetchall()]
    return jsonify({"status":"ok","announcements":anns})

@APP.route("/api/loader/game_list", methods=["GET"])
def api_loader_game_list():
    d = db()
    games = [dict(r) for r in d.execute("SELECT * FROM game_list WHERE active=1").fetchall()]
    return jsonify({"status":"ok","game_list":games})

# ============================================================
# ADMIN API — BEDDELKA
# ============================================================
@APP.route("/api/admin/config", methods=["POST"])
def api_admin_config():
    if "admin" not in session: return jsonify({"e":"unauth"}),401
    data = request.get_json() or {}
    d = db()
    for k,v in data.items():
        d.execute("INSERT OR REPLACE INTO config(key,value,updated) VALUES(?,?,?)",
                  (k,str(v),datetime.now().isoformat()))
    d.commit()
    return jsonify({"ok":1})

@APP.route("/api/admin/announcement", methods=["POST"])
def api_admin_announcement():
    if "admin" not in session: return jsonify({"e":"unauth"}),401
    data = request.get_json() or {}
    d = db()
    d.execute("INSERT INTO announcements(title,message,active,created) VALUES(?,?,?,?)",
              (data.get("title",""), data.get("message",""), 1, datetime.now().isoformat()))
    d.commit()
    return jsonify({"ok":1})

@APP.route("/api/admin/announcement/delete/<int:i>", methods=["POST"])
def api_admin_ann_delete(i):
    if "admin" not in session: return jsonify({"e":"unauth"}),401
    d = db()
    d.execute("DELETE FROM announcements WHERE id=?", (i,))
    d.commit()
    return jsonify({"ok":1})

@APP.route("/api/admin/game_list", methods=["POST"])
def api_admin_game_list():
    if "admin" not in session: return jsonify({"e":"unauth"}),401
    data = request.get_json() or {}
    d = db()
    d.execute("INSERT INTO game_list(region,package,version,active) VALUES(?,?,?,?)",
              (data.get("region",""), data.get("package",""), data.get("version","4.6.0"), 1))
    d.commit()
    return jsonify({"ok":1})

@APP.route("/api/admin/game_list/delete/<int:i>", methods=["POST"])
def api_admin_game_delete(i):
    if "admin" not in session: return jsonify({"e":"unauth"}),401
    d = db()
    d.execute("DELETE FROM game_list WHERE id=?", (i,))
    d.commit()
    return jsonify({"ok":1})

# ============================================================
# HTML
# ============================================================
LOGIN_HTML = """<!DOCTYPE html><html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hamse Cheats vip loader - Login</title>
<style>
body{background:#0a0a0f;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;padding:20px}
.card{background:#111;border:1px solid #222;border-radius:16px;padding:30px;max-width:380px;width:100%;box-shadow:0 0 60px #ff003320}
h1{color:#ff3355;font-size:22px;text-align:center;margin:0 0 6px}
p{color:#666;text-align:center;font-size:12px;letter-spacing:2px;margin:0 0 24px}
input{width:100%;padding:14px;background:#050505;border:1px solid #222;border-radius:10px;color:#fff;font-size:14px;margin-bottom:12px;box-sizing:border-box}
input:focus{border-color:#ff0033;outline:none}
.btn{width:100%;background:linear-gradient(90deg,#ff0033,#7c00ff);color:#fff;border:0;border-radius:10px;padding:14px;font-size:14px;font-weight:700;cursor:pointer;letter-spacing:1px}
.err{background:#ff003320;color:#ff6b6b;padding:10px;border-radius:8px;font-size:12px;text-align:center;margin-bottom:14px}
</style></head><body>
<div class="card">
<h1>HAMSE CHEATS VIP LOADER</h1>
<p>ADMIN PANEL</p>
{% if error %}<div class="err">{{error}}</div>{% endif %}
<form method="post">
<input name="u" placeholder="Username" required>
<input name="p" type="password" placeholder="Password" required>
<button class="btn" type="submit">LOGIN</button>
</form>
</div></body></html>"""

DASH_HTML = """<!DOCTYPE html><html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hamse Cheats vip loader - Admin</title>
<style>
body{background:#0a0a0f;color:#fff;font-family:sans-serif;margin:0;padding:16px}
h1{color:#ff3355;font-size:18px;margin:0 0 4px}
.sub{color:#666;font-size:11px;letter-spacing:2px;margin-bottom:20px}
.sec{background:#111;border:1px solid #222;border-radius:14px;padding:16px;margin-bottom:14px}
.sec h2{font-size:13px;color:#ff3355;margin:0 0 12px;letter-spacing:1px}
input,textarea{width:100%;padding:12px;background:#050505;border:1px solid #222;border-radius:8px;color:#fff;font-size:13px;margin-bottom:10px;box-sizing:border-box}
textarea{min-height:80px}
.btn{background:linear-gradient(90deg,#ff0033,#7c00ff);color:#fff;border:0;border-radius:8px;padding:12px;font-size:13px;font-weight:700;cursor:pointer;width:100%;letter-spacing:1px}
.row{background:#050505;border:1px solid #1a1a1a;border-radius:8px;padding:10px;margin-bottom:8px;font-size:12px;display:flex;justify-content:space-between;align-items:center}
.row .x{color:#ff6080;cursor:pointer;font-weight:700}
.logout{background:#111;border:1px solid #222;color:#ff6080;padding:8px 14px;border-radius:8px;text-decoration:none;font-size:12px;float:right}
</style></head><body>
<a class="logout" href="/logout">Logout</a>
<h1>HAMSE CHEATS VIP LOADER</h1>
<div class="sub">ADMIN PANEL — {{u}}</div>

<div class="sec">
<h2>⚙️ LOADER CONFIG</h2>
<form id="configForm">
{% for k,v in config.items() %}
<input name="{{k}}" placeholder="{{k}}" value="{{v}}">
{% endfor %}
<button class="btn" type="submit">SAVE CONFIG</button>
</form>
</div>

<div class="sec">
<h2>📢 ANNOUNCEMENTS</h2>
<form id="annForm">
<input name="title" placeholder="Title" required>
<textarea name="message" placeholder="Message" required></textarea>
<button class="btn" type="submit">ADD ANNOUNCEMENT</button>
</form>
{% for a in anns %}
<div class="row">
<div><b>{{a['title']}}</b><br><small>{{a['message']}}</small></div>
<span class="x" onclick="delAnn({{a['id']}})">✕</span>
</div>
{% endfor %}
</div>

<div class="sec">
<h2>🎮 GAME LIST</h2>
<form id="gameForm">
<input name="region" placeholder="Region (Global, Korea, Vietnam, Taiwan)" required>
<input name="package" placeholder="Package (com.tencent.ig)" required>
<input name="version" placeholder="Version (4.6.0)" value="4.6.0">
<button class="btn" type="submit">ADD GAME</button>
</form>
{% for g in games %}
<div class="row">
<div><b>{{g['region']}}</b> — {{g['package']}} ({{g['version']}})</div>
<span class="x" onclick="delGame({{g['id']}})">✕</span>
</div>
{% endfor %}
</div>

<script>
document.getElementById('configForm').onsubmit = async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const obj = {};
  fd.forEach((v,k) => obj[k] = v);
  const r = await fetch('/api/admin/config', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(obj)});
  alert('✅ Config la kaydiyay');
};
document.getElementById('annForm').onsubmit = async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const obj = {};
  fd.forEach((v,k) => obj[k] = v);
  await fetch('/api/admin/announcement', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(obj)});
  location.reload();
};
document.getElementById('gameForm').onsubmit = async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const obj = {};
  fd.forEach((v,k) => obj[k] = v);
  await fetch('/api/admin/game_list', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(obj)});
  location.reload();
};
async function delAnn(i){ if(!confirm('Tirtir?')) return; await fetch('/api/admin/announcement/delete/'+i,{method:'POST'}); location.reload(); }
async function delGame(i){ if(!confirm('Tirtir?')) return; await fetch('/api/admin/game_list/delete/'+i,{method:'POST'}); location.reload(); }
</script>
</body></html>"""

if __name__ == "__main__":
    with APP.app_context():
        ensure_admin()
        ensure_config()
    print("HAMSE CHEATS VIP LOADER ADMIN wuu shaqeynayaa")
    print("Fur: http://127.0.0.1:5001")
    APP.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)))
