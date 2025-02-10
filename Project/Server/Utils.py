import json
def load_db():
    with open('user_database.json', 'r') as file:
        return json.load(file)

def save_user(user_db):
    with open('user_database.json', 'r') as file:
        json.dump(user_db, file, indent=4)

def add_user(user_db, username, password):
    user_db.append({'user': username, 'pass': password})
    save_user(user_db)

def user_exists(user_db, username):
    return any(user['user'] == username for user in user_db)

def authenticate_user(user_db, username, password):
    for user in user_db:
        if user['user'] == username and user['pass'] == password:
            return True
    return False