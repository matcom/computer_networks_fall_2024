# import customtkinter as ctk
# import json
# from tkinter import messagebox
# import client_cli

# class HttpClientGUI:
#     def __init__(self, parent):
#         ctk.set_appearance_mode("dark") 
#         ctk.set_default_color_theme("blue")
#         self.root = parent
#         self.root.title("HTTP Client")
#         self.root.geometry("600x550")
#         self.root.grid_columnconfigure(1, weight=1)
        
#         # URL
#         ctk.CTkLabel(parent, text="URL:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
#         self.url_entry = ctk.CTkEntry(parent, width=400)
#         self.url_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
#         # Method
#         ctk.CTkLabel(parent, text="Method:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
#         self.method_var = ctk.StringVar(value="GET")
#         self.method_menu = ctk.CTkOptionMenu(parent, variable=self.method_var, values=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "CONNECT", "TRACE", "LINK", "UNLINK", "CUSTOM"], command=self.toggle_body_state)
#         self.method_menu.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
#         # Headers
#         ctk.CTkLabel(parent, text="Headers (JSON):").grid(row=2, column=0, padx=10, pady=5, sticky="w")
#         self.headers_entry = ctk.CTkEntry(parent, width=400)
#         self.headers_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
#         # Body
#         ctk.CTkLabel(parent, text="Body (JSON):").grid(row=3, column=0, padx=10, pady=5, sticky="w")
#         self.body_text = ctk.CTkTextbox(parent, width=400, height=100)
#         self.body_text.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        
#         # Send Button
#         self.send_button = ctk.CTkButton(parent, text="Send", command=self.send_request)
#         self.send_button.grid(row=4, column=1, pady=10)
        
#         # Response
#         ctk.CTkLabel(parent, text="Response:").grid(row=5, column=0, padx=10, pady=5, sticky="w")
#         self.response_text = ctk.CTkTextbox(parent, width=400, height=150, state="disabled")
#         self.response_text.grid(row=5, column=1, padx=10, pady=5, sticky="ew")
        
#         self.toggle_body_state("GET")
        
#     def toggle_body_state(self, method):
#         self.body_text.delete("1.0", "end")
        
#         if method == "GET":
#             self.body_text.configure(state="disabled")
#         else:
#             self.body_text.configure(state="normal")
        
#     def send_request(self):
#         url = self.url_entry.get()
#         method = self.method_var.get()
#         headers = self.headers_entry.get()
#         body = self.body_text.get("1.0", "end").strip()

#         try:
#             headers = json.loads(headers) if headers else {}
#         except json.JSONDecodeError:
#             messagebox.showerror("Error", "Headers must be valid JSON.\nExample:\n{\"Content-Type\": \"application/json\"}")
#             return

#         try:
#             body = json.loads(body) if body else ""
#         except json.JSONDecodeError:
#             messagebox.showerror("Error", "Body must be valid JSON.")
#             return

#         try:
#             response_text = client_cli.run_client(method, url, headers, body)
        
#             # Dividir encabezado y cuerpo
#             header_part, body_part = response_text.split("\n\n", 1) if "\n\n" in response_text else (response_text, "")

#             # Obtener el código de estado HTTP
#             first_line = header_part.split("\n")[0]  # Primera línea "HTTP/1.1 200 OK"
#             status_code = int(first_line.split(" ")[1])  # Extraer código (ej: 200)

#             # Configurar colores según código de estado
#             self.response_text.configure(state="normal")
#             self.response_text.delete("1.0", "end")

#             # Colorear encabezados (azul)
#             self.response_text.insert("end", header_part + "\n\n", "header")

#             # Si el cuerpo es JSON, lo formateamos bonito
#             try:
#                 body_json = json.loads(body_part)
#                 formatted_body = json.dumps(body_json, indent=2)
#             except json.JSONDecodeError:
#                 formatted_body = body_part  # Si no es JSON, mostrarlo tal cual

#             # Insertar el cuerpo con color blanco
#             self.response_text.insert("end", formatted_body, "body")

