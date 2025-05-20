Distributed Monitoring System

Sistema distribuido para monitoreo y procesamiento distribuido de tareas (transcripción de audios) en tiempo real usando Python, Redis, FastAPI y Next.js.

---

¿Qué hace este proyecto?

- Asigna tareas de transcripción de audio a varios nodos de procesamiento.
- Monitorea en tiempo real el estado de los nodos y las tareas usando WebSocket.
- Muestra los resultados y el estado de los nodos en una interfaz web moderna (Next.js).

---

Instalación rápida

1.Clona el repositorio
   ```bash
   git clone <url-del-repo>
   cd Distributed-Monitoring-System
   ```
2.Levantar redis
   ```bash
  docker-compose up -d
```
3.Dependencias de python
   ```bash
  cd DMS
  python -m venv venv
  venv\Scripts\activate
  pip install -r requirements.txt
  pip install openai-whisper ffmpeg-python redis psutil fastapi uvicorn
```
4.Dependencias del frontend
  ```bash
  cd web
  npm install
   ```
---

Requisitos

- Python 3.8+
- Docker y Docker Compose
- Node.js y npm
- FFmpeg (Para Whisper)
- Redis (Se levanta con Docker)

---

Uso
Coloca archivos .mp3 en la carpeta audios/.
El sistema asignará tareas automáticamente a los nodos disponibles.
Accede a la interfaz web en http://localhost:3000 para ver el monitoreo en tiempo real.

---

Documentación de la API
# Documentación de la API

Esta API está construida con FastAPI y expone endpoints HTTP y un WebSocket para monitoreo en tiempo real del sistema distribuido.

---

## Endpoints HTTP

### `GET /docs`
- **Descripción:** Documentación interactiva Swagger de la API.
- **Respuesta:** Interfaz web para probar los endpoints.

---

## WebSocket

### `ws://127.0.0.1:8000/ws`
- **Descripción:** Canal WebSocket para recibir actualizaciones en tiempo real sobre el estado de los nodos, tareas y resultados.
- **Método:** Conexión WebSocket

#### **Formato de los mensajes recibidos:**
   ```json
{
  "nodes": {
    "node1": {
      "cpu": "23.5",
      "ram": "40.2",
      "disk": "60.1",
      "tasks": "1"
      "current_tasks": ["task1"],
      "completed_tasks": ["task2"]
    },
    ...
  },
  "tasks": {
    "node1": ["task1", "task2"],
    ...
  },
  "results": {
    "node1": ["resultado1", "resultado2"],
    ...
  }
}
```
---

Créditos

-FastAPI
-Next.js
-OpenAI Whisper
-Redis
-FFMPEG
