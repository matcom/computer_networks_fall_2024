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
        self.root.geometry("700x650")  # Aumentar tamaño para historial
        self.root.grid_columnconfigure(1, weight=1)
        
        # Estilo general
        font_style = ("Arial", 14)
        
        # Historial de solicitudes
        self.history = []
        
        # URL
        ctk.CTkLabel(parent, text="🌐 URL:", font=font_style).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.url_entry = ctk.CTkEntry(parent, width=500, font=font_style)
        self.url_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # Method
        ctk.CTkLabel(parent, text="📡 Method:", font=font_style).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.method_var = ctk.StringVar(value="GET")
        self.method_menu = ctk.CTkOptionMenu(parent, variable=self.method_var, 
                                             values=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "CONNECT", "TRACE", "LINK", "UNLINK", "CUSTOM"],
                                             command=self.toggle_body_state, font=font_style)
        self.method_menu.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # Headers
        ctk.CTkLabel(parent, text="📝 Headers (JSON):", font=font_style).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.headers_entry = ctk.CTkTextbox(parent, width=500, height=60, font=font_style)
        self.headers_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        # Body
        ctk.CTkLabel(parent, text="📦 Body (JSON):", font=font_style).grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.body_text = ctk.CTkTextbox(parent, width=500, height=100, font=font_style)
        self.body_text.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        
        # Send Button
        self.send_button = ctk.CTkButton(parent, text="🚀 Send Request", command=self.send_request, font=font_style)
        self.send_button.grid(row=4, column=1, pady=15)
        
        # Response
        ctk.CTkLabel(parent, text="📩 Response:", font=font_style).grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.response_text = ctk.CTkTextbox(parent, width=500, height=200, font=font_style, state="disabled")
        self.response_text.grid(row=5, column=1, padx=10, pady=5, sticky="ew")
        
        # Historial de solicitudes
        ctk.CTkLabel(parent, text="📜 Request History:", font=font_style).grid(row=6, column=0, padx=10, pady=5, sticky="w")
        self.history_var = ctk.StringVar(value="No history yet")
        self.history_menu = ctk.CTkOptionMenu(parent, variable=self.history_var, values=["No history yet"], font=font_style)
        self.history_menu.grid(row=6, column=1, padx=10, pady=5, sticky="ew")
        self.load_history_button = ctk.CTkButton(parent, text="🔄 Load Request", command=self.load_request, font=font_style)
        self.load_history_button.grid(row=7, column=1, pady=10)
        
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
        headers = self.headers_entry.get("1.0", "end").strip()
        body = json.dumps(self.body_text.get("1.0", "end").strip())

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
        
            # Guardar en historial
            self.history.append((url, method, json.dumps(headers, indent=2), json.dumps(body, indent=2)))
            self.history_menu.configure(values=[f"{i+1}: {h[1]} {h[0]}" for i, h in enumerate(self.history)])
            self.history_var.set(f"{len(self.history)}: {method} {url}")
            
            self.response_text.configure(state="normal")
            self.response_text.delete("1.0", "end")
            self.response_text.insert("end", response_text)
            self.response_text.configure(state="disabled")
        except Exception as e:
            messagebox.showerror("Error", f"Request failed: {e}")
    
    def load_request(self):
        index = int(self.history_var.get().split(":")[0]) - 1
        if 0 <= index < len(self.history):
            url, method, headers, body = self.history[index]
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, url)
            self.method_var.set(method)
            self.headers_entry.delete("1.0", "end")
            self.headers_entry.insert("end", headers)
            self.body_text.delete("1.0", "end")
            self.body_text.insert("end", body)

if __name__ == "__main__":
    root = ctk.CTk()
    app = HttpClientGUI(root)
    root.mainloop()
