from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from . import database, models, schemas
from fastapi import Request


# Configuración de Seguridad
SECRET_KEY = "12345" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Indica a FastAPI dónde buscar el token (en la URL /token)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Genera el token JWT encriptado"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    # Guardamos el usuario (sub) y el rol en el token
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    """Decodifica el token y valida al usuario actual"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub") # Aquí vendrá el numero_documento
        role: str = payload.get("role")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username, role=role)
    except JWTError:
        raise credentials_exception
        
    user = db.query(models.Usuario).filter(models.Usuario.numero_documento == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_user_from_cookie(request: Request, db: Session = Depends(database.get_db)):
    """Extrae el token de la cookie y valida al usuario."""
    token = request.cookies.get("access_token")
    if not token:
        return None # No hay sesión iniciada
    
    # El token viene como "Bearer eyJhbG..." hay que quitar el "Bearer "
    try:
        scheme, _, param = token.partition(" ")
        if scheme.lower() != "bearer":
            return None
        
        # Reutilizamos la lógica de validación que ya creamos
        payload = jwt.decode(param, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
            
        user = db.query(models.Usuario).filter(models.Usuario.numero_documento == username).first()
        return user
    except Exception:
        return None