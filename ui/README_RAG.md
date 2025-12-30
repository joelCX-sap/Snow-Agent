# 🚗 Tire Discounts - RAG Knowledge Base

Sistema de chat inteligente con base de conocimientos vectorial para Tire Discounts.

## 📋 Descripción

Este módulo añade funcionalidad de RAG (Retrieval-Augmented Generation) al frontend, permitiendo:

1. **Chat Inteligente**: Hacer preguntas sobre documentos cargados usando IA
2. **Gestión de Documentos**: Cargar, procesar y administrar documentos en la base de datos vectorial

## 🎯 Nuevas Páginas

### 1. RAG Chat (`/rag-chat`)

Página de chat inteligente que permite hacer preguntas sobre los documentos cargados.

**Características:**
- Chat conversacional con historial
- Búsqueda semántica en documentos vectorizados
- Fuentes citadas con similitud
- Descarga de documentos fuente
- Estadísticas de la base de datos

**Uso:**
1. Escribe tu pregunta en el campo de texto
2. Haz clic en "Ask Question" o presiona Ctrl+Enter
3. El sistema buscará información relevante y generará una respuesta
4. Puedes ver las fuentes utilizadas y descargar los documentos

### 2. Gestión de Documentos (`/rag-documents`)

Página para administrar documentos y la base de datos vectorial.

**Características:**
- Carga de documentos (PDF, DOCX, XLSX, CSV, PPTX)
- Procesamiento automático y vectorización
- Estadísticas de la base de datos en tiempo real
- Lista de documentos disponibles
- Descarga de documentos
- Limpieza de base de datos

**Uso:**
1. Selecciona un archivo para cargar
2. Haz clic en "Upload and Process"
3. El sistema extraerá el texto, lo dividirá en chunks y generará embeddings
4. Los documentos quedan disponibles para consulta en el chat

## 🔧 Configuración

### Requisitos Previos

1. **Backend API en ejecución:**
```bash
cd backend
python api.py
```

El backend debe estar corriendo en `http://localhost:8000`

2. **Variables de entorno configuradas** (`ui/.env`):
```env
VITE_API_BASE_URL="http://127.0.0.1:8000/"
VITE_API_KEY="your-super-secret-api-key"
```

### Instalación

1. Instalar dependencias:
```bash
cd ui
npm install
```

2. Iniciar servidor de desarrollo:
```bash
npm run dev
```

3. Abrir en el navegador: `http://localhost:5173`

## 📡 Endpoints de API Utilizados

El frontend consume los siguientes endpoints del backend:

### Chat
- `POST /api/chat/ask` - Hacer preguntas al RAG

### Documentos
- `POST /api/documents/upload` - Cargar y procesar documento
- `GET /api/documents/list` - Listar documentos disponibles
- `GET /api/documents/download/{filename}` - Descargar documento

### Base de Datos
- `GET /api/stats` - Obtener estadísticas de la base de datos
- `DELETE /api/database/clear` - Limpiar toda la base de datos

## 🗂️ Estructura de Archivos

```
ui/src/
├── services/
│   └── api.js                          # Servicio de API con endpoints RAG
├── pages/
│   ├── rag-chat/                       # Página de chat inteligente
│   │   ├── rag-chat.html
│   │   ├── rag-chat.js
│   │   └── rag-chat.css
│   └── rag-documents/                  # Página de gestión de documentos
│       ├── rag-documents.html
│       ├── rag-documents.js
│       └── rag-documents.css
└── config/
    └── routes.js                       # Configuración de rutas
```

## 💡 Ejemplos de Uso

### Preguntas de Ejemplo

```
- ¿Qué es BOPIS y cómo funciona?
- ¿Cuál es la política de devolución de neumáticos?
- ¿Cómo manejo una devolución de orden de compra?
- ¿Qué documentación necesito para SHOP?
- ¿Cuáles son las mejores prácticas para clientes web?
```

### Formatos Soportados

- **PDF** (.pdf)
- **Word** (.docx)
- **Excel** (.xlsx, .xls)
- **CSV** (.csv)
- **PowerPoint** (.pptx, .ppt)

## 🎨 Componentes UI5

El frontend utiliza SAP UI5 Web Components:

- `ui5-title` - Títulos
- `ui5-label` - Etiquetas
- `ui5-button` - Botones
- `ui5-panel` - Paneles colapsables
- `ui5-textarea` - Áreas de texto
- `ui5-message-strip` - Mensajes informativos
- `ui5-dialog` - Diálogos de confirmación
- `ui5-busy-indicator` - Indicadores de carga
- `ui5-link` - Enlaces

## 🔐 Seguridad

- Las peticiones incluyen un API Key configurado en `.env`
- CORS configurado en el backend para permitir peticiones del frontend
- Validación de tipos de archivo en el frontend y backend

## 🐛 Troubleshooting

### El chat no responde

1. Verifica que el backend esté corriendo: `http://localhost:8000/docs`
2. Verifica que haya documentos cargados en la base de datos
3. Revisa la consola del navegador para errores

### No puedo cargar documentos

1. Verifica el formato del archivo (debe ser uno de los soportados)
2. Verifica el tamaño del archivo (límites del backend)
3. Revisa los logs del backend para errores de procesamiento

### La base de datos no muestra estadísticas

1. Verifica la conexión con HANA
2. Revisa las credenciales en `backend/.env`
3. Asegúrate de que la tabla `RAG_TIRES` existe

## 📊 Flujo de Datos

```
1. Usuario carga documento
   ↓
2. Frontend envía archivo a /api/documents/upload
   ↓
3. Backend extrae texto del documento
   ↓
4. Backend divide texto en chunks
   ↓
5. Backend genera embeddings (vectores)
   ↓
6. Backend almacena en HANA tabla RAG_TIRES
   ↓
7. Usuario hace pregunta en chat
   ↓
8. Backend busca chunks similares usando cosine similarity
   ↓
9. Backend genera respuesta con LLM usando contexto
   ↓
10. Frontend muestra respuesta y fuentes
```

## 🚀 Próximas Mejoras

- [ ] Filtrado de documentos por tipo o fecha
- [ ] Historial de chat persistente
- [ ] Exportar conversaciones
- [ ] Búsqueda avanzada de documentos
- [ ] Vista previa de documentos
- [ ] Múltiples idiomas
- [ ] Análisis de sentimiento en respuestas

## 📝 Notas

- El sistema utiliza embeddings de OpenAI (`text-embedding-3-small`)
- Las respuestas se generan con SAP AI Hub (GPT-4o)
- Los vectores se almacenan en SAP HANA Cloud
- La búsqueda utiliza similitud coseno para encontrar chunks relevantes

## 📞 Soporte

Para problemas o preguntas, consulta:
- Documentación de API: `backend/API_DOCUMENTATION.md`
- Logs del backend: Terminal donde corre `python api.py`
- Logs del frontend: Consola del navegador (F12)
