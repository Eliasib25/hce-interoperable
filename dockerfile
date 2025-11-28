# Imgen base oficial de Python 3.12 slim
FROM python:3.12-slim

# Se establece el directorio de trabajo dentro del contenedor
WORKDIR /app
# Se instalan las dependencias del sistema necesarias para la aplicación
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc pkg-config libcairo2-dev libffi-dev libjpeg-dev zlib1g-dev \
    libpango-1.0-0 libgdk-pixbuf-2.0-0 curl && \
    rm -rf /var/lib/apt/lists/*

# Se copian los archivos de requerimientos e instalan dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Se copia el script de entrada (entrypoint)
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Se copia la carpeta de la aplicación al contenedor
COPY ./app /app/app

# Expone el puerto que usa Uvicorn
EXPOSE 8000

# Se usa el archivo entrypoint para ejecutar init_db y sync_fhir antes de uvicorn
ENTRYPOINT ["/entrypoint.sh"]

# Comando para correr la aplicación (Modo producción)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]