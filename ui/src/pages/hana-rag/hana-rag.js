import "@ui5/webcomponents/dist/TextArea.js";
import "@ui5/webcomponents/dist/Button.js";
import "@ui5/webcomponents/dist/MessageStrip.js";
import "@ui5/webcomponents/dist/Title.js";
import "@ui5/webcomponents/dist/Text.js";
import "@ui5/webcomponents/dist/Card.js";
import "@ui5/webcomponents/dist/CardHeader.js";

import { apiService } from "../../services/api.js";

function setBusy(button, busy = true) {
  button.disabled = busy;
  button.loading = busy;
}

function showMessage(strip, text, design = "Information") {
  if (!strip) return;
  strip.textContent = text;
  strip.design = design;
  strip.style.display = "block";
}

function hideMessage(strip) {
  if (!strip) return;
  strip.style.display = "none";
  strip.textContent = "";
}

function renderSources(container, sources) {
  if (!container) return;
  container.innerHTML = "";

  if (!Array.isArray(sources) || sources.length === 0) {
    container.innerHTML = "<ui5-text>No se recibieron fuentes.</ui5-text>";
    return;
  }

  const list = document.createElement("ul");
  list.style.margin = "0";
  list.style.paddingLeft = "1rem";

  sources.forEach((src) => {
    const li = document.createElement("li");
    const title = src.title || src.filename || "Fuente";
    const snippet = src.snippet || src.content || "";
    const path = src.path || src.url || "";

    li.innerHTML = `
      <div style="margin-bottom: 0.25rem;">
        <strong>${title}</strong>${path ? ` <small style="color: var(--sapTextColor)">${path}</small>` : ""}
      </div>
      ${snippet ? `<div style="font-size: 0.9em; color: var(--sapTextColor);">${snippet}</div>` : ""}
    `;
    list.appendChild(li);
  });

  container.appendChild(list);
}

export default function init() {
  const questionInput = document.getElementById("questionInput");
  const askButton = document.getElementById("askButton");
  const answerContainer = document.getElementById("answer");
  const sourcesContainer = document.getElementById("sources");
  const messageStrip = document.getElementById("askMessage");

  if (!questionInput || !askButton || !answerContainer || !sourcesContainer) {
    console.warn("Elementos de la página Consulta Procedimientos no encontrados");
    return;
  }

  const ask = async () => {
    const question = (questionInput.value || "").trim();
    if (!question) {
      showMessage(messageStrip, "Ingrese una pregunta.", "Negative");
      return;
    }

    hideMessage(messageStrip);
    setBusy(askButton, true);
    showMessage(messageStrip, "Consultando procedimientos...", "Information");
    answerContainer.textContent = "";
    sourcesContainer.innerHTML = "";

    try {
      const result = await apiService.askQuestion(question);

      if (!result || result.success === false) {
        const errMsg = (result && result.message) ? result.message : "Error realizando la consulta";
        showMessage(messageStrip, errMsg, "Negative");
        return;
      }

      const answer = result.answer || "Sin respuesta.";
      const sources = result.sources || [];

      answerContainer.textContent = answer;
      renderSources(sourcesContainer, sources);

      showMessage(messageStrip, "Consulta completada.", "Positive");
    } catch (err) {
      console.error("Error consultando /ask:", err);
      showMessage(messageStrip, `Error: ${err.message}`, "Negative");
    } finally {
      setBusy(askButton, false);
      setTimeout(() => hideMessage(messageStrip), 3000);
    }
  };

  askButton.addEventListener("click", ask);
  questionInput.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      ask();
    }
  });
}
