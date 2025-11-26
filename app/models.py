from sqlalchemy import Column, Integer, String, Date, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

# 1. Catálogos (Tablas Maestras)

class Rol(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)  # Admin, Medico, Paciente, Admisionista

class TipoDocumento(Base):
    __tablename__ = "tipos_documento"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    prefijo = Column(String, nullable=False) # CC, TI, RC, etc.

class Sede(Base):
    __tablename__ = "sedes"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    ciudad = Column(String, nullable=False)

class TipoEncuentro(Base):
    __tablename__ = "tipos_encuentro"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False) # Consulta General, Urgencia, Control

# 2. Usuarios (Centralizados)

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nombres = Column(String, nullable=False)
    apellidos = Column(String, nullable=False)
    
    # Llaves foráneas
    tipo_documento_id = Column(Integer, ForeignKey("tipos_documento.id"), nullable=False)
    numero_documento = Column(String, unique=True, nullable=False, index=True)
    
    fecha_nacimiento = Column(Date, nullable=False)
    genero = Column(String, nullable=False) # M/F
    telefono = Column(String, nullable=True)
    email = Column(String, nullable=True)
    
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=False) # Sede de registro
    rol_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    
    password_hash = Column(String, nullable=False) # Guardaremos la contraseña encriptada aquí
    
    # Relaciones para navegar fácilmente
    rol = relationship("Rol")
    sede = relationship("Sede")
    tipo_documento = relationship("TipoDocumento")

# 3. Datos Clínicos (Historia Clínica)

class EncuentroMedico(Base):
    __tablename__ = "encuentros_medicos"
    
    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    diagnostico = Column(String, nullable=False)
    
    # --- NUEVO CAMPO AGREGADO ---
    observaciones_generales = Column(String, nullable=True) 
    # ----------------------------

    # ... (el resto de relaciones sigue igual: tipo_id, sede_id, etc.)
    tipo_id = Column(Integer, ForeignKey("tipos_encuentro.id"), nullable=False)
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=False)
    medico_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    paciente_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    
    medico = relationship("Usuario", foreign_keys=[medico_id])
    paciente = relationship("Usuario", foreign_keys=[paciente_id])
    sede = relationship("Sede")
    tipo = relationship("TipoEncuentro")
    
    observaciones = relationship("ObservacionClinica", back_populates="encuentro")
    
    observaciones = relationship("ObservacionClinica", back_populates="encuentro")

class ObservacionClinica(Base):
    __tablename__ = "observaciones_clinicas"
    
    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    descripcion = Column(String, nullable=False) # Ej: Frecuencia Cardiaca
    valor = Column(String, nullable=False)       # Ej: 80
    unidad = Column(String, nullable=True)       # Ej: bpm
    interpretacion = Column(String, nullable=True) # Ej: Normal
    
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=False)
    encuentro_id = Column(Integer, ForeignKey("encuentros_medicos.id"), nullable=False)
    
    encuentro = relationship("EncuentroMedico", back_populates="observaciones")