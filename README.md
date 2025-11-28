# 🏥 HCE Interoperable - Sistema de Historia Clínica Electrónica

Sistema de gestión de historias clínicas electrónicas con interoperabilidad FHIR R4, multi-sede y control de acceso basado en roles.

## ✨ Características

- **🔐 Autenticación Segura**: Sistema JWT con cookies httponly y encriptación bcrypt
- **👥 Multi-rol**: Soporte para Médicos, Pacientes, Admisionistas
- **🏢 Multi-sede**: Gestión de usuarios en Bogotá, Medellín y Cali
- **🔄 Interoperabilidad FHIR R4**: Sincronización bidireccional con servidor HAPI FHIR
- **📊 Gestión Clínica Completa**: Encuentros médicos, diagnósticos, observaciones y signos vitales
- **📄 Exportación PDF**: Generación automática de historias clínicas
- **📱 Responsive Design**: Interfaces adaptables a dispositivos móviles

**Estándares Implementados:**
- FHIR R4 (Fast Healthcare Interoperability Resources)
- SNOMED CT (Terminología clínica)
- LOINC (Códigos de observaciones clínicas)
- UCUM (Unidades de medida)

---

## 🚀 Configuración y Despliegue

### Requisitos Previos

- **Docker Desktop** 
- **Docker Compose** 
- **Git**

### Paso 1: Clonar el Repositorio

```bash
# Clonar el repositorio desde GitHub
git clone https://github.com/Eliasib25/hce-interoperable.git

# Navegar al directorio del proyecto
cd hce_interoperable
```

### Paso 2: Construir y Desplegar con Docker

```bash
# Construir las imágenes y levantar los servicios
docker compose up -d --build
```

Este comando inicia tres contenedores:
1. **db_citus** (PostgreSQL + Citus) - Puerto 5432
2. **hapifhir** (HAPI FHIR Server R4) - Puerto 8080
3. **hce_app** (Aplicación FastAPI) - Puerto 8000

Y crea la imgaen de la app: 

hce_interoperable-app que corresponde a (middleware-citus:1.0)

### Paso 3: Verificar el Despliegue

```bash
# Ver el estado de los contenedores
docker compose ps

# Ver logs de inicialización
docker compose logs -f app
```

**Logs esperados:**
```
🚀 Iniciando aplicación HCE...
✅ PostgreSQL está listo!
📊 Inicializando datos de la base de datos...
✅ Tablas creadas!
--- Usuarios de prueba creados ---
✅ FHIR está listo!
🔄 Sincronizando datos con servidor FHIR...
🎉 Inicialización completa. Iniciando servidor Uvicorn...
```

---

## 🔐 Acceso al Sistema

### URL de Acceso

```
http://localhost:8000
```

### Usuarios de Prueba

#### 🏙️ Sede Bogotá

| Rol | Usuario | Contraseña | Nombre |
|-----|---------|------------|--------|
| Médico | `2002` | `12345` | Pepito Perez |
| Paciente | `3003` | `12345` | Juanita Lopez |
| Admisionista | `4004` | `12345` | Carlos Gomez |

#### 🌆 Sede Medellín

| Rol | Usuario | Contraseña | Nombre |
|-----|---------|------------|--------|
| Médico | `5005` | `12345` | Maria Rodriguez |
| Admisionista | `6006` | `12345` | Andres Martinez |

#### 🏖️ Sede Cali

| Rol | Usuario | Contraseña | Nombre |
|-----|---------|------------|--------|
| Médico | `7007` | `12345` | Laura Gonzalez |
| Admisionista | `8008` | `12345` | Miguel Torres |

### Funcionalidades por Rol

- **Médico**: Buscar pacientes, registrar consultas, ver antecedentes clínicos
- **Paciente**: Ver historia clínica completa, descargar PDF
- **Admisionista**: Buscar y gestionar información de pacientes

---

**¡Sistema listo para usar! 🎉**
