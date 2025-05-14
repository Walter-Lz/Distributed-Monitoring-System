FROM python:3.9-slim

# Instalar dependencias del sistema necesarias para psutil
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Crear y establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos necesarios
COPY requirements.txt .
COPY node.py .
COPY utils/ utils/

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Comando para ejecutar el nodo
CMD ["python", "node.py"] 