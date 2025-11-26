from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# URL de conexión usando las credenciales de tu docker-compose
# formato: postgresql://usuario:contraseña@host:puerto/nombre_bd
import os

# Permite sobreescribir vía variable de entorno `DATABASE_URL` cuando se ejecuta en contenedor
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password123@localhost:5432/hce_db",
)

# Crear el motor de la base de datos
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Crear la sesión para hacer consultas
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()

# Dependencia para obtener la DB en cada petición (se usará luego en FastAPI)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()