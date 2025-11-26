from pydantic import BaseModel
from typing import Optional, List
from datetime import date

# 1. Esquemas para Autenticación (Token)
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

# 2. Esquemas para Usuarios (Lectura)
class UsuarioBase(BaseModel):
    nombres: str
    apellidos: str
    email: Optional[str] = None
    rol_id: int

class UsuarioOut(UsuarioBase):
    id: int
    numero_documento: str
    
    class Config:
        from_attributes = True # Permite leer desde los modelos de SQLAlchemy