import tkinter as tk
from tkinter import font
from datetime import datetime
class ChatWindow:
    def __init__(self, controller, name):
        self.controller = controller
        self.name = name

                # Create a new Tkinter window
        self.window = tk.Toplevel()
        self.window.title(name)

        # Get the size of the default font
        default_font = font.nametofont("TkDefaultFont")
        default_size = default_font.cget("size")

        # Create a font object with the default font, the default size, and a bold weight
        bold_font = font.Font(size=default_size, weight='bold')

        # Create a text widget for displaying messages
        self.text_widget = tk.Text(self.window)
        self.text_widget.pack()
        self.text_widget.tag_configure('bold', font=bold_font)
        self.text_widget.tag_configure('timestamp', foreground='blue')


        # Create an entry widget for typing messages
        self.entry_widget = tk.Entry(self.window)
        self.entry_widget.pack(side=tk.BOTTOM, fill=tk.X)

        # Bind the Return key to the send_message method
        self.entry_widget.bind("<Return>", self.send_message)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def show(self):
        # Start the Tkinter event loop
        self.window.mainloop()

    def send_message(self, event):
        # Get the message from the entry widget and send it to the controller
        message = self.entry_widget.get() 
        self.controller.send_message(message, self.name)
        # print("canal self.name "+ self.name)
        self.display_message(message, self.controller.user_nick)

        # Clear the entry widget
        self.entry_widget.delete(0, tk.END)

    def display_message(self, message, sender=None):
        current_time = datetime.now().strftime('%H:%M:%S')
        # Prepend the timestamp to the message
        current_time = "[{}] ".format(current_time)
        self.text_widget.insert(tk.END, current_time, 'timestamp')

        if sender is None:
            self.text_widget.insert(tk.END, message + "\n")
        else:
            # Display the sender in bold and the message in the text widget
            self.text_widget.insert(tk.END, "<", 'bold')
            self.text_widget.insert(tk.END, sender, 'bold')
            self.text_widget.insert(tk.END, "> ", 'bold')
            self.text_widget.insert(tk.END, message + "\n")

    def on_close(self):
        # Remove this ChannelWindow from the chat_windows dictionary
        if self.name in self.controller.chat_windows and '#' in self.name :
            self.controller.handle_user_command("/PART "+self.name) 
        elif self.name in self.controller.chat_windows and '#' not in self.name :
            self.controller.remove_channel_window(self.name)
        else:
            self.window.destroy()