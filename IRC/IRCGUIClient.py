import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
from datetime import datetime
from IRCClientLibrary import EnhancedIRCClient
from typing import Dict, Optional

class IRCGui:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Python IRC Client")
        self.root.geometry("1000x700")
        
        # IRC Client instance
        self.client: Optional[EnhancedIRCClient] = None
        self.current_channel: Optional[str] = None
        self.channels: Dict[str, scrolledtext.ScrolledText] = {}
        self.private_chats: Dict[str, scrolledtext.ScrolledText] = {}
        
        self._setup_gui()
        self._create_menu()
        self._setup_status_bar()
        
    def _setup_gui(self):
        """Set up the main GUI layout"""
        # Create main container with weights
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        # Channel list frame (left side)
        channel_frame = ttk.LabelFrame(self.root, text="Channels & Users")
        channel_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Channel treeview
        self.channel_tree = ttk.Treeview(channel_frame, show='tree')
        self.channel_tree.pack(fill=tk.BOTH, expand=True)
        self.channel_tree.bind('<<TreeviewSelect>>', self._on_channel_select)
        
        # Main chat area (right side)
        chat_frame = ttk.Frame(self.root)
        chat_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        chat_frame.grid_rowconfigure(0, weight=1)
        chat_frame.grid_columnconfigure(0, weight=1)
        
        # Notebook for chat tabs
        self.chat_notebook = ttk.Notebook(chat_frame)
        self.chat_notebook.grid(row=0, column=0, sticky="nsew")
        
        # Server tab
        self.server_tab = scrolledtext.ScrolledText(self.chat_notebook, wrap=tk.WORD)
        self.chat_notebook.add(self.server_tab, text="Server")
        
        # Message input frame
        input_frame = ttk.Frame(chat_frame)
        input_frame.grid(row=1, column=0, sticky="ew", pady=5)
        input_frame.grid_columnconfigure(0, weight=1)
        
        self.message_input = ttk.Entry(input_frame)
        self.message_input.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.message_input.bind('<Return>', self._send_message)
        
        send_button = ttk.Button(input_frame, text="Send", command=self._send_message)
        send_button.grid(row=0, column=1)
        
        # User list frame (right side)
        user_frame = ttk.LabelFrame(self.root, text="Users")
        user_frame.grid(row=1, column=2, sticky="nsew", padx=5, pady=5)
        
        self.user_list = ttk.Treeview(user_frame, show='tree', columns=('mode',))
        self.user_list.pack(fill=tk.BOTH, expand=True)
        
    def _create_menu(self):
        """Create the application menu"""
        menubar = tk.Menu(self.root)
        
        # Connection menu
        connection_menu = tk.Menu(menubar, tearoff=0)
        connection_menu.add_command(label="Connect", command=self._show_connect_dialog)
        connection_menu.add_command(label="Disconnect", command=self._disconnect)
        menubar.add_cascade(label="Connection", menu=connection_menu)
        
        # Channel menu
        channel_menu = tk.Menu(menubar, tearoff=0)
        channel_menu.add_command(label="Join Channel", command=self._show_join_dialog)
        channel_menu.add_command(label="Leave Channel", command=self._leave_current_channel)
        menubar.add_cascade(label="Channel", menu=channel_menu)
        
        self.root.config(menu=menubar)
        
    def _setup_status_bar(self):
        """Create status bar"""
        self.status_var = tk.StringVar()
        self.status_var.set("Not connected")
        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=2)
        
    def _show_connect_dialog(self):
        """Show connection dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Connect to Server")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        
        # Server details
        ttk.Label(dialog, text="Server:").pack(pady=5)
        server_entry = ttk.Entry(dialog)
        server_entry.insert(0, "localhost")
        server_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Port:").pack(pady=5)
        port_entry = ttk.Entry(dialog)
        port_entry.insert(0, "6667")
        port_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Nickname:").pack(pady=5)
        nick_entry = ttk.Entry(dialog)
        nick_entry.pack(pady=5)
        
        def connect():
            server = server_entry.get()
            port = int(port_entry.get())
            nickname = nick_entry.get()
            
            if server and port and nickname:
                self._connect_to_server(server, port, nickname)
                dialog.destroy()
        
        ttk.Button(dialog, text="Connect", command=connect).pack(pady=10)
        
    def _connect_to_server(self, server: str, port: int, nickname: str):
        """Connect to IRC server"""
        self.client = EnhancedIRCClient(server, port)
        
        # Set up event handlers
        self.client.on('message', self._handle_message)
        self.client.on('join', self._handle_join)
        self.client.on('part', self._handle_part)
        self.client.on('nick', self._handle_nick)
        self.client.on('error', self._handle_error)
        self.client.on('connect', self._handle_connect)
        self.client.on('disconnect', self._handle_disconnect)
        
        if self.client.connect(nickname):
            self.status_var.set(f"Connected to {server}:{port} as {nickname}")
            self._add_server_message(f"Connected to {server}:{port} as {nickname}")
        else:
            messagebox.showerror("Connection Error", "Failed to connect to server")
            
    def _disconnect(self):
        """Disconnect from server"""
        if self.client:
            self.client.disconnect()
            self.client = None
            self.status_var.set("Disconnected")
            self._add_server_message("Disconnected from server")
            
    def _show_join_dialog(self):
        """Show join channel dialog"""
        if not self.client:
            messagebox.showerror("Error", "Not connected to server")
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Join Channel")
        dialog.geometry("250x120")
        dialog.transient(self.root)
        
        ttk.Label(dialog, text="Channel:").pack(pady=5)
        channel_entry = ttk.Entry(dialog)
        channel_entry.pack(pady=5)
        
        def join():
            channel = channel_entry.get()
            if channel:
                self.client.join_channel(channel)
                dialog.destroy()
        
        ttk.Button(dialog, text="Join", command=join).pack(pady=10)
        
    def _leave_current_channel(self):
        """Leave the current channel"""
        if self.current_channel and self.client:
            self.client.leave_channel(self.current_channel)
            
    def _send_message(self, event=None):
        """Send message to current channel or user"""
        if not self.client:
            return
            
        message = self.message_input.get().strip()
        if not message:
            return
            
        if self.current_channel:
            if self.current_channel.startswith('#'):
                self.client.send_channel_message(self.current_channel, message)
            else:
                self.client.send_private_message(self.current_channel, message)
                self._add_chat_message(self.current_channel, "You", message)
                
        self.message_input.delete(0, tk.END)
        
    def _handle_message(self, data):
        """Handle incoming messages"""
        source = data['from']
        target = data['to']
        message = data['message']
        
        if target.startswith('#'):
            # Channel message
            self._add_chat_message(target, source, message)
        else:
            # Private message
            if target == self.client.nickname:
                # Message to us
                self._ensure_private_chat(source)
                self._add_chat_message(source, source, message)
            
    def _handle_join(self, data):
        """Handle channel join events"""
        user = data['user']
        channel = data['channel']
        
        if user == self.client.nickname:
            # We joined a channel
            self._create_channel_tab(channel)
            self.channel_tree.insert('', 'end', channel, text=channel)
        
        self._add_chat_message(channel, None, f"{user} joined the channel")
        
    def _handle_part(self, data):
        """Handle channel part events"""
        user = data['user']
        channel = data['channel']
        
        if user == self.client.nickname:
            # We left a channel
            self._remove_channel_tab(channel)
            item = self.channel_tree.find(channel)
            if item:
                self.channel_tree.delete(item)
        
        self._add_chat_message(channel, None, f"{user} left the channel")
        
    def _create_channel_tab(self, channel: str):
        """Create a new channel tab"""
        if channel not in self.channels:
            chat_area = scrolledtext.ScrolledText(self.chat_notebook, wrap=tk.WORD)
            self.channels[channel] = chat_area
            self.chat_notebook.add(chat_area, text=channel)
            
    def _ensure_private_chat(self, nickname: str):
        """Ensure private chat tab exists"""
        if nickname not in self.private_chats:
            chat_area = scrolledtext.ScrolledText(self.chat_notebook, wrap=tk.WORD)
            self.private_chats[nickname] = chat_area
            self.chat_notebook.add(chat_area, text=f"@{nickname}")
            
    def _add_chat_message(self, target: str, sender: Optional[str], message: str):
        """Add message to appropriate chat area"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        if target.startswith('#'):
            # Channel message
            if target in self.channels:
                chat_area = self.channels[target]
                if sender:
                    formatted_message = f"[{timestamp}] <{sender}> {message}\n"
                else:
                    formatted_message = f"[{timestamp}] * {message}\n"
                chat_area.configure(state='normal')
                chat_area.insert(tk.END, formatted_message)
                chat_area.configure(state='disabled')
                chat_area.see(tk.END)
        else:
            # Private message
            if target in self.private_chats:
                chat_area = self.private_chats[target]
                formatted_message = f"[{timestamp}] <{sender}> {message}\n"
                chat_area.configure(state='normal')
                chat_area.insert(tk.END, formatted_message)
                chat_area.configure(state='disabled')
                chat_area.see(tk.END)
                
    def _add_server_message(self, message: str):
        """Add message to server tab"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.server_tab.configure(state='normal')
        self.server_tab.insert(tk.END, formatted_message)
        self.server_tab.configure(state='disabled')
        self.server_tab.see(tk.END)
        
    def _on_channel_select(self, event):
        """Handle channel selection"""
        selection = self.channel_tree.selection()
        if selection:
            self.current_channel = self.channel_tree.item(selection[0])['text']
            
    def run(self):
        """Start the GUI"""
        self.root.mainloop()

if __name__ == "__main__":
    gui = IRCGui()
    gui.run()