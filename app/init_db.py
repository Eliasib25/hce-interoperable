from .database import SessionLocal, engine, Base
from . import models
from .utils import get_password_hash
import datetime

def init_db():
    # Crear todas las tablas primero
    print("Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas!")
    
    db = SessionLocal()
    
    try:
        # 1. Crear Roles
        roles = ["Medico", "Paciente", "Admisionista"]
        for nombre_rol in roles:
            rol_existente = db.query(models.Rol).filter_by(nombre=nombre_rol).first()
            if not rol_existente:
                db.add(models.Rol(nombre=nombre_rol))
        
        # 2. Crear Tipos de Documento
        tipos_doc = [
            {"nombre": "Cédula de Ciudadanía", "prefijo": "CC"},
            {"nombre": "Tarjeta de Identidad", "prefijo": "TI"},
            {"nombre": "Cédula de Extranjería", "prefijo": "CE"},
            {"nombre": "Pasaporte", "prefijo": "PA"}
        ]
        for td in tipos_doc:
            td_existente = db.query(models.TipoDocumento).filter_by(nombre=td["nombre"]).first()
            if not td_existente:
                db.add(models.TipoDocumento(nombre=td["nombre"], prefijo=td["prefijo"]))

        # 3. Crear Sedes
        sedes = [
            {"nombre": "Sede Central", "ciudad": "Bogotá"},
            {"nombre": "Sede Norte", "ciudad": "Medellín"},
            {"nombre": "Sede Occidente", "ciudad": "Cali"}
        ]
        for sede in sedes:
            sede_existente = db.query(models.Sede).filter_by(nombre=sede["nombre"]).first()
            if not sede_existente:
                db.add(models.Sede(nombre=sede["nombre"], ciudad=sede["ciudad"]))
                
        # 4. Crear Tipos de Encuentro
        tipos_encuentro = ["Consulta General", "Urgencia", "Control", "Examenes"]
        for te in tipos_encuentro:
            te_ex = db.query(models.TipoEncuentro).filter_by(nombre=te).first()
            if not te_ex:
                db.add(models.TipoEncuentro(nombre=te))

        db.commit() # Guardar catálogos para tener los IDs disponibles
        print("--- Catálogos creados ---")

        # 5. Crear Usuarios de Prueba (Uno por cada Rol)
        # Obtener referencias primero
        rol_medico = db.query(models.Rol).filter_by(nombre="Medico").first()
        rol_paciente = db.query(models.Rol).filter_by(nombre="Paciente").first()
        rol_admi = db.query(models.Rol).filter_by(nombre="Admisionista").first()
        
        sede_bog = db.query(models.Sede).filter_by(ciudad="Bogotá").first()
        sede_med = db.query(models.Sede).filter_by(ciudad="Medellín").first()
        doc_cc = db.query(models.TipoDocumento).filter_by(prefijo="CC").first()
        
        # Generar hash de contraseña una sola vez con contraseña corta y simple
        # Contraseña genérica para todos: '12345'
        password_generico = get_password_hash("12345")

        usuarios_prueba = [
            # Usuarios Sede Bogotá
            models.Usuario(
                nombres="Pepito", apellidos="Perez", tipo_documento_id=doc_cc.id,
                numero_documento="2002", fecha_nacimiento=datetime.date(1985, 5, 20),
                genero="M", email="medico@hce.com", sede_id=sede_bog.id, rol_id=rol_medico.id,
                password_hash=password_generico
            ),
            models.Usuario(
                nombres="Juanita", apellidos="Lopez", tipo_documento_id=doc_cc.id,
                numero_documento="3003", fecha_nacimiento=datetime.date(1995, 3, 10),
                genero="F", email="paciente@hce.com", sede_id=sede_bog.id, rol_id=rol_paciente.id,
                password_hash=password_generico
            ),
            models.Usuario(
                nombres="Carlos", apellidos="Gomez", tipo_documento_id=doc_cc.id,
                numero_documento="4004", fecha_nacimiento=datetime.date(1990, 8, 15),
                genero="M", email="admi@hce.com", sede_id=sede_bog.id, rol_id=rol_admi.id,
                password_hash=password_generico
            ),
            # Usuarios Sede Medellín
            models.Usuario(
                nombres="Maria", apellidos="Rodriguez", tipo_documento_id=doc_cc.id,
                numero_documento="5005", fecha_nacimiento=datetime.date(1988, 7, 12),
                genero="F", email="medico.medellin@hce.com", sede_id=sede_med.id, rol_id=rol_medico.id,
                password_hash=password_generico
            ),
            models.Usuario(
                nombres="Andres", apellidos="Martinez", tipo_documento_id=doc_cc.id,
                numero_documento="6006", fecha_nacimiento=datetime.date(1992, 11, 25),
                genero="M", email="admi.medellin@hce.com", sede_id=sede_med.id, rol_id=rol_admi.id,
                password_hash=password_generico
            )
        ]

        for u in usuarios_prueba:
            u_ex = db.query(models.Usuario).filter_by(numero_documento=u.numero_documento).first()
            if not u_ex:
                db.add(u)
        
        db.commit()
        print("--- Usuarios de prueba creados ---")
        
    except Exception as e:
        print(f"Error al poblar datos: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Iniciando poblado de datos...")
    init_db()
    print("Finalizado.")