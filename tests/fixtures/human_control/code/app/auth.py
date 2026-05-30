def login(email: str, password: str) -> bool:
    return bool(email) and bool(password)


def register(email: str, password: str) -> dict:
    return {"email": email, "ok": True}
