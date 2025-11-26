import requests
import json
import os

# URL del servidor HAPI FHIR
# Lee desde variable de entorno o usa localhost por defecto
FHIR_HOST = os.getenv("FHIR_HOST", "localhost")
FHIR_PORT = os.getenv("FHIR_PORT", "8080")

FHIR_SERVER_URL = f"http://{FHIR_HOST}:{FHIR_PORT}/fhir"

# ---------------------------------------------------------
# FUNCIONES DE ESCRITURA (SQL -> FHIR)
# ---------------------------------------------------------

def sync_patient_to_fhir(usuario_sql):
    """Sincroniza Paciente construyendo el JSON manualmente (FHIR R4)"""
    print(f"--- Sincronizando Paciente: {usuario_sql.nombres} ---")
    
    fhir_id = f"pac-{usuario_sql.numero_documento}"
    
    patient_json = {
        "resourceType": "Patient",
        "id": fhir_id,
        "identifier": [
            {
                "system": f"http://hospital-universidad.com/identificacion/{usuario_sql.tipo_documento.prefijo}",
                "value": usuario_sql.numero_documento
            }
        ],
        "name": [
            {
                "use": "official",
                "family": usuario_sql.apellidos,
                "given": [usuario_sql.nombres]
            }
        ],
        "gender": "male" if usuario_sql.genero == "M" else "female",
    }
    
    if usuario_sql.fecha_nacimiento:
        patient_json["birthDate"] = str(usuario_sql.fecha_nacimiento)

    url = f"{FHIR_SERVER_URL}/Patient/{fhir_id}"
    return enviar_a_hapi(url, patient_json)

def sync_encounter_to_fhir(encuentro_sql):
    """Sincroniza Encuentro (Cita)"""
    print(f"--- Sincronizando Encuentro ID: {encuentro_sql.id} ---")
    
    fhir_id = f"enc-{encuentro_sql.id}"
    
    encounter_json = {
        "resourceType": "Encounter",
        "id": fhir_id,
        "status": "finished",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "AMB",
            "display": "ambulatory"
        },
        "subject": {
            "reference": f"Patient/pac-{encuentro_sql.paciente.numero_documento}"
        },
        "reasonCode": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "390906004", 
                        "display": encuentro_sql.diagnostico
                    }
                ]
            }
        ]
    }
    
    url = f"{FHIR_SERVER_URL}/Encounter/{fhir_id}"
    return enviar_a_hapi(url, encounter_json)

def sync_observation_to_fhir(obs_sql, paciente_doc):
    """Sincroniza Observación (Signos vitales)"""
    print(f"--- Sincronizando Observación ID: {obs_sql.id} ---")
    
    fhir_id = f"obs-{obs_sql.id}"
    
    try:
        val = float(obs_sql.valor)
        value_entry = {
            "valueQuantity": {
                "value": val,
                "unit": obs_sql.unidad,
                "system": "http://unitsofmeasure.org"
            }
        }
    except:
        value_entry = {"valueString": obs_sql.valor}

    observation_json = {
        "resourceType": "Observation",
        "id": fhir_id,
        "status": "final",
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "8867-4",
                    "display": obs_sql.descripcion
                }
            ]
        },
        "subject": {
            "reference": f"Patient/pac-{paciente_doc}"
        },
        "encounter": {
            "reference": f"Encounter/enc-{obs_sql.encuentro_id}"
        }
    }
    
    observation_json.update(value_entry)
    
    url = f"{FHIR_SERVER_URL}/Observation/{fhir_id}"
    return enviar_a_hapi(url, observation_json)

def enviar_a_hapi(url, data_json):
    headers = {"Content-Type": "application/fhir+json"}
    try:
        response = requests.put(url, json=data_json, headers=headers)
        if response.status_code in [200, 201]:
            print(f"✅ Sincronizado OK: {url.split('/')[-1]}")
            return True
        else:
            print(f"❌ Error HAPI {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error Conexión: {e}")
        return False

# ---------------------------------------------------------
# FUNCIONES DE LECTURA (FHIR -> FRONTEND)
# ---------------------------------------------------------

def get_patient_observations(paciente_doc):
    """
    Busca todas las observaciones de un paciente específico en FHIR.
    Esta es la función que te faltaba.
    """
    fhir_id = f"pac-{paciente_doc}"
    
    # Búsqueda FHIR: GET /fhir/Observation?subject=Patient/pac-{documento}
    url = f"{FHIR_SERVER_URL}/Observation?subject=Patient/{fhir_id}"
    headers = {"Accept": "application/fhir+json"}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            # HAPI devuelve un Bundle. Retornamos los entries (observaciones).
            bundle = response.json()
            return bundle.get('entry', [])
        else:
            print(f"❌ Error buscando FHIR: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error conexión FHIR: {e}")
        return []
    
def get_patient_encounters(paciente_doc):
    """
    Busca todos los encuentros (citas/diagnósticos) de un paciente en FHIR.
    """
    fhir_id = f"pac-{paciente_doc}"
    
    # Búsqueda FHIR: GET /fhir/Encounter?subject=Patient/pac-{documento}
    url = f"{FHIR_SERVER_URL}/Encounter?subject=Patient/{fhir_id}"
    headers = {"Accept": "application/fhir+json"}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            bundle = response.json()
            return bundle.get('entry', [])
        else:
            print(f"❌ Error buscando Encuentros FHIR: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error conexión FHIR Encuentros: {e}")
        return []