# ---------------------------------------------------
# CONFIGURACIÓN DEL TALLER
# ---------------------------------------------------

# IP local de la computadora donde corre el servidor.
# Los celulares de los trabajadores deben estar en la MISMA red WiFi.
# Para saber tu IP local: en Windows "ipconfig", en Mac/Linux "ifconfig" o "ip a".
SERVER_HOST = "0.0.0.0"   # no cambiar, permite conexiones desde otros dispositivos
SERVER_PORT = 5000
SERVER_IP_PARA_QR = "192.168.1.51"  # <-- CAMBIAR por la IP real de tu compu

# --- WhatsApp (CallMeBot) ---
WHATSAPP_ENABLED = False          # poné True cuando tengas tu apikey
WHATSAPP_PHONE = ""               # tu número con código de país, sin "+", ej: "5493511234567"
WHATSAPP_APIKEY = ""              # el que te devuelve CallMeBot
