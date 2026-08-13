"""
Envío de notificaciones a WhatsApp.

Para la DEMO usamos CallMeBot (gratis, pensado para notificaciones personales):
  1. Desde el WhatsApp del ADMIN (el tuyo), envía el mensaje "I allow callmebot to send me messages"
     al contacto +34 644 59 71 67.
  2. Te va a responder con tu "apikey" personal.
  3. Poné tu número (con código de país, sin +) y ese apikey en config.py.

Si en el futuro quieren algo más robusto/empresarial (varios admins, más volumen),
se reemplaza esta función por la API oficial de WhatsApp Business (Meta) o Twilio,
sin tocar el resto de la app.
"""
import urllib.parse
import requests
from config import WHATSAPP_PHONE, WHATSAPP_APIKEY, WHATSAPP_ENABLED


def send_whatsapp(message: str) -> tuple[bool, str]:
    if not WHATSAPP_ENABLED:
        return False, "Notificaciones de WhatsApp desactivadas en config.py"

    if not WHATSAPP_PHONE or not WHATSAPP_APIKEY:
        return False, "Falta configurar WHATSAPP_PHONE / WHATSAPP_APIKEY en config.py"

    try:
        text = urllib.parse.quote(message)
        url = f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_PHONE}&text={text}&apikey={WHATSAPP_APIKEY}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return True, "Enviado"
        return False, f"Error HTTP {resp.status_code}: {resp.text}"
    except Exception as e:
        return False, f"Error de conexión: {e}"
