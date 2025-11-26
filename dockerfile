# Usa una imagen base oficial de Python
FROM python:3.12-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

## ---------------- Dependencias del sistema necesarias ----------------
# Para xhtml2pdf / svglib / pycairo y WeasyPrint se requieren librerías nativas:
# - gcc, pkg-config, libcairo2-dev, libffi-dev, libjpeg-dev, zlib1g-dev
# - libpango-1.0-0, libgdk-pixbuf-2.0-0 (renderizado de texto y fuentes)
# - curl para healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc pkg-config libcairo2-dev libffi-dev libjpeg-dev zlib1g-dev \
    libpango-1.0-0 libgdk-pixbuf-2.0-0 curl && \
    rm -rf /var/lib/apt/lists/*

# Copia los archivos de requerimientos e instala dependencias Python (cache optimizada)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el script de entrada (entrypoint)
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copia todo el código fuente de la aplicación (la carpeta 'app')
COPY ./app /app/app

# Expone el puerto que usa Uvicorn
EXPOSE 8000

# Usar entrypoint para ejecutar init_db y sync_fhir antes de uvicorn
ENTRYPOINT ["/entrypoint.sh"]

# Comando para correr la aplicación (Modo producción)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]