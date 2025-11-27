#!/bin/bash
set -e

echo "🚀 Iniciando aplicación HCE..."

# Esperar a que la base de datos esté lista
echo "⏳ Esperando a que PostgreSQL esté listo..."
until python -c "import psycopg2; psycopg2.connect('$DATABASE_URL')" 2>/dev/null; do
  echo "PostgreSQL no está listo - esperando..."
  sleep 2
done

echo "✅ PostgreSQL está listo!"

# Inicializar base de datos (catálogos y usuarios de prueba)
echo "📊 Inicializando datos de la base de datos..."
python -m app.init_db

# Construir URL de FHIR desde variables de entorno
FHIR_URL="http://${FHIR_HOST}:${FHIR_PORT}/fhir"

# Esperar a que HAPI FHIR esté listo
echo "⏳ Esperando a que servidor FHIR esté listo en ${FHIR_URL}...."
max_attempts=100
attempt=0
until curl -s "${FHIR_URL}/metadata" > /dev/null 2>&1; do
  attempt=$((attempt + 1))
  if [ $attempt -ge $max_attempts ]; then
    echo "⚠️ FHIR no está disponible después de $max_attempts intentos. Continuando sin sincronización..."
    break
  fi
  echo "FHIR no está listo - esperando... (intento $attempt/$max_attempts)"
  sleep 3
done

if curl -s "${FHIR_URL}/metadata" > /dev/null 2>&1; then
  echo "✅ FHIR está listo!"
  # Sincronizar usuarios con FHIR
  echo "🔄 Sincronizando datos con servidor FHIR..."
  python -m app.sync_fhir
else
  echo "⚠️ Saltando sincronización FHIR."
fi

echo "🎉 Inicialización completa. Iniciando servidor Uvicorn..."

# Ejecutar el comando principal (Uvicorn)
exec "$@"
