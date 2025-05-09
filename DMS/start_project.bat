@echo off
echo 🚀 Iniciando el proyecto Distributed Monitoring System...

REM 1. Activar el entorno virtual
if not exist venv (
    echo 📦 Creando entorno virtual...
    python -m venv venv
)
echo 🐍 Activando entorno virtual...
call venv\Scripts\activate

REM 2. Instalar dependencias
echo 📦 Instalando dependencias...


REM 3. Iniciar Redis con Docker Compose
echo 🐳 Iniciando Redis con Docker Compose...
docker-compose up -d

REM 4. Ejecutar nodos
echo 🖥️ Ejecutando nodos...
for /L %%i in (1,1,3) do (
    echo 🔧 Iniciando nodo %%i...
    start cmd /k "venv\Scripts\activate && python node.py"
)

REM 5. Ejecutar cliente principal
echo 📤 Ejecutando cliente principal...
start cmd /k "venv\Scripts\activate && python main.py"

REM 6. (Opcional) Iniciar servidor API
echo 🌐 Iniciando servidor API...
start cmd /k "venv\Scripts\activate && uvicorn api:app --reload"

REM 7. Levantar la interfaz web
echo 🌐 Iniciando la interfaz web...
cd web
start cmd /k "npm install && npm start"
cd ..

echo ✅ Proyecto iniciado correctamente.
pause