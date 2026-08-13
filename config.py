# ---------------------------------------------------
# CONFIGURACIÓN DEL TALLER
# ---------------------------------------------------

# Host/puerto en los que corre Flask (esto lo maneja el hosting en la nube, no lo toques).
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5000

# URL PÚBLICA del servidor una vez desplegado en la nube (Render, Railway, PythonAnywhere, etc).
# Ejemplo: "https://mi-taller.onrender.com"
# La app de escritorio usa esta URL para hablar con el servidor desde cualquier lugar,
# y también se usa para generar el QR general del taller.
PUBLIC_URL = "https://CAMBIAR-por-tu-url.onrender.com"

# Clave simple para que solo vos (admin) puedas usar la app de escritorio contra el servidor.
# Poné cualquier texto secreto, el mismo acá y en las variables de entorno del hosting.
ADMIN_KEY = "cambia-esta-clave-secreta"

# --- WhatsApp (CallMeBot) ---
WHATSAPP_ENABLED = False          # poné True cuando tengas tu apikey
WHATSAPP_PHONE = ""               # tu número con código de país, sin "+", ej: "5493511234567"
WHATSAPP_APIKEY = ""              # el que te devuelve CallMeBot
