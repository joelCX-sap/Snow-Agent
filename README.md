# Sistema de Gestión Aeroportuaria

Sistema integrado de análisis climático y gestión de procedimientos aeroportuarios, con frontend en UI5 Web Components (Vite) y backend en FastAPI. Incluye un pipeline RAG (Retrieval Augmented Generation) con embeddings y búsqueda vectorial en SAP HANA, así como orquestación de LLM a través de SAP Gen AI Hub.

## 🏗️ Arquitectura del Sistema

```
Aeropuertos-Web-fiori/
├── backend/                              # Backend FastAPI
│   ├── fastapi_app.py                    # API principal y endpoints
│   ├── rag_bariloche.py                  # Sistema RAG (embeddings, HANA, LLM)
│   ├── api.py                            # Servicios de clima (obtención externa)
│   ├── workflow_trigger.py               # Integración con SAP Build Process Automation
│   ├── process-automation-service-binding.json
│   ├── requirements.txt                  # Dependencias Python
│   ├── station_data.json                 # Datos locales para estación (MARWIS)
│   └── data/
│       └── historico.csv                 # Datos históricos para consultas
│
└── ui/                                   # Frontend UI5 Web Components (Vite)
    ├── index.html                        # Shell principal
    ├── vite.config.js
    ├── package.json
    ├── .env                              # Variables de entorno del front (Vite)
    ├── src/
    │   ├── main.js                       # Bootstrap de la app
    │   ├── style.css                     # Estilos globales
    │   ├── config/
    │   │   └── routes.js                 # Definición de rutas/páginas
    │   ├── modules/
    │   │   ├── navigation.js
    │   │   └── router.js                 # Enrutador simple
    │   ├── services/
    │   │   └── api.js                    # Cliente HTTP hacia el backend
    │   └── pages/
    │       ├── consulta-clima/           # Página de análisis climático (usa /weather)
    │       ├── historico-clima/          # Página de históricos (usa /historico)
    │       ├── estacion-marwis/          # Página MARWIS (usa /station-data)
    │       └── hana-rag/                 # Página de demo RAG/HANA
    └── public/
        └── images/                       # Recursos estáticos
```

## 🚀 Funcionalidades

- ✅ Análisis climático por ciudad y fecha, con síntesis contextual
- ✅ Sistema RAG: búsqueda semántica de procedimientos en documentos
- ✅ Gestión de documentos (PDF, DOCX, XLSX, CSV, PPTX)
- ✅ Orquestación LLM vía SAP Gen AI Hub (modelo gpt-4o) con prompt de sistema e instrucciones anti-alucinación
- ✅ Base vectorial en SAP HANA (REAL_VECTOR(1536))
- ✅ Integración con SAP Build Process Automation (envío de resultados a workflow)
- ✅ UI basada en UI5 Web Components (Vite) con rutas y módulos simples

## 📋 Requisitos

Backend:
- Python 3.8+
- pip
- Acceso a SAP HANA (para vector DB) y a SAP Gen AI Hub (si se desea LLM/embeddings reales)

Frontend:
- Node.js 16+
- npm

## 🔧 Instalación

### 1) Backend

```bash
cd backend
pip install -r requirements.txt
```

Crear y completar archivo `.env` (ejemplo de variables usadas por el código):

- ALLOWED_ORIGIN=http://localhost:5173
- EMBEDDING_MODEL_NAME=text-embedding-3-small
- HANA_ADDRESS=...
- HANA_PORT=443
- HANA_USER=...
- HANA_PASSWORD=...
- HANA_ENCRYPT=True

Notas:
- Para LLM y embeddings reales vía SAP Gen AI Hub, configurar las credenciales requeridas por el SDK `gen_ai_hub` (variables y bindings según su entorno). Si no están disponibles, el sistema usa fallback: embeddings determinísticos y respuesta de contexto sin LLM.

### 2) Frontend

```bash
cd ui
npm install
```

Configurar `ui/.env`:

- VITE_API_BASE_URL=http://127.0.0.1:8000
- VITE_API_KEY=your-super-secret-api-key

## 🏃 Ejecución

### Backend (FastAPI)

```bash
cd backend
python fastapi_app.py
```

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Frontend (Vite)

```bash
cd ui
npm run dev
```

- App: http://localhost:5173

## 🔌 Endpoints del Backend (FastAPI)

Información general:
- GET `/` → Metadatos de la API y endpoints.
- GET `/health` → Health check.

RAG / LLM:
- POST `/ask`
  - Request: `{ "question": "texto de consulta" }`
  - Respuesta: `{ "success": true, "answer": "...", "sources": [...] }`
  - Flujo: recupera contexto de HANA (RAG) y orquesta LLM si está disponible.

Análisis Climático + Procedimientos:
- POST `/weather`
  - Request: `{ "ciudad": "rio grande", "fecha": "YYYY-MM-DD" }`
  - Respuesta: `{ success, resultado: { clima_obtenido, condiciones_analizadas, respuesta_llm, fuentes, ... } }`
  - Flujo completo:
    1. Obtiene datos de clima (`api.py`)
    2. Analiza condiciones
    3. Genera consulta RAG contextual
    4. RAGService: busca en HANA y llama al LLM (si hay orquestación)
    5. Envía resultado a workflow SAP (best effort)

Gestión de Documentos (RAG):
- POST `/upload` (multipart/form-data)
  - Campo: `file`
  - Extensiones permitidas: pdf, docx, xlsx, xls, csv, pptx, ppt (máx 16MB)
  - Procesa documento: extracción → chunking → embeddings → almacenamiento en HANA
- GET `/documents/list` → Lista archivos en `backend/uploads/`
- GET `/documents/download/{filename}` → Descarga archivo
- GET `/stats` → Estadísticas (total de chunks, archivos, últimas actualizaciones)
- DELETE `/clear_all` → Limpia todos los registros de la tabla vectorial

Histórico:
- POST `/historico`
  - Request: `{ "fecha_inicio": "YYYY-MM-DD", "fecha_fin": "YYYY-MM-DD", "limite": 1000 }`
  - Devuelve registros filtrados desde `backend/data/historico.csv`

MARWIS (estación/sensores):
- GET `/station-data` → Devuelve listado desde `backend/station_data.json` (o formato antiguo)
- POST `/station-data/refresh` → Ejecuta `marwis.run_marwis()` para refrescar datos

## 🧠 Pipeline RAG/LLM (Backend)

Ubicación: `backend/rag_bariloche.py`

1. Ingesta de documentos
   - `DocumentProcessor`: soporta PDF/DOCX/XLSX/CSV/PPTX con extracción de texto.
   - `RAGService.chunk_text`: divide en chunks con solapamiento.
   - `EmbeddingService.get_embeddings`: genera embeddings vía `gen_ai_hub.proxy.native.openai.embeddings` (modelo por defecto `text-embedding-3-small`). Si no hay proxy, usa un embedding de respaldo determinístico.
   - `HANAVectorDB.store_document_chunks`: escribe en tabla HANA (por defecto `procedimientos_Bariloche`) con columna `VECTOR REAL_VECTOR(1536)`.

2. Búsqueda y respuesta
   - `HANAVectorDB.search_similar_chunks`: embedding de la query y similitud coseno en HANA.
   - Construcción del prompt:
     - `SystemMessage`: reglas estrictas anti-alucinación y formato esperado de respuesta.
     - `UserMessage`: incluye CONTEXTO (texto de chunks) + consulta del usuario o `generar_consulta_rag(...)`.
   - Orquestación LLM (si disponible):
     - `LLM(name="gpt-4o", version="latest")` + `Template(messages=[...])` + `OrchestrationService`.
     - Si no hay orquestación, retorna contexto resumido como fallback.
   - Fuentes: se devuelven los documentos coincidentes (filename, similitud, preview).