#             # Aplicar colores
#             self.response_text.tag_config("header", foreground="blue")
#             self.response_text.tag_config("body", foreground="white")

#             # Código de estado en color según resultado
#             if 200 <= status_code < 300:
#                 self.response_text.tag_config("status", foreground="green")  # Éxito
#             elif 400 <= status_code < 600:
#                 self.response_text.tag_config("status", foreground="red")  # Error

#             self.response_text.configure(state="disabled")
#         except Exception as e:
#             messagebox.showerror("Error", f"Request failed: {e}")


# if __name__ == "__main__":
#     root = ctk.CTk()
#     app = HttpClientGUI(root)
#     root.mainloop()

import customtkinter as ctk
import json
from tkinter import messagebox
import client_cli

class HttpClientGUI:
    def __init__(self, parent):
        ctk.set_appearance_mode("dark") 
        ctk.set_default_color_theme("blue")
        self.root = parent
        self.root.title("HTTP Client")
        self.root.geometry("600x550")
        self.root.grid_columnconfigure(1, weight=1)
        
        # URL
        ctk.CTkLabel(parent, text="URL:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.url_entry = ctk.CTkEntry(parent, width=400)
        self.url_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # Method
        ctk.CTkLabel(parent, text="Method:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.method_var = ctk.StringVar(value="GET")
        self.method_menu = ctk.CTkOptionMenu(parent, variable=self.method_var, values=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "CONNECT", "TRACE", "LINK", "UNLINK", "CUSTOM"], command=self.toggle_body_state)
        self.method_menu.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # Headers
        ctk.CTkLabel(parent, text="Headers (JSON):").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.headers_entry = ctk.CTkEntry(parent, width=400)
        self.headers_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        # Body
        ctk.CTkLabel(parent, text="Body (JSON):").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.body_text = ctk.CTkTextbox(parent, width=400, height=100)
        self.body_text.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        
        # Send Button
        self.send_button = ctk.CTkButton(parent, text="Send", command=self.send_request)
        self.send_button.grid(row=4, column=1, pady=10)
        
        # Response
        ctk.CTkLabel(parent, text="Response:").grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.response_text = ctk.CTkTextbox(parent, width=400, height=150, state="disabled")
        self.response_text.grid(row=5, column=1, padx=10, pady=5, sticky="ew")
        
        self.toggle_body_state("GET")
        
    def toggle_body_state(self, method):
        self.body_text.delete("1.0", "end")
        
        if method == "GET":
            self.body_text.configure(state="disabled")
        else:
            self.body_text.configure(state="normal")
        
    def send_request(self):
        url = self.url_entry.get()
        method = self.method_var.get()
        headers = self.headers_entry.get()
        body = self.body_text.get("1.0", "end").strip()

        try:
            headers = json.loads(headers) if headers else {}
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Headers must be valid JSON.\nExample:\n{\"Content-Type\": \"application/json\"}")
            return

        try:
            body = json.loads(body) if body else ""
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Body must be valid JSON.")
            return

        try:
            response_text = client_cli.run_client(method, url, headers, body)
        
            # Dividir encabezado y cuerpo
            header_part, body_part = response_text.split("\n\n", 1) if "\n\n" in response_text else (response_text, "")

            self.response_text.configure(state="normal")
            self.response_text.delete("1.0", "end")

            # Insertar encabezados tal cual
            self.response_text.insert("end", header_part + "\n\n")

            # Si el cuerpo es JSON, formatearlo bonito
            try:
                body_json = json.loads(body_part)
                formatted_body = json.dumps(body_json, indent=2)
            except json.JSONDecodeError:
                formatted_body = body_part  # Si no es JSON, mostrarlo tal cual

            # Insertar el cuerpo formateado
            self.response_text.insert("end", formatted_body)
            
            self.response_text.configure(state="disabled")
        except Exception as e:
            messagebox.showerror("Error", f"Request failed: {e}")

if __name__ == "__main__":
    root = ctk.CTk()
    app = HttpClientGUI(root)
    root.mainloop()
