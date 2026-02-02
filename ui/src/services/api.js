const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const API_KEY = import.meta.env.VITE_API_KEY || "your-super-secret-api-key";

// General Request function to the API
export async function request(endpoint, method = "GET", body = null, headers = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY,
      ...headers
    },
    body: body ? JSON.stringify(body) : null
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

// File upload request function (for multipart/form-data)
export async function uploadRequest(endpoint, formData, headers = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "POST",
    headers: {
      "X-API-Key": API_KEY,
      ...headers
      // Note: Don't set Content-Type for FormData, let browser set it with boundary
    },
    body: formData
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

// API Service object with all endpoints
export const apiService = {
  // Health check
  async checkHealth() {
    return request("/health");
  },

  // Chat endpoints
  async chatAnthropic(message, temperature = 0.6, maxTokens = 1000) {
    return request("/api/chat/anthropic", "POST", {
      message,
      temperature,
      max_tokens: maxTokens
    });
  },

  async chatOpenAI(message, temperature = 0.6, maxTokens = 1000) {
    return request("/api/chat/openai", "POST", {
      message,
      temperature,
      max_tokens: maxTokens
    });
  },

  async chatGemini(message, temperature = 0.6, maxTokens = 1000) {
    return request("/api/chat/gemini", "POST", {
      message,
      temperature,
      max_tokens: maxTokens
    });
  },

  // PDF extraction endpoints
  async uploadPDF(formData) {
    // GPT-4.1 is now fixed in the backend
    const endpoint = `/api/pdf/upload`;
    return uploadRequest(endpoint, formData);
  },

  // Excel/CSV extraction endpoints
  async uploadExcel(formData) {
    // GPT-4.1 is now fixed in the backend
    const endpoint = `/api/excel/upload`;
    return uploadRequest(endpoint, formData);
  },

  async extractFromBase64(fileContent, filename, extractionModel = "anthropic", temperature = 0.1, maxTokens = 2000) {
    return request("/api/pdf/extract", "POST", {
      file_content: fileContent,
      filename,
      extraction_model: extractionModel,
      temperature,
      max_tokens: maxTokens
    });
  },

  // RAG endpoints (Tire Discounts Knowledge Base)
  async ragUploadDocument(formData) {
    const endpoint = `/api/documents/upload`;
    return uploadRequest(endpoint, formData);
  },

  async ragAskQuestion(question) {
    return request("/api/chat/ask", "POST", {
      question
    });
  },

  async ragGetStats() {
    return request("/api/stats");
  },

  async ragListDocuments() {
    return request("/api/documents/list");
  },

  async ragDownloadDocument(filename) {
    const response = await fetch(`${API_BASE_URL}/api/documents/download/${encodeURIComponent(filename)}`, {
      method: "GET",
      headers: {
        "X-API-Key": API_KEY
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.blob();
  },

  async ragClearDatabase() {
    return request("/api/database/clear", "DELETE");
  },

  // Aeropuertos API - nuevas funciones
  async askQuestion(question) {
    // POST /ask { question }
    return request("/ask", "POST", { question });
  },

  async getWeather(ciudad, fecha) {
    // POST /weather { ciudad, fecha(YYYY-MM-DD) }
    return request("/weather", "POST", { ciudad, fecha });
  },

  async listDocuments() {
    // GET /documents/list
    return request("/documents/list");
  },

  async downloadDocument(filename) {
    // GET /documents/download/{filename}
    const response = await fetch(`${API_BASE_URL}/documents/download/${encodeURIComponent(filename)}`, {
      method: "GET",
      headers: {
        "X-API-Key": API_KEY
      }
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.blob();
  },

  async uploadDocument(formData) {
    // POST /upload (multipart)
    return uploadRequest("/upload", formData);
  },

  async clearAll() {
    // DELETE /clear_all
    return request("/clear_all", "DELETE");
  },

  async consultarHistorico(fechaInicio, fechaFin, limite = 1000) {
    // POST /historico { fecha_inicio, fecha_fin, limite }
    return request("/historico", "POST", {
      fecha_inicio: fechaInicio,
      fecha_fin: fechaFin,
      limite
    });
  },

  // MARWIS - Station Data
  async getStationData() {
    // GET /station-data
    return request("/station-data");
  },

  async refreshStationData() {
    // POST /station-data/refresh
    return request("/station-data/refresh", "POST", {});
  },

  async generarAvisos(condiciones) {
    // POST /generar-avisos
    return request("/generar-avisos", "POST", condiciones);
  },

  async getSimulacion(escenario) {
    // GET /simulacion/{escenario}
    return request(`/simulacion/${escenario}`);
  },

  // SAP Integration Suite
  async enviarAvisoISuite(aviso) {
    // POST /enviar-aviso-isuite { aviso }
    return request("/enviar-aviso-isuite", "POST", { aviso });
  },

  async getISuiteStatus() {
    // GET /isuite/status
    return request("/isuite/status");
  }
};

// Exportar función individual para compatibilidad
export async function consultarHistorico(fechaInicio, fechaFin, limite = 1000) {
  return apiService.consultarHistorico(fechaInicio, fechaFin, limite);
}
