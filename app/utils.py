from passlib.context import CryptContext

# Configuración para encriptar contraseñas usando Bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """Verifica si una contraseña plana coincide con el hash guardado."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Genera un hash seguro de la contraseña."""
    return pwd_context.hash(password)