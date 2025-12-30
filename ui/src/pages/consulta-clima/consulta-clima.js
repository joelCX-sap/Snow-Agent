import "@ui5/webcomponents/dist/Input.js";
import "@ui5/webcomponents/dist/Label.js";
import "@ui5/webcomponents/dist/Button.js";
import "@ui5/webcomponents/dist/MessageStrip.js";
import "@ui5/webcomponents/dist/Title.js";
import "@ui5/webcomponents/dist/Text.js";
import "@ui5/webcomponents/dist/Card.js";
import "@ui5/webcomponents/dist/CardHeader.js";
import "@ui5/webcomponents/dist/BusyIndicator.js";

import { apiService } from "../../services/api.js";

function setBusy(button, busy = true) {
  button.disabled = busy;
  if (busy) {
    button.setAttribute("loading", "");
  } else {
    button.removeAttribute("loading");
  }
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

function setGlobalBusy(isBusy) {
  const el = document.getElementById("pageBusy");
  if (!el) return;
  // Mostrar como grid para centrar el spinner y ocultar cuando no esté activo
  el.style.display = isBusy ? "grid" : "none";
  try {
    if (isBusy) {
      el.setAttribute("active", "");
    } else {
      el.removeAttribute("active");
    }
  } catch {}
}

function todayISO() {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

function formatClimaResumen(cond) {
  if (!cond || typeof cond !== "object") return "Sin datos del clima.";
  const ubicacion = cond.ubicacion || "";
  const fecha = cond.fecha || todayISO();
  const temp = cond.temperatura_actual ?? "N/A";
  const condicion = cond.condicion_actual || "N/A";
  const viento = cond.viento ?? "N/A";
  const visibilidad = cond.visibilidad ?? "N/A";
  const humedad = cond.humedad ?? "N/A";
  const precipitacion = cond.precipitacion ?? "N/A";

  const pr = cond.pronostico || {};
  const tmax = pr.temp_max ?? "N/A";
  const tmin = pr.temp_min ?? "N/A";
  const plluvia = pr.prob_lluvia ?? "N/A";
  const pnieve = pr.prob_nieve ?? "N/A";
  const vmax = pr.viento_max ?? "N/A";

  return [
    `Ubicación: ${ubicacion}`,
    `Fecha: ${fecha}`,
    `Condición actual: ${condicion}`,
    `Temperatura actual: ${temp} °C`,
    `Humedad: ${humedad}%`,
    `Viento: ${viento} km/h (máx pronóstico: ${vmax} km/h)`,
    `Visibilidad: ${visibilidad} km`,
    `Precipitación actual: ${precipitacion} mm`,
    `Pronóstico del día -> Máx: ${tmax} °C, Mín: ${tmin} °C, Prob. lluvia: ${plluvia}%, Prob. nieve: ${pnieve}%`
  ].join("\n");
}

function renderCondicionesAdversas(container, condiciones) {
  if (!container) return;
  container.innerHTML = "";
  const list = Array.isArray(condiciones) ? condiciones : [];

  if (list.length === 0) {
    container.innerHTML = `<ui5-message-strip design="Information" hide-close-button>Sin condiciones adversas detectadas.</ui5-message-strip>`;
    return;
  }

  const ul = document.createElement("ul");
  ul.style.margin = "0";
  ul.style.paddingLeft = "1rem";
  list.forEach((c) => {
    const li = document.createElement("li");
    li.textContent = c;
    ul.appendChild(li);
  });
  container.appendChild(ul);
}

function renderFuentes(container, fuentes) {
  if (!container) return;
  container.innerHTML = "";

  const list = Array.isArray(fuentes) ? fuentes : [];
  if (list.length === 0) {
    container.innerHTML = "<ui5-text>No se recibieron fuentes.</ui5-text>";
    return;
  }

  const ul = document.createElement("ul");
  ul.style.margin = "0";
  ul.style.paddingLeft = "1rem";

  list.forEach((src) => {
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
    ul.appendChild(li);
  });

  container.appendChild(ul);
}

function renderWorkflowInfo(container, info) {
  if (!container) return;
  container.textContent = "";

  if (!info) {
    container.innerHTML = "<ui5-text>No hay información de workflow.</ui5-text>";
    return;
  }
  try {
    container.textContent = JSON.stringify(info, null, 2);
  } catch {
    container.textContent = String(info);
  }
}

export default function init() {
  const cityInput = document.getElementById("cityInput");
  const dateInput = document.getElementById("dateInput");
  const weatherButton = document.getElementById("weatherButton");
  const weatherMessage = document.getElementById("weatherMessage");

  const climaResumen = document.getElementById("climaResumen");
  const condicionesAdversas = document.getElementById("condicionesAdversas");
  const llmAnswer = document.getElementById("llmAnswer");
  const fuentesList = document.getElementById("fuentesList");
  const workflowInfo = document.getElementById("workflowInfo");

  if (!cityInput || !dateInput || !weatherButton) {
    console.warn("Elementos de la página Consulta Clima no encontrados");
    return;
  }

  // Pre-cargar fecha de hoy en formato YYYY-MM-DD
  dateInput.value = todayISO();

  const consultar = async () => {
    const ciudad = (cityInput.value || "").trim() || "rio grande";
    const fecha = (dateInput.value || "").trim();

    if (!fecha || !/^\d{4}-\d{2}-\d{2}$/.test(fecha)) {
      showMessage(weatherMessage, "Ingrese una fecha válida (YYYY-MM-DD).", "Negative");
      return;
    }

    hideMessage(weatherMessage);
    setBusy(weatherButton, true);
    setGlobalBusy(true);
    showMessage(weatherMessage, "Consultando clima y procedimientos...", "Information");

    // Limpiar salidas previas
    climaResumen.textContent = "";
    condicionesAdversas.innerHTML = "";
    llmAnswer.textContent = "";
    fuentesList.innerHTML = "";
    workflowInfo.textContent = "";

    try {
      const result = await apiService.getWeather(ciudad, fecha);

      if (!result || result.success === false) {
        const errMsg = (result && result.message) ? result.message : "Error obteniendo datos del clima";
        showMessage(weatherMessage, errMsg, "Negative");
        return;
      }

      const data = result.resultado || {};
      const analisis = data.condiciones_analizadas || null;

      // Resumen del clima
      climaResumen.textContent = formatClimaResumen(analisis);
      renderCondicionesAdversas(condicionesAdversas, analisis ? analisis.condiciones_adversas : []);

      // Respuesta LLM y fuentes
      llmAnswer.textContent = data.respuesta_llm || "Sin respuesta generada.";
      renderFuentes(fuentesList, data.fuentes || []);

      // Info de workflow
      renderWorkflowInfo(workflowInfo, data.workflow_info || null);

      showMessage(weatherMessage, "Consulta completada.", "Positive");
      
      // Mostrar notificación
      const inboxUrl = "https://xp6xzy9lzsyf9cc9.canary-eu12.process-automation.build.cloud.sap/comsapspaprocessautomation.comsapspainbox/inbox.html#/detail/NA/46a1587c-cad1-11f0-8e73-eeee0a92954d/TaskCollection(SAP__Origin='NA',InstanceID='46a1587c-cad1-11f0-8e73-eeee0a92954d')";
      if (window.showNotification) {
        window.showNotification(inboxUrl);
      }
    } catch (err) {
      console.error("Error consultando /weather:", err);
      showMessage(weatherMessage, `Error: ${err.message}`, "Negative");
    } finally {
      setBusy(weatherButton, false);
      setGlobalBusy(false);
      setTimeout(() => hideMessage(weatherMessage), 3500);
    }
  };

  weatherButton.addEventListener("click", consultar);
  dateInput.addEventListener("change", () => {
    // No-op: el valor ya se actualiza en datePicker
  });

  // Ejecutar sólo cuando el usuario lo solicite (no automático al cargar)
  // No llamar consultar() aquí.
}
