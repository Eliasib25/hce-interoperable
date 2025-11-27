# DOCUMENTACIÓN TÉCNICA
## Sistema de Historia Clínica Electrónica (HCE) Interoperable

---

## 📋 TABLA DE CONTENIDO

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura General](#arquitectura-general)
3. [Diagrama de Flujo de Interoperabilidad](#diagrama-de-flujo-de-interoperabilidad)
4. [Esquema de Mapeo Semántico](#esquema-de-mapeo-semántico)
5. [Justificación de Estándares](#justificación-de-estándares)
6. [Componentes del Sistema](#componentes-del-sistema)
7. [Modelo de Datos](#modelo-de-datos)
8. [API y Endpoints](#api-y-endpoints)
9. [Seguridad](#seguridad)
10. [Despliegue](#despliegue)

---

## 1. RESUMEN EJECUTIVO

### 1.1 Descripción del Sistema

El sistema HCE Interoperable es una plataforma de gestión de historias clínicas electrónicas que implementa estándares de interoperabilidad en salud, permitiendo el intercambio semántico de información médica entre diferentes sistemas.

### 1.2 Características Principales

- **Multi-sede**: Gestión de pacientes en múltiples sedes (Bogotá, Medellín, Cali)
- **Multi-rol**: Soporte para Médicos, Pacientes, Admisionistas y Administradores
- **Interoperabilidad FHIR R4**: Sincronización bidireccional con servidor HAPI FHIR
- **Gestión Clínica Completa**: Registro de encuentros médicos, diagnósticos, observaciones y signos vitales
- **Exportación PDF**: Generación de historias clínicas en formato PDF
- **Responsive Design**: Interfaces adaptables a dispositivos móviles

### 1.3 Tecnologías Utilizadas

| Categoría | Tecnología | Versión |
|-----------|-----------|---------|
| Backend | FastAPI | Latest |
| Base de Datos | PostgreSQL + Citus | Latest |
| Servidor FHIR | HAPI FHIR JPA Server | v6.8.0 |
| Lenguaje | Python | 3.12 |
| Contenedores | Docker + Docker Compose | Latest |
| Orquestación | Kubernetes (k8s) | Latest |
| Frontend | Jinja2 Templates + CSS | - |

---

## 2. ARQUITECTURA GENERAL

### 2.1 Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                        CAPA DE PRESENTACIÓN                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Dashboard   │  │  Dashboard   │  │  Dashboard   │          │
│  │   Médico     │  │  Paciente    │  │  Admisionista│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                  │                  │                  │
│         └──────────────────┴──────────────────┘                  │
│                           │                                      │
└───────────────────────────┼──────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE APLICACIÓN (FastAPI)                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  API REST                                                │   │
│  │  - Autenticación (JWT)                                   │   │
│  │  - Gestión de Usuarios                                   │   │
│  │  - Gestión de Encuentros Médicos                         │   │
│  │  - Gestión de Observaciones Clínicas                     │   │
│  │  - Exportación PDF                                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           │                                      │
│              ┌────────────┴────────────┐                         │
│              ▼                         ▼                         │
│  ┌────────────────────┐    ┌────────────────────┐              │
│  │  FHIR Client       │    │  SQLAlchemy ORM    │              │
│  │  (Interoperabilidad)│    │  (Persistencia)    │              │
│  └────────────────────┘    └────────────────────┘              │
└─────────────┬──────────────────────┬────────────────────────────┘
              │                      │
              ▼                      ▼
┌──────────────────────┐  ┌──────────────────────┐
│  HAPI FHIR Server    │  │  PostgreSQL + Citus  │
│  (Puerto 8080)       │  │  (Puerto 5432)       │
│                      │  │                      │
│  Recursos FHIR:      │  │  Tablas:             │
│  - Patient           │  │  - usuarios          │
│  - Encounter         │  │  - encuentros_medicos│
│  - Observation       │  │  - observaciones...  │
│  - Practitioner      │  │  - catálogos (roles, │
│                      │  │    sedes, etc.)      │
└──────────────────────┘  └──────────────────────┘
```

### 2.2 Patrón Arquitectónico

El sistema implementa una **arquitectura de 3 capas** con un componente adicional de interoperabilidad:

1. **Capa de Presentación**: Interfaces web responsive (HTML/CSS/JS)
2. **Capa de Aplicación**: Lógica de negocio en FastAPI
3. **Capa de Datos**: Base de datos SQL + Servidor FHIR
4. **Componente de Interoperabilidad**: Cliente FHIR para sincronización

### 2.3 Modelo de Despliegue

#### Desarrollo (Docker Compose)
```yaml
Servicios:
├── db_citus (PostgreSQL + Citus)
├── hapifhir (HAPI FHIR Server)
└── app (FastAPI Application)
```

#### Producción (Kubernetes)
```yaml
Recursos:
├── Deployment (3 réplicas de app)
├── Service (LoadBalancer)
├── ConfigMaps (Configuración)
└── Secrets (Credenciales)
```

---

## 3. DIAGRAMA DE FLUJO DE INTEROPERABILIDAD

### 3.1 Flujo SQL → FHIR (Sincronización de Datos)

```
┌─────────────────────────────────────────────────────────────────┐
│  EVENTO: Creación/Actualización en Base de Datos SQL            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │  1. Trigger: Nuevo Registro    │
         │     - Usuario (Paciente)       │
         │     - Encuentro Médico         │
         │     - Observación Clínica      │
         └────────────┬───────────────────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │  2. FHIR Client (Python)       │
         │     fhir_client.py             │
         └────────────┬───────────────────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │  3. Mapeo Semántico            │
         │     SQL → FHIR Resource        │
         │                                │
         │  Usuario → Patient             │
         │  Encuentro → Encounter         │
         │  Observación → Observation     │
         └────────────┬───────────────────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │  4. Construcción JSON FHIR     │
         │     - resourceType             │
         │     - id (identificador único) │
         │     - coding (SNOMED/LOINC)    │
         │     - references               │
         └────────────┬───────────────────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │  5. HTTP PUT Request           │
         │     FHIR_SERVER_URL/Resource/id│
         │     Headers: application/json  │
         └────────────┬───────────────────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │  6. HAPI FHIR Server           │
         │     - Validación FHIR R4       │
         │     - Persistencia             │
         │     - Indexación               │
         └────────────┬───────────────────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │  7. Respuesta HTTP             │
         │     200 OK ✓                   │
         │     400 Bad Request ✗          │
         └────────────────────────────────┘
```

### 3.2 Flujo FHIR → Frontend (Consulta de Datos)

```
┌─────────────────────────────────────────────────────────────────┐
│  EVENTO: Usuario Solicita Historial Clínico                     │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │  1. Request HTTP GET           │
         │     /dashboard                 │
         │     Cookie: access_token       │
         └────────────┬───────────────────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │  2. Autenticación JWT          │
         │     - Validar Token            │
         │     - Extraer Usuario          │
         │     - Verificar Rol            │
         └────────────┬───────────────────┘
                      │
           ┌──────────┴──────────┐
           │                     │
           ▼                     ▼
┌──────────────────┐   ┌──────────────────┐
│  3a. Query SQL   │   │  3b. Query FHIR  │
│  (Base de Datos) │   │  (Opcional)      │
│                  │   │                  │
│  - Encuentros    │   │  GET /Encounter  │
│  - Observaciones │   │  ?subject=...    │
│  - Datos Demog.  │   │                  │
└────────┬─────────┘   └────────┬─────────┘
         │                      │
         └──────────┬───────────┘
                    ▼
         ┌────────────────────────────────┐
         │  4. Agregación de Datos        │
         │     - Merge SQL + FHIR         │
         │     - Ordenamiento cronológico │
         │     - Formateo                 │
         └────────────┬───────────────────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │  5. Render Template            │
         │     dashboard_paciente.html    │
         │     - Historial completo       │
         │     - Diagnósticos             │
         │     - Tratamientos             │
         │     - Signos vitales           │
         └────────────┬───────────────────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │  6. Response HTML              │
         │     200 OK + Página renderizada│
         └────────────────────────────────┘
```

### 3.3 Flujo de Sincronización Inicial

```
┌─────────────────────────────────────────────────────────────────┐
│  INICIO: Contenedor Docker arranca (entrypoint.sh)              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │  1. Esperar PostgreSQL         │
         │     Health Check Loop          │
         │     hasta que esté listo       │
         └────────────┬───────────────────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │  2. Inicializar Base de Datos  │
         │     python -m app.init_db      │
         │                                │
         │     - Crear tablas             │
         │     - Insertar catálogos       │
         │     - Crear usuarios de prueba │
         └────────────┬───────────────────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │  3. Esperar HAPI FHIR          │
         │     Curl metadata endpoint     │
         │     Max 100 intentos           │
         └────────────┬───────────────────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │  4. Sincronizar con FHIR       │
         │     python -m app.sync_fhir    │
         │                                │
         │     FOR EACH usuario:          │
         │       sync_patient_to_fhir()   │
         └────────────┬───────────────────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │  5. Iniciar Uvicorn            │
         │     FastAPI en puerto 8000     │
         └────────────────────────────────┘
```

---

## 4. ESQUEMA DE MAPEO SEMÁNTICO

### 4.1 Mapeo: Usuario (SQL) → Patient (FHIR)

| Campo SQL | Tipo SQL | Campo FHIR | Tipo FHIR | Transformación |
|-----------|----------|------------|-----------|----------------|
| `numero_documento` | String | `identifier[0].value` | string | Directo |
| `tipo_documento.prefijo` | String | `identifier[0].system` | uri | `http://hospital-universidad.com/identificacion/{prefijo}` |
| `nombres` | String | `name[0].given[0]` | string | Directo |
| `apellidos` | String | `name[0].family` | string | Directo |
| `genero` | String (M/F) | `gender` | code | M → "male", F → "female" |
| `fecha_nacimiento` | Date | `birthDate` | date | Formato ISO 8601 (YYYY-MM-DD) |
| `telefono` | String | `telecom[0].value` | string | Sistema: "phone" |
| `email` | String | `telecom[1].value` | string | Sistema: "email" |

**Ejemplo de Mapeo:**

```json
// SQL Record
{
  "numero_documento": "3003",
  "tipo_documento": {"prefijo": "CC"},
  "nombres": "Juanita",
  "apellidos": "Lopez",
  "genero": "F",
  "fecha_nacimiento": "1995-03-10"
}

// FHIR Patient Resource
{
  "resourceType": "Patient",
  "id": "pac-3003",
  "identifier": [{
    "system": "http://hospital-universidad.com/identificacion/CC",
    "value": "3003"
  }],
  "name": [{
    "use": "official",
    "family": "Lopez",
    "given": ["Juanita"]
  }],
  "gender": "female",
  "birthDate": "1995-03-10"
}
```

### 4.2 Mapeo: EncuentroMedico (SQL) → Encounter (FHIR)

| Campo SQL | Campo FHIR | Transformación/Coding |
|-----------|------------|----------------------|
| `id` | `id` | Prefijo: `enc-{id}` |
| `fecha` | `period.start` | ISO 8601 DateTime |
| `tipo.nombre` | `type[0].coding[0].display` | Sistema: ActCode |
| `diagnostico` | `reasonCode[0].coding[0].display` | Sistema: SNOMED CT (390906004) |
| `paciente.numero_documento` | `subject.reference` | `Patient/pac-{documento}` |
| `medico.numero_documento` | `participant[0].individual.reference` | `Practitioner/med-{documento}` |
| `sede.nombre + ciudad` | `location[0].location.display` | Concatenación |
| - | `status` | Valor fijo: "finished" |
| - | `class.code` | Valor fijo: "AMB" (ambulatory) |

**Códigos SNOMED CT Utilizados:**
- `390906004`: "Consulta médica" (Medical consultation)
- Extensible según diagnósticos específicos

### 4.3 Mapeo: ObservacionClinica (SQL) → Observation (FHIR)

| Campo SQL | Campo FHIR | Transformación/Coding |
|-----------|------------|----------------------|
| `id` | `id` | Prefijo: `obs-{id}` |
| `fecha` | `effectiveDateTime` | ISO 8601 DateTime |
| `descripcion` | `code.coding[0].display` + `code.text` | LOINC code según tipo |
| `valor` | `valueQuantity.value` | Conversión a float |
| `unidad` | `valueQuantity.unit` | UCUM (Unified Code for Units of Measure) |
| `interpretacion` | `interpretation[0].text` | Texto libre |
| `encuentro_id` | `encounter.reference` | `Encounter/enc-{id}` |
| - | `status` | Valor fijo: "final" |
| - | `category[0].coding[0].code` | "vital-signs" |

**Códigos LOINC para Signos Vitales:**

| Signo Vital | Código LOINC | Unidad UCUM |
|-------------|--------------|-------------|
| Frecuencia Cardíaca | 8867-4 | /min (bpm) |
| Presión Arterial Sistólica | 8480-6 | mm[Hg] |
| Presión Arterial Diastólica | 8462-4 | mm[Hg] |
| Temperatura Corporal | 8310-5 | Cel (°C) |
| Frecuencia Respiratoria | 9279-1 | /min |
| Saturación de Oxígeno | 2708-6 | % |
| Peso | 29463-7 | kg |
| Altura | 8302-2 | cm |

### 4.4 Flujo de Mapeo Bidireccional

```
┌─────────────────────────────────────────────────────────────────┐
│                    SISTEMA DE MAPEO SEMÁNTICO                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
           ┌──────────────┴──────────────┐
           │                             │
           ▼                             ▼
┌────────────────────┐         ┌────────────────────┐
│   BASE DE DATOS    │         │  SERVIDOR FHIR     │
│   POSTGRESQL       │         │  HAPI FHIR         │
│                    │         │                    │
│  Modelo Relacional │◄───────►│  Recursos FHIR     │
│  - Normalizado     │  Mapeo  │  - JSON            │
│  - Integridad FK   │ Semantic│  - Estándares HL7  │
│  - SQL             │         │  - RESTful API     │
└────────────────────┘         └────────────────────┘
         │                              │
         │                              │
         ▼                              ▼
┌────────────────────┐         ┌────────────────────┐
│  Ventajas SQL      │         │  Ventajas FHIR     │
│  - Consultas rápidas│         │  - Interoperabilidad│
│  - Transacciones   │         │  - Estándar global │
│  - Relaciones      │         │  - Extensible      │
│  - Reportes locales│         │  - Intercambio     │
└────────────────────┘         └────────────────────┘
```

---

## 5. JUSTIFICACIÓN DE ESTÁNDARES

### 5.1 FHIR R4 (Fast Healthcare Interoperability Resources)

#### ¿Qué es FHIR?

FHIR es un estándar desarrollado por HL7 International para el intercambio electrónico de información de salud. La versión R4 (Release 4) es la primera normativa oficial del estándar.

#### Justificación de Uso

| Criterio | Justificación |
|----------|--------------|
| **Interoperabilidad** | Permite que diferentes sistemas de salud intercambien información sin pérdida semántica |
| **Adopción Global** | Usado por organizaciones como NHS (UK), CMS (USA), Ministerios de Salud en LATAM |
| **RESTful API** | Arquitectura moderna, fácil integración con aplicaciones web y móviles |
| **Recursos Modulares** | Patient, Encounter, Observation son recursos independientes y reutilizables |
| **Extensibilidad** | Permite personalizar recursos sin romper la compatibilidad |
| **JSON/XML** | Formatos de datos ampliamente soportados |

#### Recursos FHIR Implementados

1. **Patient**: Información demográfica del paciente
   - Identificadores únicos
   - Datos de contacto
   - Información administrativa

2. **Encounter**: Encuentros o consultas médicas
   - Fecha y hora de la consulta
   - Motivo de consulta
   - Diagnósticos
   - Ubicación (sede)

3. **Observation**: Observaciones clínicas y signos vitales
   - Mediciones numéricas (peso, temperatura, PA)
   - Interpretaciones
   - Códigos LOINC

4. **Practitioner**: Profesionales de la salud (médicos)
   - Identificación profesional
   - Especialidades

### 5.2 SNOMED CT (Systematized Nomenclature of Medicine - Clinical Terms)

#### ¿Qué es SNOMED CT?

Es la terminología clínica más completa y multilingüe del mundo, que proporciona códigos, términos, sinónimos y definiciones para describir conceptos clínicos.

#### Justificación de Uso

| Criterio | Justificación |
|----------|--------------|
| **Cobertura Completa** | Más de 350,000 conceptos clínicos activos |
| **Multilingüe** | Soporta español, inglés y otros idiomas |
| **Estándar OMS** | Recomendado por la Organización Mundial de la Salud |
| **Interoperabilidad Semántica** | Permite que diferentes sistemas "entiendan" el mismo concepto |
| **Requisito Legal** | Exigido en regulaciones de salud digital en varios países |

#### Implementación en el Sistema

```python
# Ejemplo de código SNOMED CT en Encounter
"reasonCode": [{
    "coding": [{
        "system": "http://snomed.info/sct",
        "code": "390906004",  # Código SNOMED
        "display": "Consulta médica"  # Término descriptivo
    }]
}]
```

**Códigos SNOMED CT Comunes:**
- `390906004`: Consulta médica
- `185347001`: Encuentro con médico de atención primaria
- `73761001`: Procedimiento colonoscópico
- `449868002`: Medición de presión arterial

### 5.3 LOINC (Logical Observation Identifiers Names and Codes)

#### ¿Qué es LOINC?

LOINC es un sistema de codificación universal para identificar observaciones clínicas, mediciones de laboratorio y signos vitales.

#### Justificación de Uso

| Criterio | Justificación |
|----------|--------------|
| **Estándar para Laboratorios** | Utilizado por más de 175 países |
| **Compatibilidad FHIR** | Recomendado por HL7 para Observation resources |
| **Especificidad** | Códigos únicos para cada tipo de medición |
| **Gratuito** | Uso sin costo para implementaciones clínicas |
| **Actualización Continua** | Nuevos códigos agregados semestralmente |

#### Implementación en el Sistema

```python
# Ejemplo de código LOINC en Observation
"code": {
    "coding": [{
        "system": "http://loinc.org",
        "code": "8867-4",  # Código LOINC
        "display": "Heart rate"  # Término estándar
    }],
    "text": "Frecuencia Cardíaca"  # Texto local
}
```

**Tabla de Mapeo LOINC Implementada:**

| Medición | Código LOINC | Nombre Estándar |
|----------|--------------|-----------------|
| Frecuencia Cardíaca | 8867-4 | Heart rate |
| PA Sistólica | 8480-6 | Systolic blood pressure |
| PA Diastólica | 8462-4 | Diastolic blood pressure |
| Temperatura | 8310-5 | Body temperature |
| Frecuencia Respiratoria | 9279-1 | Respiratory rate |
| Saturación O₂ | 2708-6 | Oxygen saturation |
| Peso | 29463-7 | Body weight |
| Altura | 8302-2 | Body height |

### 5.4 UCUM (Unified Code for Units of Measure)

#### ¿Qué es UCUM?

Sistema de códigos para representar unidades de medida en sistemas de información en salud.

#### Justificación de Uso

| Criterio | Justificación |
|----------|--------------|
| **Estándar FHIR** | Requerido para valueQuantity en Observations |
| **No Ambigüedad** | Elimina confusión entre unidades similares |
| **Conversión Automática** | Permite conversión entre unidades compatibles |
| **Cobertura Completa** | Incluye unidades SI, imperiales y especializadas |

**Códigos UCUM Utilizados:**

| Unidad | Código UCUM | Descripción |
|--------|-------------|-------------|
| Latidos/minuto | `/min` | Frecuencia cardíaca |
| mmHg | `mm[Hg]` | Presión arterial |
| Grados Celsius | `Cel` | Temperatura |
| Porcentaje | `%` | Saturación de oxígeno |
| Kilogramos | `kg` | Peso |
| Centímetros | `cm` | Altura |

### 5.5 OAuth 2.0 + JWT (JSON Web Tokens)

#### Justificación de Uso

| Criterio | Justificación |
|----------|--------------|
| **Seguridad** | Token firmado criptográficamente |
| **Stateless** | No requiere sesiones en servidor |
| **Escalabilidad** | Ideal para arquitecturas distribuidas |
| **Estándar Industrial** | Ampliamente adoptado (Google, Facebook, etc.) |
| **FHIR Smart on FHIR** | Compatible con autenticación SMART para apps de salud |

---

## 6. COMPONENTES DEL SISTEMA

### 6.1 FastAPI Application (app/)

#### Estructura de Módulos

```
app/
├── __init__.py           # Inicialización del paquete
├── main.py               # Punto de entrada, rutas principales
├── models.py             # Modelos SQLAlchemy (ORM)
├── schemas.py            # Esquemas Pydantic (validación)
├── database.py           # Configuración de BD
├── auth.py               # Autenticación JWT
├── utils.py              # Funciones auxiliares (hash passwords)
├── fhir_client.py        # Cliente FHIR (sincronización)
├── init_db.py            # Inicialización de datos
├── sync_fhir.py          # Script de sincronización
├── static/               # CSS, JS, imágenes
│   └── styles.css
└── templates/            # Plantillas Jinja2
    ├── login.html
    ├── dashboard_paciente.html
    ├── dashboard_medico.html
    ├── dashboard_admin.html
    └── pdf_template.html
```

#### Módulos Principales

**main.py** - API REST y Rutas Web
```python
Endpoints:
├── POST /token                    # Login API (OAuth2)
├── GET /login                     # Página de login
├── POST /login                    # Procesar login web
├── GET /dashboard                 # Dashboard según rol
├── GET /medico/buscar_paciente    # Buscar historial
├── POST /medico/guardar_consulta  # Registrar consulta
├── GET /exportar_pdf              # Descargar historia clínica
└── POST /logout                   # Cerrar sesión
```

**models.py** - Modelo de Datos ORM
```python
Entidades:
├── Rol                 # Admin, Medico, Paciente, Admisionista
├── TipoDocumento       # CC, TI, CE, PA
├── Sede                # Bogotá, Medellín, Cali
├── TipoEncuentro       # Consulta, Urgencia, Control
├── Usuario             # Tabla central de usuarios
├── EncuentroMedico     # Consultas/Citas
└── ObservacionClinica  # Signos vitales, laboratorios
```

**fhir_client.py** - Sincronización FHIR
```python
Funciones:
├── sync_patient_to_fhir()       # Usuario → Patient
├── sync_encounter_to_fhir()     # Encuentro → Encounter
├── sync_observation_to_fhir()   # Observación → Observation
├── get_patient_observations()   # Consultar FHIR
├── get_patient_encounters()     # Consultar FHIR
└── enviar_a_hapi()              # HTTP PUT wrapper
```

### 6.2 PostgreSQL + Citus

#### Justificación de Citus

| Característica | Beneficio |
|----------------|-----------|
| **Distribución Horizontal** | Escalabilidad para millones de registros |
| **Sharding Automático** | Datos distribuidos por sede/región |
| **Consultas SQL Estándar** | Compatible con PostgreSQL |
| **Multitenancy** | Ideal para arquitectura multi-sede |

#### Esquema de Base de Datos

```sql
-- Catálogos
roles (id, nombre)
tipos_documento (id, nombre, prefijo)
sedes (id, nombre, ciudad)
tipos_encuentro (id, nombre)

-- Entidad Central
usuarios (
    id PK,
    nombres, apellidos,
    tipo_documento_id FK,
    numero_documento UNIQUE,
    fecha_nacimiento, genero,
    telefono, email,
    sede_id FK,
    rol_id FK,
    password_hash
)

-- Datos Clínicos
encuentros_medicos (
    id PK,
    fecha TIMESTAMP,
    diagnostico TEXT,
    observaciones_generales TEXT,
    tipo_id FK,
    sede_id FK,
    medico_id FK,
    paciente_id FK
)

observaciones_clinicas (
    id PK,
    fecha TIMESTAMP,
    descripcion VARCHAR,  -- "Frecuencia Cardíaca"
    valor VARCHAR,        -- "80"
    unidad VARCHAR,       -- "bpm"
    interpretacion TEXT,
    sede_id FK,
    encuentro_id FK
)
```

### 6.3 HAPI FHIR Server

#### Configuración

```yaml
Imagen: hapiproject/hapi:v6.8.0
Puerto: 8080
Base de Datos: H2 (en memoria) / PostgreSQL (producción)
Versión FHIR: R4
```

#### Endpoints FHIR Utilizados

```
GET  /fhir/metadata                          # Capacidades del servidor
PUT  /fhir/Patient/{id}                      # Crear/Actualizar paciente
GET  /fhir/Patient?identifier=...            # Buscar paciente
PUT  /fhir/Encounter/{id}                    # Crear encuentro
GET  /fhir/Encounter?subject=Patient/{id}    # Buscar encuentros
PUT  /fhir/Observation/{id}                  # Crear observación
GET  /fhir/Observation?subject=Patient/{id}  # Buscar observaciones
```

---

## 7. MODELO DE DATOS

### 7.1 Diagrama Entidad-Relación

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│    Rol      │         │TipoDocumento │         │    Sede     │
├─────────────┤         ├──────────────┤         ├─────────────┤
│ id PK       │         │ id PK        │         │ id PK       │
│ nombre      │         │ nombre       │         │ nombre      │
└──────┬──────┘         │ prefijo      │         │ ciudad      │
       │                └──────┬───────┘         └──────┬──────┘
       │                       │                        │
       │                       │                        │
       └───────────┬───────────┴────────────┬───────────┘
                   │                        │
                   ▼                        ▼
            ┌─────────────────────────────────────┐
            │            Usuario                  │
            ├─────────────────────────────────────┤
            │ id PK                               │
            │ nombres, apellidos                  │
            │ tipo_documento_id FK                │
            │ numero_documento UNIQUE             │
            │ fecha_nacimiento, genero            │
            │ telefono, email                     │
            │ sede_id FK                          │
            │ rol_id FK                           │
            │ password_hash                       │
            └──────────┬─────────────┬────────────┘
                       │             │
         ┌─────────────┘             └─────────────┐
         │ (como médico)                (como paciente)
         │                                          │
         ▼                                          ▼
┌─────────────────────────────────────────────────────┐
│              EncuentroMedico                        │
├─────────────────────────────────────────────────────┤
│ id PK                                               │
│ fecha TIMESTAMP                                     │
│ diagnostico TEXT                                    │
│ observaciones_generales TEXT                        │
│ tipo_id FK → TipoEncuentro                          │
│ sede_id FK → Sede                                   │
│ medico_id FK → Usuario                              │
│ paciente_id FK → Usuario                            │
└────────────────────┬────────────────────────────────┘
                     │
                     │ 1:N
                     │
                     ▼
         ┌────────────────────────────┐
         │   ObservacionClinica       │
         ├────────────────────────────┤
         │ id PK                      │
         │ fecha TIMESTAMP            │
         │ descripcion VARCHAR        │
         │ valor VARCHAR              │
         │ unidad VARCHAR             │
         │ interpretacion TEXT        │
         │ sede_id FK → Sede          │
         │ encuentro_id FK            │
         └────────────────────────────┘

         ┌────────────────────────────┐
         │     TipoEncuentro          │
         ├────────────────────────────┤
         │ id PK                      │
         │ nombre VARCHAR             │
         │   (Consulta, Urgencia...)  │
         └────────────────────────────┘
```

### 7.2 Cardinalidades

```
Rol          1:N Usuario
TipoDocumento 1:N Usuario
Sede          1:N Usuario
Sede          1:N EncuentroMedico
Usuario       1:N EncuentroMedico (como médico)
Usuario       1:N EncuentroMedico (como paciente)
TipoEncuentro 1:N EncuentroMedico
EncuentroMedico 1:N ObservacionClinica
Sede          1:N ObservacionClinica
```

---

## 8. API Y ENDPOINTS

### 8.1 Autenticación

#### POST /token
```http
POST /token HTTP/1.1
Content-Type: application/x-www-form-urlencoded

username=3003&password=12345

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 8.2 Dashboard

#### GET /dashboard
```http
GET /dashboard HTTP/1.1
Cookie: access_token=Bearer eyJhbGc...

Response: HTML (dashboard según rol)
```

### 8.3 Médico - Buscar Paciente

#### GET /medico/buscar_paciente
```http
GET /medico/buscar_paciente?q_doc=3003 HTTP/1.1
Cookie: access_token=Bearer eyJhbGc...

Response: HTML con historial clínico del paciente
```

### 8.4 Médico - Guardar Consulta

#### POST /medico/guardar_consulta
```http
POST /medico/guardar_consulta HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Cookie: access_token=Bearer eyJhbGc...

paciente_doc=3003&
tipo_encuentro=1&
diagnostico=Hipertensión arterial&
tratamiento=Enalapril 10mg&
observaciones=Control en 30 días&
fc=75&pa_sistolica=130&pa_diastolica=85&
temperatura=36.5&fr=18&spo2=98&peso=70&altura=165

Response: Redirect a /dashboard
```

### 8.5 Exportar PDF

#### GET /exportar_pdf
```http
GET /exportar_pdf HTTP/1.1
Cookie: access_token=Bearer eyJhbGc...

Response: application/pdf
Content-Disposition: attachment; filename="historia_clinica_3003.pdf"
```

---

## 9. SEGURIDAD

### 9.1 Autenticación y Autorización

#### JWT (JSON Web Tokens)

```python
# Estructura del Token
{
  "sub": "3003",              # Número de documento (sujeto)
  "role": "Paciente",         # Rol del usuario
  "exp": 1732723200           # Timestamp de expiración
}

# Firma
HMAC-SHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  SECRET_KEY
)
```

#### Control de Acceso por Rol

| Rol | Permisos |
|-----|----------|
| **Paciente** | - Ver su propia historia clínica<br>- Descargar PDF de su historia<br>- Ver datos personales |
| **Médico** | - Buscar pacientes<br>- Ver historias clínicas completas<br>- Registrar consultas<br>- Registrar observaciones |
| **Admisionista** | - Buscar pacientes<br>- Registrar pacientes nuevos<br>- Actualizar datos demográficos<br>- Agendar citas |
| **Admin** | - Todos los permisos<br>- Gestión de usuarios<br>- Configuración del sistema |

### 9.2 Protección de Datos

#### Encriptación de Contraseñas

```python
# Usando bcrypt + passlib
password_hash = get_password_hash("12345")
# Resultado: $2b$12$... (60 caracteres)

# Verificación
verify_password("12345", password_hash)  # → True
```

#### Variables de Entorno Sensibles

```bash
# docker-compose.yml
environment:
  DATABASE_URL: "postgresql://postgres:password123@db_citus:5432/hce_db"
  SECRET_KEY: "clave-super-secreta-cambiar-en-produccion"
  FHIR_HOST: "hapifhir"
```

### 9.3 Validación de Datos

```python
# Pydantic Schemas
class UsuarioBase(BaseModel):
    nombres: str
    apellidos: str
    email: Optional[EmailStr] = None  # Validación de email
    
    @validator('nombres')
    def validar_nombres(cls, v):
        if len(v) < 2:
            raise ValueError('Nombre muy corto')
        return v
```

---

## 10. DESPLIEGUE

### 10.1 Docker Compose (Desarrollo)

```yaml
# docker-compose.yml
version: '3.8'

services:
  db_citus:
    image: citusdata/citus:latest
    ports: ["5432:5432"]
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password123
      POSTGRES_DB: hce_db
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      
  hapifhir:
    image: hapiproject/hapi:v6.8.0
    ports: ["8080:8080"]
    
  app:
    build: .
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: "postgresql://postgres:password123@db_citus:5432/hce_db"
      FHIR_HOST: "hapifhir"
      FHIR_PORT: "8080"
    depends_on:
      - db_citus
      - hapifhir
```

**Comandos:**
```bash
# Construir y levantar
docker compose up -d --build

# Ver logs
docker compose logs -f app

# Detener
docker compose down

# Eliminar volúmenes (datos)
docker compose down -v
```

### 10.2 Kubernetes (Producción)

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hce-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hce
  template:
    metadata:
      labels:
        app: hce
    spec:
      containers:
      - name: app
        image: hce-app:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: hce-secrets
              key: database-url
        - name: FHIR_HOST
          value: "hapifhir-service"
```

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: hce-service
spec:
  type: LoadBalancer
  selector:
    app: hce
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
```

**Comandos:**
```bash
# Aplicar configuración
kubectl apply -f k8s/

# Ver pods
kubectl get pods

# Ver logs
kubectl logs -f deployment/hce-app

# Escalar
kubectl scale deployment hce-app --replicas=5
```

### 10.3 Flujo de Despliegue Continuo

```
┌────────────────┐
│  Git Push      │
│  (main branch) │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  GitHub Actions│
│  / GitLab CI   │
└───────┬────────┘
        │
        ├─► Run Tests
        ├─► Build Docker Image
        ├─► Push to Registry
        │
        ▼
┌────────────────┐
│  Kubernetes    │
│  Pull Image    │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  Rolling Update│
│  (Zero Downtime)│
└────────────────┘
```

---

## ANEXOS

### A. Glosario de Términos

| Término | Definición |
|---------|-----------|
| **HCE** | Historia Clínica Electrónica |
| **FHIR** | Fast Healthcare Interoperability Resources |
| **HL7** | Health Level 7 International (organización de estándares) |
| **SNOMED CT** | Systematized Nomenclature of Medicine - Clinical Terms |
| **LOINC** | Logical Observation Identifiers Names and Codes |
| **UCUM** | Unified Code for Units of Measure |
| **JWT** | JSON Web Token |
| **ORM** | Object-Relational Mapping |
| **REST** | Representational State Transfer |

### B. Referencias

1. **FHIR R4 Specification**: https://hl7.org/fhir/R4/
2. **SNOMED CT Browser**: https://browser.ihtsdotools.org/
3. **LOINC Database**: https://loinc.org/
4. **HAPI FHIR Documentation**: https://hapifhir.io/
5. **FastAPI Documentation**: https://fastapi.tiangolo.com/
6. **PostgreSQL + Citus**: https://www.citusdata.com/

### C. Contacto y Mantenimiento

**Equipo de Desarrollo:**
- Universidad: [Nombre de la Universidad]
- Materia: Integración de Soluciones
- Semestre: Décimo Semestre
- Fecha: Noviembre 2025

**Repositorio:**
- GitHub: jaiderreyes/interop_masterdata_fhir_colombia

---

## CONCLUSIONES

Este sistema HCE Interoperable implementa las mejores prácticas de interoperabilidad en salud:

1. ✅ **Estándares Globales**: FHIR R4, SNOMED CT, LOINC
2. ✅ **Arquitectura Escalable**: Docker, Kubernetes, Citus
3. ✅ **Seguridad Robusta**: JWT, bcrypt, HTTPS
4. ✅ **Mapeo Semántico**: SQL ↔ FHIR bidireccional
5. ✅ **Multi-sede**: Escalable a múltiples ubicaciones
6. ✅ **Responsive**: Interfaces adaptables a móviles

El sistema está preparado para:
- Integración con sistemas externos vía FHIR
- Escalamiento horizontal (más usuarios, más sedes)
- Cumplimiento de regulaciones de salud digital
- Extensión con nuevos recursos FHIR

---

**Versión del Documento**: 1.0  
**Última Actualización**: 27 de Noviembre de 2025  
**Autor**: Sistema HCE - Equipo de Desarrollo
