import sqlite3
from datetime import datetime

DB_PATH = "taller.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,      -- 'herramienta' o 'material'
            quantity REAL NOT NULL,
            unit TEXT NOT NULL,          -- piezas, metros, litros, kg, etc.
            location TEXT,
            min_stock REAL DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            worker_name TEXT NOT NULL,
            action TEXT NOT NULL,        -- 'retiro' o 'devolucion'
            quantity REAL NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (item_id) REFERENCES items (id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS pending_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            sent INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def add_item(name, category, quantity, unit, location, min_stock=0):
    conn = get_conn()
    conn.execute(
        "INSERT INTO items (name, category, quantity, unit, location, min_stock) VALUES (?,?,?,?,?,?)",
        (name, category, quantity, unit, location, min_stock),
    )
    conn.commit()
    conn.close()


def get_items():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM items ORDER BY name").fetchall()
    conn.close()
    return rows


def get_item(item_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    conn.close()
    return row


def update_item_quantity(item_id, new_quantity):
    conn = get_conn()
    conn.execute("UPDATE items SET quantity=? WHERE id=?", (new_quantity, item_id))
    conn.commit()
    conn.close()


def delete_item(item_id):
    conn = get_conn()
    conn.execute("DELETE FROM items WHERE id=?", (item_id,))
    conn.commit()
    conn.close()


def register_movement(item_id, worker_name, action, quantity):
    """Registra el movimiento y actualiza el stock. Devuelve (ok, mensaje, nueva_cantidad)."""
    item = get_item(item_id)
    if not item:
        return False, "Ítem no encontrado", None

    current = item["quantity"]
    if action == "retiro":
        new_qty = current - quantity
    elif action == "devolucion":
        new_qty = current + quantity
    else:
        return False, "Acción inválida", None

    if new_qty < 0:
        return False, f"No hay suficiente stock. Disponible: {current}", None

    update_item_quantity(item_id, new_qty)

    conn = get_conn()
    conn.execute(
        "INSERT INTO movements (item_id, worker_name, action, quantity, timestamp) VALUES (?,?,?,?,?)",
        (item_id, worker_name, action, quantity, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()

    # Generar mensaje de notificación
    verbo = "retiró" if action == "retiro" else "devolvió"
    msg = f"🔧 {worker_name} {verbo} {quantity} {item['unit']} de '{item['name']}'. Quedan: {new_qty} {item['unit']}."
    if action == "retiro" and item["min_stock"] and new_qty <= item["min_stock"]:
        msg += f"\n⚠️ Stock bajo de '{item['name']}' (mínimo: {item['min_stock']})."

    queue_notification(msg)
    return True, msg, new_qty


def queue_notification(message):
    conn = get_conn()
    conn.execute(
        "INSERT INTO pending_notifications (message, timestamp, sent) VALUES (?,?,0)",
        (message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()


def get_unsent_notifications():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM pending_notifications WHERE sent=0 ORDER BY id").fetchall()
    conn.close()
    return rows


def mark_notification_sent(notif_id):
    conn = get_conn()
    conn.execute("UPDATE pending_notifications SET sent=1 WHERE id=?", (notif_id,))
    conn.commit()
    conn.close()


def get_movements(limit=100):
    conn = get_conn()
    rows = conn.execute(
        """SELECT m.*, i.name as item_name, i.unit as unit
           FROM movements m JOIN items i ON m.item_id = i.id
           ORDER BY m.id DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return rows
