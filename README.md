Distributed Monitoring System

Sistema distribuido para monitoreo y procesamiento distribuido de tareas (transcripción de audios) en tiempo real usando Python, Redis, FastAPI y Next.js.

---

¿Qué hace este proyecto?

- Asigna tareas de transcripción de audio a varios nodos de procesamiento.
- Monitorea en tiempo real el estado de los nodos y las tareas usando WebSocket.
- Muestra los resultados y el estado de los nodos en una interfaz web moderna (Next.js).

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
