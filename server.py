from flask import Flask, request, render_template_string, jsonify, send_file
import database as db
from notifications import send_whatsapp
from config import SERVER_HOST, SERVER_PORT
import qrcode, io

app = Flask(__name__)
db.init_db()  # asegura que la base de datos exista apenas arranca el servidor (local o en la nube)

# ---------------------------------------------------------------
# API para que la app de escritorio (admin) administre el inventario
# desde CUALQUIER lugar, sin depender de estar en la misma red.
# Protegida con una clave simple (ver config.py -> ADMIN_KEY).
# ---------------------------------------------------------------
from config import ADMIN_KEY


def check_admin(req):
    return req.headers.get("X-Admin-Key") == ADMIN_KEY and ADMIN_KEY != ""


@app.route("/api/items", methods=["GET", "POST"])
def api_items():
    if not check_admin(request):
        return jsonify({"error": "no autorizado"}), 401
    if request.method == "GET":
        items = [dict(i) for i in db.get_items()]
        return jsonify(items)
    data = request.get_json()
    db.add_item(
        data["name"], data["category"], float(data["quantity"]),
        data["unit"], data.get("location", ""), float(data.get("min_stock", 0))
    )
    return jsonify({"ok": True})


@app.route("/api/items/<int:item_id>", methods=["DELETE"])
def api_delete_item(item_id):
    if not check_admin(request):
        return jsonify({"error": "no autorizado"}), 401
    db.delete_item(item_id)
    return jsonify({"ok": True})


@app.route("/api/movements", methods=["GET"])
def api_movements():
    if not check_admin(request):
        return jsonify({"error": "no autorizado"}), 401
    return jsonify([dict(m) for m in db.get_movements()])


@app.route("/api/notifications", methods=["GET"])
def api_notifications():
    if not check_admin(request):
        return jsonify({"error": "no autorizado"}), 401
    return jsonify([dict(n) for n in db.get_unsent_notifications()])


@app.route("/api/notifications/retry", methods=["POST"])
def api_retry_notifications():
    if not check_admin(request):
        return jsonify({"error": "no autorizado"}), 401
    pending = db.get_unsent_notifications()
    sent = 0
    for n in pending:
        ok, _ = send_whatsapp(n["message"])
        if ok:
            db.mark_notification_sent(n["id"])
            sent += 1
    return jsonify({"sent": sent, "total": len(pending)})


@app.route("/qr")
def qr_general():
    """QR único que apunta al listado general del taller (para imprimir y pegar en el taller)."""
    base_url = request.url_root.rstrip("/")
    img = qrcode.make(base_url + "/")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

