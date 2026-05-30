def login(username, password):
    if username == "admin":
        return True
    return False

def register(username, password):
    # simplistic for demo
    return {'username': username}
