import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from Client import IRCClient
from threading import Thread

class ClientGUI:
    def __init__(self):
        self.host = "localhost"
        self.port = 6667
        self.client = None
        self.channels = []
        self.current_channel = None
        self.users = []
        
        # Crear ventana principal
        self.root = tk.Tk()
        self.root.title("Cliente IRC")
        self.root.geometry("800x600")
        
        # Frame para conexión
        self.connection_frame = ttk.LabelFrame(self.root, text="Conexión")
        self.connection_frame.pack(fill="x", padx=5, pady=5)
        
        # Campos de conexión
        ttk.Label(self.connection_frame, text="Host:").grid(row=0, column=0, padx=5)
        self.host_entry = ttk.Entry(self.connection_frame)
        self.host_entry.insert(0, self.host)
        self.host_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(self.connection_frame, text="Puerto:").grid(row=0, column=2, padx=5)
        self.port_entry = ttk.Entry(self.connection_frame)
        self.port_entry.insert(0, str(self.port))
        self.port_entry.grid(row=0, column=3, padx=5)
        
        ttk.Label(self.connection_frame, text="Nick:").grid(row=0, column=4, padx=5)
        self.nick_entry = ttk.Entry(self.connection_frame)
        self.nick_entry.grid(row=0, column=5, padx=5)
        
        self.connect_button = ttk.Button(self.connection_frame, text="Conectar", command=self.connect)
        self.connect_button.grid(row=0, column=6, padx=5)
        
        # Parte principal
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Canales
        self.channels_frame = ttk.LabelFrame(self.main_frame, text="Canales")
        self.channels_frame.pack(side="left", fill="y", padx=5)
        
        self.channels_listbox = tk.Listbox(self.channels_frame, width=20)
        self.channels_listbox.pack(fill="y", expand=True)
        self.channels_listbox.bind('<<ListboxSelect>>', self.on_channel_select)
        
        self.reload_channels_button = ttk.Button(self.channels_frame, text="Recargar", command=self.reload_channels)
        self.reload_channels_button.pack(pady=5)
        
        # Usuarios
        self.users_frame = ttk.LabelFrame(self.main_frame, text="Usuarios")
        self.users_frame.pack(side="right", fill="y", padx=5)
        
        self.users_listbox = tk.Listbox(self.users_frame, width=20)
        self.users_listbox.pack(fill="y", expand=True)
        
        self.reload_users_button = ttk.Button(self.users_frame, text="Recargar", command=self.reload_users)
        self.reload_users_button.pack(pady=5)
        
        # Chat
        self.chat_frame = ttk.Frame(self.main_frame)
        self.chat_frame.pack(fill="both", expand=True, padx=5)
        
        self.chat_area = scrolledtext.ScrolledText(self.chat_frame)
        self.chat_area.pack(fill="both", expand=True)
        
        # nput
        self.input_frame = ttk.Frame(self.root)
        self.input_frame.pack(fill="x", padx=5, pady=5)
        
        self.message_entry = ttk.Entry(self.input_frame)
        self.message_entry.pack(side="left", fill="x", expand=True)
        self.message_entry.bind("<Return>", self.send_message)
        
        self.send_button = ttk.Button(self.input_frame, text="Enviar", command=self.send_message)
        self.send_button.pack(side="right", padx=5)

    def connect(self):
        """Conectar o desconectar del servidor IRC"""
        if self.client and self.client.connected:
            # Desconectar
            try:
                self.client.quit_server()
                self.connect_button.config(text="Conectar")
                self.host_entry.config(state="normal")
                self.port_entry.config(state="normal")
                self.nick_entry.config(state="normal")
                # Limpiar listas y chat
                self.channels = []
                self.users = []
                self.current_channel = None
                self.update_channels_list()
                self.update_users_list("")
                self.chat_area.delete(1.0, tk.END)
                messagebox.showinfo("Desconexión", "Desconectado exitosamente del servidor")
            except Exception as e:
                messagebox.showerror("Error", f"Error al desconectar: {str(e)}")
        else:
            # Conectar
            try:
                self.host = self.host_entry.get()
                self.port = int(self.port_entry.get())
                nick = self.nick_entry.get()
                
                if not nick:
                    messagebox.showerror("Error", "Debes especificar un nickname")
                    return

                self.client = IRCClient(self.host, self.port, nick)
                self.client.connect()
                self.client.handle_message_callback = self.handle_server_message
                self.client.start_receiving()
                
                # Deshabilitar campos de conexión
                self.host_entry.config(state="disabled")
                self.port_entry.config(state="disabled")
                self.nick_entry.config(state="disabled")
                self.connect_button.config(text="Desconectar")
                
                messagebox.showinfo("Conexión", "Conectado exitosamente al servidor")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al conectar: {str(e)}")

    def handle_server_message(self, message):
        """Manejar mensajes recibidos del servidor"""
        try:
            # Mostrar el mensaje en el área de chat
            self.add_chat_message(message)
            
            # Si es un PING, responder automáticamente
            if message.startswith("PING"):
                self.client.send_command(f"PONG {message[5:]}")

            if message.startswith(':312'):
                self.add_chat_message(f"Información del usuario: {message.split(" ",1)[1]}")
            if 'ahora se conoce como' in message:
                self.add_chat_message(message)
            if 'Saliste' in message:
                self.add_chat_message(message)    

            if 'Lista de Canales:' in message:
                channels = message.split(": ")[1]
                self.channels = [channel.strip() for channel in channels.split(" ")]
                self.update_channels_list()
            # Procesar mensajes específicos
            if ":353" in message:
                self.update_users_list(message)
            if message.startswith(':'):
                prefix, command, *params = message[1:].split(' ')
                if command == "PRIVMSG":
                    target = params[0]
                    msg_content = ' '.join(params[1:])[1:]  # Eliminar el ':' inicial
                    if target.startswith('#'):
                        self.add_chat_message(f"[{target}] {prefix.split('!')[0]}: {msg_content}")
                    else:
                        self.add_chat_message(f"Mensaje privado de {prefix.split('!')[0]}: {msg_content}")
                elif command == "JOIN":
                    channel = params[0]
                    self.add_chat_message(f"{prefix.split('!')[0]} se ha unido al canal {channel}")
                    if channel not in self.channels:
                        self.channels.append(channel)
                        self.update_channels_list()
                elif command == "PART":
                    channel = params[0]
                    self.add_chat_message(f"{prefix.split('!')[0]} ha abandonado el canal {channel}")
                elif command == "QUIT":
                    self.add_chat_message(f"{prefix.split('!')[0]} se ha desconectado")
                elif command == "NICK":
                    new_nick = params[0]
                    self.add_chat_message(f"{prefix.split('!')[0]} ahora se conoce como {new_nick}")
                elif command == "NOTICE":
                    notice_content = ' '.join(params[1:])[1:]
                    self.add_chat_message(f"NOTICE de {prefix.split('!')[0]}: {notice_content}")
                # Puedes añadir más comandos según sea necesario

            # Detectar mensaje de unión al canal
            if "Te has unido al canal" in message:
                channel_name = message.split("#")[-1].strip()
                if channel_name not in self.channels:
                    self.channels.append(f"#{channel_name}".replace(".", ""))
                    self.update_channels_list()

        except Exception as e:
            self.add_chat_message(f"Error al procesar mensaje: {e}")

    def add_chat_message(self, message):
        """Añade un mensaje al área de chat y hace scroll hasta el final"""
        self.chat_area.insert(tk.END, f"{message}\n")
        self.chat_area.see(tk.END)

    def send_message(self, event=None):
        """Enviar mensaje al canal actual"""
        if not self.client or not self.current_channel:
            messagebox.showwarning("Advertencia", "Debes estar conectado y en un canal")
            return
            
        message = self.message_entry.get()
        if message:
            if message.startswith('/'):
                # Comandos
                self.client.handle_command(message.split()[0], ' '.join(message.split()[1:]))
            else:
                # Mensaje normal al canal
                self.client.send_command(f"PRIVMSG {self.current_channel} :{message}")
            self.message_entry.delete(0, tk.END)

    def on_channel_select(self, event):
        """
        Manejar selección de canal:
        - Actualiza el canal actual
        - Recarga la lista de usuarios del canal actual
        """
        selection = self.channels_listbox.curselection()
        if selection:
            self.current_channel = self.channels[selection[0]]
            self.reload_users()

    def update_channels_list(self):
        """Actualizar lista de canales en la GUI"""
        self.channels_listbox.delete(0, tk.END)
        for channel in self.channels:
            self.channels_listbox.insert(tk.END, channel)

    def update_users_list(self, names_message):
        """Actualizar lista de usuarios en la GUI"""
        self.users = [nick.strip() for nick in names_message.split(':')[-1].split(" ")]
        self.users_listbox.delete(0, tk.END)
        for user in self.users:
            self.users_listbox.insert(tk.END, user)

    def reload_channels(self):
        """Recargar la lista de canales"""
        if self.client:
            self.client.send_command("LIST")

    def reload_users(self):
        """Recargar la lista de usuarios del canal actual"""
        if self.client and self.current_channel:
            self.client.send_command(f"NAMES {self.current_channel}")

    def run(self):
        """Iniciar la GUI"""
        self.root.mainloop()


if __name__ == "__main__":
    gui = ClientGUI()
    gui.run()