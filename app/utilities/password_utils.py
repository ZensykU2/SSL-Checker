import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')  

def verify_password(provided_password: str, stored_hash: str) -> bool:
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_hash.encode('utf-8'))