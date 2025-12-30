# API FastAPI - Sistema de Aeropuertos

API RESTful desarrollada con FastAPI para análisis climático y gestión de procedimientos aeroportuarios con sistema RAG (Retrieval Augmented Generation).

## 🚀 Características

- ✅ **Análisis Climático**: Obtención y análisis de datos meteorológicos
- ✅ **Sistema RAG**: Chatbot inteligente con búsqueda semántica
- ✅ **Gestión de Documentos**: Procesamiento de PDF, DOCX, XLSX, etc.
- ✅ **Integración Workflow**: Conexión con SAP Process Automation
- ✅ **Documentación Automática**: Swagger UI y ReDoc
- ✅ **CORS Habilitado**: Listo para frontends
- ✅ **Validación Automática**: Usando Pydantic

## 📦 Estructura del Proyecto

```
.
├── fastapi_app.py                          # API principal FastAPI
├── rag_bariloche.py                        # Sistema RAG
├── api.py                                  # Funciones de clima
├── workflow_trigger.py                     # Integración workflow
├── process-automation-service-binding.json # Configuración SAP
├── .env                                    # Variables de entorno
├── requirements.txt                        # Dependencias
├── uploads/                                # Archivos subidos
└── README.md                               # Documentación
```

## 🔧 Instalación

### 1. Requisitos Previos
- Python 3.8+
- pip

### 2. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```env
# Añade tus variables de entorno aquí
SECRET_KEY=tu-clave-secreta
# Otras variables necesarias...
```

## 🏃 Ejecución

### Modo Desarrollo

```bash
python fastapi_app.py
```

O usando uvicorn directamente:

```bash
uvicorn fastapi_app:app --reload --host 0.0.0.0 --port 8000
```

### Modo Producción

```bash
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --workers 4
```

La API estará disponible en: **http://localhost:8000**

## 📚 Documentación Interactiva

Una vez corriendo, accede a:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔌 Endpoints Principales

### Información General

#### `GET /`
Información de la API y lista de endpoints.

#### `GET /health`
Health check del servicio.

### Gestión de Documentos

#### `POST /upload`
Subir documentos para el sistema RAG.

**Ejemplo con cURL:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@documento.pdf"
```

**Ejemplo con Python:**
```python
import requests

url = "http://localhost:8000/upload"
files = {"file": open("documento.pdf", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

### Chatbot RAG

#### `POST /ask`
Hacer preguntas al sistema RAG.

**Request Body:**
```json
{
  "question": "¿Cuáles son los procedimientos para lluvia?"
}
```

**Ejemplo con cURL:**
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cuáles son los procedimientos para lluvia?"}'
```

**Ejemplo con Python:**
```python
import requests

url = "http://localhost:8000/ask"
data = {"question": "¿Cuáles son los procedimientos para lluvia?"}
response = requests.post(url, json=data)
print(response.json())
```

### Análisis Climático

#### `POST /weather`
Obtener análisis climático con procedimientos recomendados.

**Request Body:**
```json
{
  "ciudad": "San Carlos de Bariloche",
  "fecha": "2025-11-25"
}
```

**Ejemplo con Python:**
```python
import requests

url = "http://localhost:8000/weather"
data = {
    "ciudad": "San Carlos de Bariloche",
    "fecha": "2025-11-25"
}
response = requests.post(url, json=data)
print(response.json())
```

### Estadísticas

#### `GET /stats`
Obtener estadísticas de la base de datos vectorial.

#### `DELETE /clear_all`
Eliminar todos los documentos de la base de datos.

## 📝 Formatos de Archivo Soportados

- PDF (.pdf)
- Word (.docx)
- Excel (.xlsx, .xls)
- CSV (.csv)
- PowerPoint (.pptx, .ppt)

**Tamaño máximo:** 16MB

## 🔒 Seguridad

- Validación de tipos de archivo
- Límite de tamaño de archivo
- Validación de datos con Pydantic
- CORS configurable

## 🛠️ Tecnologías

- **FastAPI**: Framework web moderno y rápido
- **Uvicorn**: Servidor ASGI de alto rendimiento
- **Pydantic**: Validación de datos
- **SAP AI SDK**: Integración con servicios de IA
- **Pandas**: Procesamiento de datos
- **HANA DB**: Base de datos vectorial

## 📖 Documentación Adicional

Para más detalles sobre los endpoints, tipos de respuesta y ejemplos, visita:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Contribución

Este proyecto es parte del sistema de gestión aeroportuaria integrado con SAP Build Process Automation.

## 📄 Licencia

[Especifica tu licencia aquí]
