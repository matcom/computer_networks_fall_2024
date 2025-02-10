class Channel:
    def __init__(self, name):
        self.name = name
        self.users = []
        self.operators = []
        self.t = False
        self.m= False
        self.topic = f"Bienvenido al canal {name}"
        
    def add_user(self, user):
        """Añade un usuario al canal"""
        if user not in self.users:
            self.users.append(user)
            return True
        return False
        
    def remove_user(self, user):
        """Elimina un usuario del canal"""
        if user in self.users:
            self.users.remove(user)
            if user in self.operators:
                self.operators.remove(user)
            return True
        return False
        
    def broadcast(self, message, exclude_user=None):
        """Envía un mensaje a todos los usuarios del canal"""
        for user in self.users:
            if user != exclude_user:
                user.send_message(message)
                
    def add_operator(self, user):
        """Hace operador a un usuario"""
        if user not in self.operators:
            self.add_user(user)
            self.operators.append(user)
            return True
        return False
    
    def remove_operator(self, user):
        """"Elimina un usuario de la lista de operadores"""
        if user in self.users and user in self.operators:
            self.operators.remove(user)
            return True
        return False
        
    def is_operator(self, user):
        """Verifica si un usuario es operador"""
        return user in self.operators
    
    def is_on_channel(self, user):
        """Verifica si un user está en un channel"""
        return user in self.users