3. Consulta contextual desde clima
   - `backend/fastapi_app.py::generar_consulta_rag(condiciones)`: genera un texto con datos meteorológicos y la consulta específica según condiciones adversas detectadas. Este texto se inyecta en el `UserMessage` del LLM.

## 🎨 Páginas del Frontend

Rutas definidas en `ui/src/config/routes.js` y manejadas por `ui/src/modules/router.js`.

- Consulta de Clima (`/consulta-clima`)
  - Usa `apiService.getWeather(ciudad, fecha)`.
  - Renderiza `respuesta_llm` y `fuentes` en la UI.
- Histórico de Clima (`/historico-clima`)
  - Usa `apiService.consultarHistorico(fechaInicio, fechaFin, limite)`.
  - Muestra resultados tabulares filtrados por rango.
- Estación MARWIS (`/estacion-marwis`)
  - `apiService.getStationData()` y `apiService.refreshStationData()` para listar/actualizar sensores.
- HANA RAG (`/hana-rag`)
  - Página de demostración para funcionalidades RAG/HANA.

Cliente API del front: `ui/src/services/api.js`
- Config:
  - `VITE_API_BASE_URL` apunta al backend (por defecto http://127.0.0.1:8000).
  - `VITE_API_KEY` se envía como `X-API-Key` en headers (si aplica).
- Endpoints usados en este proyecto:
  - `/ask`, `/weather`, `/upload`, `/documents/list`, `/documents/download/{filename}`, `/clear_all`, `/historico`, `/station-data`, `/station-data/refresh`.
  - Nota: existen métodos legacy en `api.js` prefijados `/api/...` que no corresponden a los endpoints actuales de FastAPI; no se utilizan en este flujo.

## 🔒 Seguridad

- Validación de extensiones y tamaño (16MB) en `/upload`
- Validación de entrada con Pydantic
- CORS configurable vía `ALLOWED_ORIGIN`
- No exponer secretos en el repositorio (.env locales)

## 🛠️ Tecnologías

Backend:
- FastAPI, Uvicorn, Pydantic
- SAP Gen AI Hub SDK (orchestration y proxy de embeddings)
- SAP HANA con tipos vectoriales (`REAL_VECTOR(1536)`)

Frontend:
- UI5 Web Components
- Vite + Vanilla JS
- CSS responsive

## 🔄 Flujo de trabajo habitual

1. Cargar documentos desde `/upload`.
2. Consultar clima con `/weather` o hacer una pregunta con `/ask`.
3. El backend recupera contexto (RAG), arma prompts y consulta el LLM (si está disponible).
4. Se devuelve respuesta con fuentes y se muestra en la UI.
5. Opcional: envío de resultados a workflow SAP (Process Automation).

## 🐛 Troubleshooting

- Backend no inicia:
  - Verificar Python 3.8+, `pip install -r requirements.txt`
  - Revisar puertos y variables `.env`
- Frontend no inicia:
  - Verificar Node 16+, `npm install`
  - Revisar `VITE_API_BASE_URL`
- Error conexión UI ↔ Backend:
  - Confirmar backend en http://localhost:8000 y CORS (`ALLOWED_ORIGIN`)
- Documentos no se procesan:
  - Verificar extensión y tamaño
  - Revisar logs: extracción de texto/embeddings/HANA

## 📖 Documentación

- Backend API: http://localhost:8000/docs
- UI5 Web Components: https://sap.github.io/ui5-webcomponents/
- FastAPI: https://fastapi.tiangolo.com/
- HANA Vector: consultar documentación de su instancia/versión
- SAP Gen AI Hub: documentación del SDK `gen_ai_hub`

## 🤝 Contribución

Este proyecto es parte de un sistema de gestión aeroportuaria con integración a SAP Build Process Automation. Se aceptan mejoras y PRs alineados a la arquitectura definida.

## 📄 Licencia

[Especificar licencia]

## 🚦 Estado

- Backend FastAPI: funcional
- Frontend UI5: funcional
- Integración RAG/LLM: funcional con fallback si no hay orquestación
- Integración workflow: implementada (best effort)
