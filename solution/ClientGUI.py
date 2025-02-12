import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from Client import IRCClient

class ClientGUI:
    def __init__(self):
        self.host = "localhost"
        self.port = 6667
        self.nick = ""
        self.client = None
        self.channels = []
        self.current_channel = None
        self.users = []
        self.current_user = None

        # Crear ventana principal
        self.root = tk.Tk()
        self.root.title("Cliente IRC")
        self.root.geometry("800x650")
        self.root.resizable(True, True)

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
        
        # Menú desplegable para conexión
        self.connection_var = tk.StringVar(value="Conectar")
        self.connection_menu = ttk.OptionMenu(
            self.connection_frame, 
            self.connection_var, 
            "Conectar", 
            "Conectar", 
            "Desconectar", 
            "Cambiar Nick", 
            command=self.handle_connection_option
        )
        self.connection_menu.grid(row=0, column=6, padx=5)
        
        # Parte principal
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Canales
        self.channels_frame = ttk.LabelFrame(self.main_frame, text="Todos los Canales")
        self.channels_frame.pack(side="left", fill="y", padx=5)
        
        self.channels_listbox = tk.Listbox(self.channels_frame, width=20)
        self.channels_listbox.pack(fill="y", expand=True)
        self.channels_listbox.bind('<<ListboxSelect>>', self.on_channel_select)
        
        self.update_channels_list()
        
        # Usuarios
        self.users_frame = ttk.LabelFrame(self.main_frame, text="Usuarios")
        self.users_frame.pack(side="right", fill="y", padx=5, pady=(0, 5))

        # Crear un frame para dividir el espacio
        self.users_paned_window = ttk.PanedWindow(self.users_frame, orient=tk.VERTICAL)
        self.users_paned_window.pack(fill="both", expand=True)

        # Parte superior: lista de usuarios
        self.users_list_frame = ttk.Frame(self.users_paned_window)
        self.users_paned_window.add(self.users_list_frame, weight=1)

        self.users_listbox = tk.Listbox(self.users_list_frame, width=20)
        self.users_listbox.pack(fill="both", expand=True)
        self.users_listbox.bind('<<ListboxSelect>>', self.on_user_select)

        self.reload_users_button = ttk.Button(self.users_list_frame, text="Recargar", command=self.reload_users)
        self.reload_users_button.pack(pady=5)

        # Parte inferior: lista de comandos
        self.commands_frame = ttk.Frame(self.users_paned_window)
        self.users_paned_window.add(self.commands_frame, weight=1)

        self.commands_listbox = tk.Listbox(self.commands_frame, width=20)
        self.commands_listbox.pack(fill="both", expand=True)
        self.commands_listbox.bind('<<ListboxSelect>>', self.on_command_select)

        self.populate_commands_list()
        
        # Chat
        self.chat_frame = ttk.Frame(self.main_frame)
        self.chat_frame.pack(fill="both", expand=True, padx=5)
        
        self.chat_area = scrolledtext.ScrolledText(self.chat_frame)
        self.chat_area.pack(fill="both", expand=True)
        
        # Configurar el área de chat para usar colores
        self.chat_area.tag_configure("command", foreground="blue")
        self.chat_area.tag_configure("error", foreground="red")
        self.chat_area.tag_configure("green", foreground="green")
        # nput
        self.input_frame = ttk.Frame(self.root)
        self.input_frame.pack(fill="x", padx=5, pady=5)
        
        self.message_entry = ttk.Entry(self.input_frame)
        self.message_entry.pack(side="left", fill="x", expand=True)
        self.message_entry.bind("<Return>", self.send_message)
        
        self.send_button = ttk.Button(self.input_frame, text="Enviar", command=self.send_message)
        self.send_button.pack(side="right", padx=5)

        # Botón para mostrar la guía de usuario
        self.guide_button = ttk.Button(self.root, text="Guía de Usuario", command=self.show_user_guide)
        self.guide_button.pack(side="bottom", pady=5)

    def handle_connection_option(self, option):
        """Manejar la opción seleccionada en el menú de conexión"""
        if option == "Conectar":
            self.connect()
        elif option == "Desconectar":
            self.disconnect()
        elif option == "Cambiar Nick":
            self.change_nick()

    def connect(self):
        """Conectar al servidor IRC"""
        try:
            self.host = self.host_entry.get()
            self.port = int(self.port_entry.get())
            nick = self.nick_entry.get()
            
            if not nick:
                messagebox.showerror("Error", "Debes especificar un nickname")
                return

            self.client = IRCClient(self.host, self.port, nick, True)
            self.client.connect()
            self.client.handle_message_callback = self.handle_message
            self.client.start_receiving()
            
            # Deshabilitar campos de conexión
            self.host_entry.config(state="disabled")
            self.port_entry.config(state="disabled")
            self.connection_var.set("Desconectar")
            self.reload_channels()
            self.root.after(1000, self.add_chat_message, "Te has unido al canal #General.")

            messagebox.showinfo("Conexión", "Conectado exitosamente al servidor")
        except Exception as e:
            messagebox.showerror("Error", f"Error al conectar: {str(e)}")

    def disconnect(self):
        """Desconectar del servidor IRC"""
        if self.client and self.client.connected:
            try:
                self.client.quit_server()
                self.client.connected= False
                self.client.sock.close()
                self.connection_var.set("Conectar")
                self.host_entry.config(state="normal")
                self.port_entry.config(state="normal")
                self.nick_entry.config(state="normal")
                # Limpiar listas y chat
                self.channels = []
                self.users = []
                self.current_channel = None
                self.current_user = None
                self.update_channels_list()
                self.update_users_list("")
                self.chat_area.delete(1.0, tk.END)
                messagebox.showinfo("Desconexión", "Desconectado exitosamente del servidor")
            except Exception as e:
                messagebox.showerror("Error", f"Error al desconectar: {str(e)}")

    def change_nick(self):
        """Cambiar el nick del usuario"""
        if self.client and self.client.connected:
            new_nick = self.nick_entry.get()
            if new_nick:
                self.client.send_command(f"NICK {new_nick}")
            else:
                messagebox.showerror("Error", "Debes especificar un nuevo nickname")

    def add_chat_message(self, message, color="gray"):
        """Añade un mensaje al área de chat y hace scroll hasta el final"""
        self.chat_area.insert(tk.END, f"{message}\n", color)
        self.chat_area.see(tk.END)

    def send_message(self, event=None):
        """Enviar mensaje al canal actual"""
            
        message = self.message_entry.get()
        if message:
            if message.startswith("/quit"):
                self.disconnect()
                return
            # if message.startswith("/part #General "):
            #     messagebox.showerror("Error", "No puedes abandonar el canal #General")
            #     return
            if message.startswith('/'):
                # Comandos
                self.add_chat_message(f"Command:{message}", "command")
                self.client.handle_command(message.split()[0], ' '.join(message.split()[1:]))
            else:
                if not self.client or not self.current_channel:
                    messagebox.showwarning("Advertencia", "Debes estar conectado y en un canal para enviar mensajes")
                    return
                # Mensaje normal al canal o a usuario
                self.client.handle_command("/privmsg" ,f"{self.current_channel} {message}")
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

    def on_user_select(self, event):
        """Manejar selección de usuario"""
        selection = self.users_listbox.curselection()
        if selection:
            self.current_channel = self.users[selection[0]]

    def update_channels_list(self):
        """Actualizar lista de canales en la GUI"""
        # Limpiar la lista de canales antes de actualizar
        self.channels_listbox.delete(0, tk.END)

        for channel in self.channels:
            self.channels_listbox.insert(tk.END, channel)

        # Crear un frame para los botones
        if not hasattr(self, 'buttons_frame'):
            self.buttons_frame = ttk.Frame(self.channels_frame)
            self.buttons_frame.pack(pady=5)

        # Botón para recargar canales
        if not hasattr(self, 'reload_channels_button'):
            self.reload_channels_button = ttk.Button(self.buttons_frame, text="Recargar", command=self.reload_channels)
            self.reload_channels_button.pack(side="left", padx=5)

        # Botón para unirse al canal seleccionado
        if not hasattr(self, 'join_button'):
            self.join_button = ttk.Button(self.buttons_frame, text="Unirme", command=self.join_selected_channel)
            self.join_button.pack(side="left", padx=5)

    def join_selected_channel(self):
        """Unirse al canal seleccionado en la lista"""
        selection = self.channels_listbox.curselection()
        if selection:
            channel_name = self.channels[selection[0]]
            self.join_channel(channel_name)

    def join_channel(self, channel_name):
        """Unirse a un canal específico"""
        if self.client:
            self.client.send_command(f"JOIN {channel_name}")

    def update_users_list(self, names_message):
        """Actualizar lista de usuarios en la GUI"""
        self.users = [nick.strip() for nick in names_message.split(':')[-1].split(" ")]
        self.users_listbox.delete(0, tk.END)
        for user in self.users:
            self.users_listbox.insert(tk.END, user)

    def reload_channels(self):
        """Recargar la lista de canales"""
        if self.client:
            # self.add_chat_message("Command: /list", "command")
            self.client.send_command("LIST")

    def reload_users(self):
        """Recargar la lista de usuarios del canal actual"""
        if self.client and self.current_channel:
            self.client.send_command(f"NAMES {self.current_channel}")

    def show_user_guide(self):
        """Mostrar una ventana con la guía de usuario"""
        guide_window = tk.Toplevel(self.root)
        guide_window.title("Guía de Usuario")
        guide_window.geometry("500x400")

        guide_text = (
            "Comandos disponibles:\n"
            "/list - Listar canales\n"
            "/names <canal> - Listar usuarios en un canal\n"
            "/whois <usuario> - Obtener información de un usuario\n"
            "/topic <canal> [nuevo_topic] - Ver o cambiar el topic de un canal\n"
            "/mode <canal> [+|-]o <usuario> - Agregar/quitar operador a un usuario\n"
            "/mode <canal> [+|-]t - El topic solo puede ser cambiado por los operadores\n"
            "/mode <canal> [+|-]m - El canal es moderado\n"
            "/mode <user> [+|-]i - El usuario es invisible\n"
            "/join <canal> - Unirse a un canal\n"
            "/part <canal> - Salir de un canal\n"
            "/privmsg <usuario> <mensaje> - Enviar un mensaje privado\n"
            "/nick <nuevo_nick> - Cambiar tu apodo\n"
            "/quit - Desconectarse del servidor\n"
            "/kick <canal> <usuario> - Expulsar a un usuario de un canal\n"
            "/notice <canal> <mensaje> - Enviar un mensaje de aviso a un canal\n"
            # Añade más comandos según sea necesario
        )

        guide_label = tk.Label(guide_window, text=guide_text, justify="left")
        guide_label.pack(padx=10, pady=10, fill="both", expand=True)

    def handle_message(self, message):
        """Maneja el mensaje recibido del servidor y procesa los comandos."""
        print(f"Mensaje recibido: {message}")
        try:
            if not message:
                return
            if message.startswith("Mensaje enviado"):
                return
            parts = message.split(' ', 1)
            first_part = parts[0]
            content = parts[1] if len(parts) > 1 else ""
            
            # Manejar códigos numéricos
            if self._handle_numeric_message(first_part, content):
                return
            
            # Manejar PING
            if self._handle_ping(first_part, content):
                return
            
            # Manejar mensajes que comienzan con ':'
            if message.startswith(':'):
                try:
                    source, cmd, *params = message[1:].split(' ')
                    self._handle_user_commands(source, cmd, params)
                except Exception as e:
                    self.add_chat_message(f"Error al procesar mensaje con prefijo: {e}" , "error")
                    self.add_chat_message(f"Mensaje original: {message}" , "error")
            else:
                if message.startswith("Te has unido al canal"):
                    channel_name = '#' + message.split("#")[-1].strip().replace(".", "")  
                    if channel_name not in self.channels:
                        self.channels.append(channel_name)
                        self.update_channels_list()
                elif message.startswith("Lista de Canales:"):
                    self.channels = []
                    self.channels = [channel.strip() for channel in message.split(": ")[1].split(" ")]
                    self.update_channels_list()

                self.add_chat_message(message)
            
        except Exception as e:
            self.add_chat_message(f"Error al procesar mensaje: {e}" , "error")

    def _handle_numeric_message(self, first_part, content):
        """Maneja mensajes con códigos numéricos"""
        if first_part.startswith(':') and first_part[1:].isdigit():
            code = str(first_part[1:])
            self.handle_numeric_response(code, content)
            return True
        return False

    def _handle_ping(self, first_part, content):
        """Maneja mensajes PING"""
        return first_part == "PING"

    def _handle_user_commands(self, source, cmd, params):
        """Maneja comandos relacionados con usuarios."""
        nick = source.split('!')[0] if '!' in source else source
        
        if cmd == "PRIVMSG":
            self._handle_privmsg(nick, params)
        elif cmd == "JOIN":
            self.add_chat_message(f"{nick} se ha unido al canal {params[0]}")
        elif cmd == "PART":
            self.add_chat_message(f"{nick} ha abandonado el canal {params[0]}")
        elif cmd == "QUIT":
            reason = ' '.join(params)[1:] if params else "No reason given"
            self.add_chat_message(f"{nick} se ha desconectado: {reason}")
        elif cmd == "NICK":
            self.nick = params[0]
            self.nick_entry.delete(0, tk.END)
            self.nick_entry.insert(0, self.nick)
            self.add_chat_message(f"{nick} ahora se conoce como {params[0]}")
        elif cmd == "TOPIC":
            channel = params[0]
            topic = ' '.join(params[1:])[1:]
            self.add_chat_message(f"El tema del canal {channel} ha cambiado a: {topic}")
        elif cmd == "NOTICE":
            target = params[0]
            notice_content = ' '.join(params[1:])[1:]
            self.add_chat_message(f"[NOTICE] {nick} a {target}: {notice_content}")
        elif cmd == "KICK":
            channel = params[0]
            kicked_user = params[1]
            reason = ' '.join(params[2:])[1:] if len(params) > 2 else "Sin razón especificada"
            self.add_chat_message(f"{kicked_user} ha sido expulsado del canal {channel} por {nick}: {reason}")

    def _handle_privmsg(self, nick, params):
        """Maneja mensajes privados"""
        target = params[0]
        msg_content = ' '.join(params[1:])[1:]
        if target.startswith('#'):
            self.add_chat_message(f"[{target}] {nick}: {msg_content}")
        else:
            self.add_chat_message(f"Mensaje privado de {nick}: {msg_content}")

    def handle_numeric_response(self, code, content):
        """Procesa los códigos numéricos del servidor IRC."""
        responses = {
            '001': "Bienvenido al servidor IRC",
            '312': f"Información del usuario: {content}",
            '331': "No hay topic establecido",
            '332': f"Topic del canal {content}",
            '353': f"Lista de usuarios: {content}",
            '366': "Fin de la lista de usuarios",
            '401': "Usuario/Canal no encontrado",
            '403': "Canal no encontrado",
            '404': "No puedes enviar mensajes a este canal",
            '421': "Comando desconocido",
            '431': "No se ha especificado nickname",
            '432': "Nickname inválido",
            '433': "Nickname ya está en uso",
            '441': "Usuario no está en el canal",
            '442': "No estás en ese canal",
            '461': "Faltan parámetros",
            '472': "Modo desconocido",
            '482': "No eres operador del canal",
            '502': "Un usuario solo puede cambiar sus propios modos"
            
        }
        
        if code in responses:
            if int(code) < 400   :
                if code == "353":
                    self.update_users_list(content)
                self.add_chat_message(f"[{code}] {responses[code]}")
            else:
                self.add_chat_message(f"Error {code}: {content}","error")
        else:
            self.add_chat_message(f"Error: {code}: {content}","error")

    def populate_commands_list(self):
        """Rellenar la lista de comandos disponibles"""
        commands = [
            "/list",
            "/names <canal>",
            "/whois <usuario>",
            "/topic <canal> [nuevo_topic]",
            "/mode <canal> [+|-]o <usuario>",
            "/mode <canal> [+|-]t",
            "/mode <canal> [+|-]m",
            "/mode <user> [+|-]i",
            "/join <canal>",
            "/part <canal>",
            "/privmsg <usuario> <mensaje>",
            "/nick <nuevo_nick>",
            "/quit",
            "/kick <canal> <usuario>",
            "/notice <canal> <mensaje>"
        ]
        for command in commands:
            self.commands_listbox.insert(tk.END, command)

    def on_command_select(self, event):
        """Manejar selección de comando y escribirlo en la barra de entrada"""
        selection = self.commands_listbox.curselection()
        if selection:
            command = self.commands_listbox.get(selection[0])
            self.message_entry.delete(0, tk.END)
            self.message_entry.insert(0, command)

    def run(self):
        """Iniciar la GUI"""
        self.root.mainloop()


if __name__ == "__main__":
    gui = ClientGUI()
    gui.run()