import customtkinter as ctk
from tkinter import ttk, messagebox
import threading
import os
import qrcode

import database as db
from notifications import send_whatsapp
from config import SERVER_IP_PARA_QR, SERVER_PORT
from server import run_server

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

QR_DIR = "qrcodes"
os.makedirs(QR_DIR, exist_ok=True)


class TallerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Inventario del Taller")
        self.geometry("1000x650")

        db.init_db()

        self.tabs = ctk.CTkTabview(self, width=980, height=630)
        self.tabs.pack(padx=10, pady=10, fill="both", expand=True)

        self.tab_inv = self.tabs.add("Inventario")
        self.tab_mov = self.tabs.add("Movimientos")
        self.tab_srv = self.tabs.add("Servidor / QR")

        self._build_inventory_tab()
        self._build_movements_tab()
        self._build_server_tab()

        self.server_thread = None
        self.refresh_all()

    # ---------------- INVENTARIO ----------------
    def _build_inventory_tab(self):
        top = ctk.CTkFrame(self.tab_inv)
        top.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(top, text="Nombre").grid(row=0, column=0, padx=4)
        self.in_name = ctk.CTkEntry(top, width=140)
        self.in_name.grid(row=1, column=0, padx=4)

        ctk.CTkLabel(top, text="Categoría").grid(row=0, column=1, padx=4)
        self.in_category = ctk.CTkOptionMenu(top, values=["herramienta", "material"])
        self.in_category.grid(row=1, column=1, padx=4)

        ctk.CTkLabel(top, text="Cantidad").grid(row=0, column=2, padx=4)
        self.in_qty = ctk.CTkEntry(top, width=80)
        self.in_qty.grid(row=1, column=2, padx=4)

        ctk.CTkLabel(top, text="Unidad").grid(row=0, column=3, padx=4)
        self.in_unit = ctk.CTkEntry(top, width=80)
        self.in_unit.grid(row=1, column=3, padx=4)

        ctk.CTkLabel(top, text="Ubicación").grid(row=0, column=4, padx=4)
        self.in_location = ctk.CTkEntry(top, width=120)
        self.in_location.grid(row=1, column=4, padx=4)

        ctk.CTkLabel(top, text="Stock mínimo").grid(row=0, column=5, padx=4)
        self.in_min = ctk.CTkEntry(top, width=80)
        self.in_min.grid(row=1, column=5, padx=4)

        ctk.CTkButton(top, text="Agregar ítem", command=self.add_item).grid(row=1, column=6, padx=10)

        # Tabla
        cols = ("id", "name", "category", "quantity", "unit", "location", "min_stock")
        self.tree = ttk.Treeview(self.tab_inv, columns=cols, show="headings", height=18)
        headers = ["ID", "Nombre", "Categoría", "Cantidad", "Unidad", "Ubicación", "Stock mín."]
        for c, h in zip(cols, headers):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=120)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        bottom = ctk.CTkFrame(self.tab_inv)
        bottom.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkButton(bottom, text="Generar QR del ítem seleccionado", command=self.generate_qr_selected).pack(side="left", padx=5)
        ctk.CTkButton(bottom, text="Eliminar ítem seleccionado", fg_color="#dc2626", hover_color="#991b1b",
                      command=self.delete_selected).pack(side="left", padx=5)
        ctk.CTkButton(bottom, text="Actualizar lista", command=self.refresh_inventory).pack(side="left", padx=5)

    def add_item(self):
        try:
            name = self.in_name.get().strip()
            category = self.in_category.get()
            qty = float(self.in_qty.get())
            unit = self.in_unit.get().strip() or "u."
            location = self.in_location.get().strip()
            min_stock = float(self.in_min.get() or 0)
            if not name:
                raise ValueError("Falta el nombre")
        except ValueError as e:
            messagebox.showerror("Error", f"Revisá los datos ingresados.\n{e}")
            return

        db.add_item(name, category, qty, unit, location, min_stock)
        for entry in (self.in_name, self.in_qty, self.in_unit, self.in_location, self.in_min):
            entry.delete(0, "end")
        self.refresh_inventory()

    def refresh_inventory(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for item in db.get_items():
            self.tree.insert("", "end", values=(
                item["id"], item["name"], item["category"], item["quantity"],
                item["unit"], item["location"] or "-", item["min_stock"]
            ))

    def _get_selected_item_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccioná un ítem de la lista primero.")
            return None
        return self.tree.item(sel[0])["values"][0]

    def delete_selected(self):
        item_id = self._get_selected_item_id()
        if item_id is None:
            return
        if messagebox.askyesno("Confirmar", "¿Eliminar este ítem del inventario?"):
            db.delete_item(item_id)
            self.refresh_inventory()

    def generate_qr_selected(self):
        item_id = self._get_selected_item_id()
        if item_id is None:
            return
        item = db.get_item(item_id)
        url = f"http://{SERVER_IP_PARA_QR}:{SERVER_PORT}/item/{item_id}"
        img = qrcode.make(url)
        safe_name = "".join(c for c in item["name"] if c.isalnum() or c in " _-").strip()
        path = os.path.join(QR_DIR, f"{item_id}_{safe_name}.png")
        img.save(path)
        messagebox.showinfo("QR generado", f"QR guardado en:\n{os.path.abspath(path)}\n\nApunta a:\n{url}")

    # ---------------- MOVIMIENTOS ----------------
    def _build_movements_tab(self):
        cols = ("id", "item_name", "worker_name", "action", "quantity", "timestamp")
        self.tree_mov = ttk.Treeview(self.tab_mov, columns=cols, show="headings", height=25)
        headers = ["ID", "Ítem", "Trabajador", "Acción", "Cantidad", "Fecha/Hora"]
        for c, h in zip(cols, headers):
            self.tree_mov.heading(c, text=h)
            self.tree_mov.column(c, width=140)
        self.tree_mov.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkButton(self.tab_mov, text="Actualizar", command=self.refresh_movements).pack(pady=(0, 10))

    def refresh_movements(self):
        for row in self.tree_mov.get_children():
            self.tree_mov.delete(row)
        for m in db.get_movements():
            self.tree_mov.insert("", "end", values=(
                m["id"], m["item_name"], m["worker_name"], m["action"], m["quantity"], m["timestamp"]
            ))

    # ---------------- SERVIDOR / NOTIFICACIONES ----------------
    def _build_server_tab(self):
        frame = ctk.CTkFrame(self.tab_srv)
        frame.pack(fill="x", padx=20, pady=20)

        self.lbl_status = ctk.CTkLabel(frame, text="Servidor: DETENIDO", font=("Arial", 16, "bold"), text_color="red")
        self.lbl_status.pack(pady=10)

        info_text = (
            f"Los trabajadores deben estar en la MISMA red WiFi que esta computadora.\n"
            f"URL base configurada: http://{SERVER_IP_PARA_QR}:{SERVER_PORT}/item/<id>\n"
            f"(Cambiá SERVER_IP_PARA_QR en config.py por la IP real de esta compu si hace falta)"
        )
        ctk.CTkLabel(frame, text=info_text, justify="left").pack(pady=10)

        ctk.CTkButton(frame, text="Iniciar servidor", command=self.start_server).pack(pady=5)

        ctk.CTkLabel(self.tab_srv, text="Notificaciones pendientes (WhatsApp)", font=("Arial", 14, "bold")).pack(pady=(20, 5))
        self.notif_box = ctk.CTkTextbox(self.tab_srv, width=900, height=250)
        self.notif_box.pack(padx=20, pady=10)

        btns = ctk.CTkFrame(self.tab_srv)
        btns.pack()
        ctk.CTkButton(btns, text="Actualizar notificaciones", command=self.refresh_notifications).pack(side="left", padx=5)
        ctk.CTkButton(btns, text="Reintentar envío a WhatsApp", command=self.retry_whatsapp).pack(side="left", padx=5)

    def start_server(self):
        if self.server_thread and self.server_thread.is_alive():
            messagebox.showinfo("Info", "El servidor ya está corriendo.")
            return
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        self.lbl_status.configure(text="Servidor: ACTIVO", text_color="green")

    def refresh_notifications(self):
        self.notif_box.delete("1.0", "end")
        for n in db.get_unsent_notifications():
            self.notif_box.insert("end", f"[{n['timestamp']}] {n['message']}\n\n")
        if not db.get_unsent_notifications():
            self.notif_box.insert("end", "No hay notificaciones pendientes.")

    def retry_whatsapp(self):
        pending = db.get_unsent_notifications()
        if not pending:
            messagebox.showinfo("Info", "No hay notificaciones pendientes.")
            return
        enviados = 0
        for n in pending:
            ok, msg = send_whatsapp(n["message"])
            if ok:
                db.mark_notification_sent(n["id"])
                enviados += 1
        messagebox.showinfo("Resultado", f"Enviadas: {enviados}/{len(pending)}")
        self.refresh_notifications()

    # ---------------- GENERAL ----------------
    def refresh_all(self):
        self.refresh_inventory()
        self.refresh_movements()
        self.refresh_notifications()


if __name__ == "__main__":
    app = TallerApp()
    app.mainloop()