LIST_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Inventario del Taller</title>
<style>
  body { font-family: Arial, sans-serif; background:#f2f2f2; margin:0; padding:20px; }
  .card { background:white; border-radius:12px; padding:16px; max-width:480px; margin:0 auto 12px auto; box-shadow:0 2px 8px rgba(0,0,0,.08); display:flex; justify-content:space-between; align-items:center;}
  h2 { text-align:center; color:#222; }
  .name { font-weight:bold; font-size:16px; }
  .meta { color:#666; font-size:13px; margin-top:2px; }
  .qty { font-weight:bold; color:#2563eb; font-size:15px; }
  a.btn { background:#2563eb; color:white; text-decoration:none; padding:10px 14px; border-radius:8px; font-size:14px; white-space:nowrap;}
  .search { max-width:480px; margin:0 auto 16px auto; }
  .search input { width:100%; padding:12px; border-radius:8px; border:1px solid #ccc; font-size:16px; box-sizing:border-box;}
  .empty { text-align:center; color:#999; }
</style>
</head>
<body>
  <h2>🔧 Inventario del Taller</h2>
  <div class="search">
    <input type="text" id="buscador" placeholder="Buscar herramienta o material..." onkeyup="filtrar()">
  </div>
  <div id="lista">
  {% for item in items %}
    <div class="card item-card" data-nombre="{{ item['name']|lower }}">
      <div>
        <div class="name">{{ item['name'] }}</div>
        <div class="meta">{{ item['category']|capitalize }} · {{ item['location'] or 'sin ubicación' }}</div>
        <div class="qty">{{ item['quantity'] }} {{ item['unit'] }} disponibles</div>
      </div>
      <a class="btn" href="/item/{{ item['id'] }}">Registrar</a>
    </div>
  {% else %}
    <p class="empty">No hay ítems cargados todavía.</p>
  {% endfor %}
  </div>
  <script>
    function filtrar() {
      const q = document.getElementById('buscador').value.toLowerCase();
      document.querySelectorAll('.item-card').forEach(function(card) {
        card.style.display = card.dataset.nombre.includes(q) ? 'flex' : 'none';
      });
    }
  </script>
</body>
</html>
"""

FORM_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ item['name'] }} - Registro</title>
<style>
  body { font-family: Arial, sans-serif; background:#f2f2f2; margin:0; padding:20px; }
  .card { background:white; border-radius:12px; padding:20px; max-width:420px; margin:0 auto; box-shadow:0 2px 8px rgba(0,0,0,.1);}
  h2 { color:#222; margin-top:0; }
  .info { background:#eef5ff; padding:10px; border-radius:8px; margin-bottom:16px; font-size:15px;}
  label { display:block; margin-top:14px; font-weight:bold; font-size:14px; }
  input, select { width:100%; padding:10px; margin-top:6px; border-radius:8px; border:1px solid #ccc; font-size:16px; box-sizing:border-box;}
  button { width:100%; margin-top:20px; padding:14px; background:#2563eb; color:white; border:none; border-radius:8px; font-size:16px; font-weight:bold;}
  .msg-ok { background:#dcfce7; color:#166534; padding:12px; border-radius:8px; margin-bottom:16px;}
  .msg-err { background:#fee2e2; color:#991b1b; padding:12px; border-radius:8px; margin-bottom:16px;}
</style>
</head>
<body>
  <div class="card">
    <h2>🔧 {{ item['name'] }}</h2>
    <div class="info">
      Categoría: {{ item['category'] }}<br>
      Disponible ahora: <b>{{ item['quantity'] }} {{ item['unit'] }}</b><br>
      Ubicación: {{ item['location'] or '-' }}
    </div>

    {% if mensaje %}
      <div class="{{ 'msg-ok' if ok else 'msg-err' }}">{{ mensaje }}</div>
    {% endif %}

    <form method="POST">
      <a href="/" style="display:block;text-align:center;margin-bottom:10px;color:#2563eb;">&larr; Volver al listado</a>
      <label>Tu nombre</label>
      <input type="text" name="worker_name" required placeholder="Ej: Juan Pérez">

      <label>¿Qué hacés?</label>
      <select name="action">
        <option value="retiro">Retirar</option>
        <option value="devolucion">Devolver</option>
      </select>

      <label>Cantidad</label>
      <input type="number" step="any" min="0.01" name="quantity" required placeholder="Ej: 1">

      <button type="submit">Confirmar</button>
    </form>
  </div>
</body>
</html>
"""

NOT_FOUND_HTML = """
<!DOCTYPE html><html><body style="font-family:Arial;text-align:center;padding:40px;">
<h2>Ítem no encontrado</h2><p>Consultá con el administrador del taller.</p>
</body></html>
"""


@app.route("/item/<int:item_id>", methods=["GET", "POST"])
def item_form(item_id):
    item = db.get_item(item_id)
    if not item:
        return NOT_FOUND_HTML, 404

    mensaje = None
    ok = False

    if request.method == "POST":
        worker_name = request.form.get("worker_name", "").strip()
        action = request.form.get("action")
        try:
            quantity = float(request.form.get("quantity", 0))
        except ValueError:
            quantity = 0

        if not worker_name or quantity <= 0:
            mensaje = "Completá tu nombre y una cantidad válida."
        else:
            ok, mensaje, new_qty = db.register_movement(item_id, worker_name, action, quantity)
            if ok:
                # Intenta enviar WhatsApp al admin en el momento (best-effort)
                send_whatsapp(mensaje)

        item = db.get_item(item_id)  # refrescar cantidad mostrada

    return render_template_string(FORM_HTML, item=item, mensaje=mensaje, ok=ok)


@app.route("/")
def home():
    items = db.get_items()
    return render_template_string(LIST_HTML, items=items)


def run_server():
    db.init_db()
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=False)


if __name__ == "__main__":
    run_server()
