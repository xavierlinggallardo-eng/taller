from flask import Flask, request, render_template_string
import database as db
from notifications import send_whatsapp
from config import SERVER_HOST, SERVER_PORT

app = Flask(__name__)

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
    return "Servidor de inventario del taller activo. Escaneá el QR de una herramienta para continuar."


def run_server():
    db.init_db()
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=False)


if __name__ == "__main__":
    run_server()
