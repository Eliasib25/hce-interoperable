from .database import SessionLocal
from .models import Usuario
from .fhir_client import sync_patient_to_fhir

def sync_all_patients():
    db = SessionLocal()
    try:
        # Buscamos solo los usuarios que sean pacientes o todos si quieres probar
        # En este caso enviaremos TODOS para que queden registrados como Personas en el sistema FHIR
        usuarios = db.query(Usuario).all()
        
        print(f"Encontrados {len(usuarios)} usuarios para sincronizar...")
        
        for u in usuarios:
            sync_patient_to_fhir(u)
            
    except Exception as e:
        print(f"Error general: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    sync_all_patients()