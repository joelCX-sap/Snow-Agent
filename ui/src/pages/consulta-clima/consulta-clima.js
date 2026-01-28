import "@ui5/webcomponents/dist/Input.js";
import "@ui5/webcomponents/dist/Label.js";
import "@ui5/webcomponents/dist/Button.js";
import "@ui5/webcomponents/dist/MessageStrip.js";
import "@ui5/webcomponents/dist/Title.js";
import "@ui5/webcomponents/dist/Text.js";
import "@ui5/webcomponents/dist/Card.js";
import "@ui5/webcomponents/dist/CardHeader.js";
import "@ui5/webcomponents/dist/BusyIndicator.js";
import "@ui5/webcomponents/dist/Select.js";
import "@ui5/webcomponents/dist/Option.js";
import "@ui5/webcomponents/dist/List.js";
import "@ui5/webcomponents/dist/Popover.js";
import "@ui5/webcomponents/dist/Switch.js";
import "@ui5/webcomponents/dist/RadioButton.js";

import { apiService } from "../../services/api.js";

// Variable global para almacenar datos de avisos
let avisosData = null;
let avisoSeleccionado = null;
let modoSimulacion = false;

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

function formatClimaResumen(cond, datosClima = null) {
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
  
  // Obtener metadata de Open-Meteo si está disponible
  let metadataStr = "";
  if (datosClima && datosClima.openmeteo_metadata) {
    const meta = datosClima.openmeteo_metadata;
    metadataStr = `\n\n📍 Coordenadas: ${meta.coordinates || "N/A"}\n🏔️ Elevación: ${meta.elevation || "N/A"} m\n🌐 Zona horaria: ${meta.timezone || "N/A"}`;
  }

  return [
    `📍 Ubicación: ${ubicacion}`,
    `📅 Fecha: ${fecha}`,
    `🌤️ Condición actual: ${condicion}`,
    `🌡️ Temperatura actual: ${temp} °C`,
    `💧 Humedad: ${humedad}%`,
    `💨 Viento: ${viento} km/h (máx pronóstico: ${vmax} km/h)`,
    `👁️ Visibilidad: ${visibilidad} km`,
    `🌧️ Precipitación actual: ${precipitacion} mm`,
    `📊 Pronóstico del día -> Máx: ${tmax} °C, Mín: ${tmin} °C`,
    `   Prob. lluvia: ${plluvia}%, Prob. nieve: ${pnieve}%`,
    metadataStr
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

/**
 * Renderiza los indicadores de probabilidad de lluvia y nieve
 * @param {number} probLluvia - Probabilidad de lluvia (0-100)
 * @param {number} probNieve - Probabilidad de nieve (0-100)
 */
function renderProbabilidades(probLluvia, probNieve) {
  const container = document.getElementById("probabilidadesContainer");
  const probLluviaValor = document.getElementById("probLluviaValor");
  const probLluviaDesc = document.getElementById("probLluviaDesc");
  const probLluviaCard = document.getElementById("probLluviaCard");
  const probNieveValor = document.getElementById("probNieveValor");
  const probNieveDesc = document.getElementById("probNieveDesc");
  const probNieveCard = document.getElementById("probNieveCard");
  
  if (!container) return;
  
  // Mostrar el contenedor
  container.style.display = "grid";
  
  // Actualizar probabilidad de lluvia
  if (probLluviaValor) {
    probLluviaValor.textContent = `${probLluvia}%`;
  }
  if (probLluviaDesc) {
    if (probLluvia >= 70) {
      probLluviaDesc.textContent = "Alta probabilidad";
    } else if (probLluvia >= 40) {
      probLluviaDesc.textContent = "Probabilidad moderada";
    } else if (probLluvia > 0) {
      probLluviaDesc.textContent = "Baja probabilidad";
    } else {
      probLluviaDesc.textContent = "Sin probabilidad";
    }
  }
  // Cambiar color según nivel de probabilidad
  if (probLluviaCard) {
    if (probLluvia >= 70) {
      probLluviaCard.style.background = "linear-gradient(135deg, #bbdefb 0%, #64b5f6 100%)";
      probLluviaCard.style.borderColor = "#42a5f5";
    } else if (probLluvia >= 40) {
      probLluviaCard.style.background = "linear-gradient(135deg, #e3f2fd 0%, #90caf9 100%)";
      probLluviaCard.style.borderColor = "#64b5f6";
    }
  }
  
  // Actualizar probabilidad de nieve
  if (probNieveValor) {
    probNieveValor.textContent = `${probNieve}%`;
  }
  if (probNieveDesc) {
    if (probNieve >= 70) {
      probNieveDesc.textContent = "Alta probabilidad";
    } else if (probNieve >= 40) {
      probNieveDesc.textContent = "Probabilidad moderada";
    } else if (probNieve > 0) {
      probNieveDesc.textContent = "Baja probabilidad";
    } else {
      probNieveDesc.textContent = "Sin probabilidad";
    }
  }
  // Cambiar color según nivel de probabilidad
  if (probNieveCard) {
    if (probNieve >= 70) {
      probNieveCard.style.background = "linear-gradient(135deg, #c5cae9 0%, #7986cb 100%)";
      probNieveCard.style.borderColor = "#5c6bc0";
    } else if (probNieve >= 40) {
      probNieveCard.style.background = "linear-gradient(135deg, #e8eaf6 0%, #9fa8da 100%)";
      probNieveCard.style.borderColor = "#7986cb";
    }
  }
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

function renderAvisos(avisos) {
  const avisosCard = document.getElementById("avisosCard");
  const avisosLista = document.getElementById("avisosLista");
  
  if (!avisosCard || !avisosLista) {
    console.error("❌ Elementos avisosCard o avisosLista no encontrados");
    return;
  }
  
  console.log("📋 renderAvisos llamado con:", avisos);
  
  // Limpiar lista
  avisosLista.innerHTML = "";
  avisoSeleccionado = null;
  
  const avisosGenerados = avisos.avisos_generados || [];
  
  if (avisosGenerados.length === 0) {
    avisosCard.style.display = "none";
    return;
  }
  
  avisosCard.style.display = "block";
  
  // Crear items de la lista
  avisosGenerados.forEach((aviso, index) => {
    const item = document.createElement("ui5-li");
    item.textContent = `${aviso.nombre} (${aviso.tipo})`;
    item.description = `Prioridad: ${aviso.prioridad} | ${aviso.clase}`;
    item.dataset.avisoIndex = index;
    avisosLista.appendChild(item);
  });
  
  // Seleccionar automáticamente el primer aviso y mostrar detalle
  const primerItem = avisosLista.querySelector("ui5-li");
  if (primerItem) {
    primerItem.selected = true;
    avisoSeleccionado = avisosGenerados[0];
    mostrarDetalleAviso(avisoSeleccionado, avisos);
  }
  
  // Event listener para selección
  const handleSelection = (e) => {
    console.log("Selección detectada:", e.detail);
    const selectedItem = e.detail.selectedItems[0];
    if (selectedItem) {
      const index = parseInt(selectedItem.dataset.avisoIndex);
      avisoSeleccionado = avisosGenerados[index];
      mostrarDetalleAviso(avisoSeleccionado, avisos);
      console.log("Aviso seleccionado:", avisoSeleccionado);
    } else {
      ocultarDetalleAviso();
      avisoSeleccionado = null;
    }
  };
  
  // Remover listener anterior si existe
  avisosLista.removeEventListener("selection-change", handleSelection);
  // Agregar nuevo listener
  avisosLista.addEventListener("selection-change", handleSelection);
}

function mostrarDetalleAviso(aviso, avisosCompletos) {
  const detalleSection = document.getElementById("avisoDetalleSection");
  const codigosSAPTexto = document.getElementById("codigosSAPTexto");
  const tareasTexto = document.getElementById("tareasTexto");
  
  if (!detalleSection || !codigosSAPTexto || !tareasTexto) return;
  
  // Mostrar sección
  detalleSection.style.display = "block";
  
  // Generar texto con códigos SAP en el formato requerido
  let textoSAP = `Clase de aviso QMART= ${aviso.QMART || "N/A"}\n`;
  textoSAP += `Descripción QMTXT = ${aviso.QMTXT || aviso.nombre}\n`;
  textoSAP += `Ubic TPLNR=${aviso.TPLNR || "N/A"}\n`;
  textoSAP += `Centro de emplazamiento SWERK = ${aviso.SWERK || "N/A"}\n`;
  textoSAP += `Grupo planificado INGRP=${aviso.INGRP || "N/A"}\n`;
  textoSAP += `Puesto de trabajo GEWRK=${aviso.GEWRK || "N/A"}\n`;
  textoSAP += `Prioridad PRIOK=${aviso.PRIOK || aviso.prioridad || "N/A"}\n`;
  textoSAP += `Grupo modo de fallo QMGRP=${aviso.QMGRP || "N/A"}\n`;
  textoSAP += `Modo de fallo QMCOD= ${aviso.QMCOD || "N/A"}`;
  
  codigosSAPTexto.textContent = textoSAP;
  
  // Generar texto con tareas del procedimiento
  const tareas = aviso.tareas_procedimiento || [];
  let textoTareas = "";
  tareas.forEach((tarea, idx) => {
    textoTareas += `${idx + 1}. ${tarea}\n`;
  });
  
  if (textoTareas === "") {
    textoTareas = "No hay tareas definidas para este aviso.";
  }
  
  tareasTexto.textContent = textoTareas;
  
  // Crear/actualizar sección "Resumen del Aviso"
  let resumenContainer = document.getElementById("resumenAvisoTexto");
  if (!resumenContainer) {
    const tituloResumen = document.createElement("ui5-title");
    tituloResumen.level = "H5";
    tituloResumen.style.marginTop = "0.5rem";
    tituloResumen.textContent = "Resumen del Aviso";
    resumenContainer = document.createElement("div");
    resumenContainer.id = "resumenAvisoTexto";
    resumenContainer.style.padding = "1rem";
    resumenContainer.style.backgroundColor = "var(--sapGroup_ContentBackground)";
    resumenContainer.style.borderRadius = "0.25rem";
    resumenContainer.style.fontFamily = "monospace";
    resumenContainer.style.fontSize = "0.875rem";
    resumenContainer.style.whiteSpace = "pre-wrap";
    detalleSection.appendChild(tituloResumen);
    detalleSection.appendChild(resumenContainer);
  }
  
  const condiciones = avisosCompletos.condiciones_evaluadas || {};
  const marwisData = avisosCompletos.datos_marwis;
  let textoResumen = `AVISO: ${aviso.nombre} (${aviso.tipo})\n`;
  textoResumen += `Fecha: ${aviso.fecha_generacion}\n`;
  textoResumen += `\n${"=".repeat(70)}\n`;
  textoResumen += `CONDICIONES METEOROLÓGICAS:\n`;
  textoResumen += `${"=".repeat(70)}\n\n`;
  textoResumen += `- Temperatura: ${condiciones.temperatura_actual || "N/A"}°C\n`;
  textoResumen += `- Humedad: ${condiciones.humedad || "N/A"}%\n`;
  textoResumen += `- Viento: ${condiciones.viento || "N/A"} km/h\n`;
  textoResumen += `- Visibilidad: ${condiciones.visibilidad || "N/A"} km\n`;
  if (marwisData && marwisData.measurements) {
    textoResumen += `\n${"=".repeat(70)}\n`;
    textoResumen += `DATOS MARWIS (PISTA):\n`;
    textoResumen += `${"=".repeat(70)}\n\n`;
    marwisData.measurements.slice(0, 5).forEach(sensor => {
      textoResumen += `- ${sensor.SensorChannelName || "Sensor"}: ${sensor.Value || "N/A"} ${sensor.SensorChannelUnit || ""}\n`;
    });
  }
  resumenContainer.textContent = textoResumen;
}

function ocultarDetalleAviso() {
  const detalleSection = document.getElementById("avisoDetalleSection");
  if (detalleSection) {
    detalleSection.style.display = "none";
  }
}

function renderPopoverDetalle(aviso, avisosCompletos) {
  if (!aviso) return;
  
  // Información del Aviso con códigos SAP
  const avisoInfoLista = document.getElementById("avisoInfoLista");
  avisoInfoLista.innerHTML = "";
  const infoItems = [
    { label: "Tipo", value: aviso.tipo },
    { label: "Nombre", value: aviso.nombre },
    { label: "Clase de aviso (QMART)", value: aviso.QMART || "N/A" },
    { label: "Descripción (QMTXT)", value: aviso.QMTXT || aviso.nombre },
    { label: "Ubicación (TPLNR)", value: aviso.TPLNR || "N/A" },
    { label: "Centro emplazamiento (SWERK)", value: aviso.SWERK || "N/A" },
    { label: "Grupo planificador (INGRP)", value: aviso.INGRP || "N/A" },
    { label: "Puesto trabajo (GEWRK)", value: aviso.GEWRK || "N/A" },
    { label: "Prioridad (PRIOK)", value: aviso.PRIOK || aviso.prioridad || "N/A" },
    { label: "Grupo modo fallo (QMGRP)", value: aviso.QMGRP || "N/A" },
    { label: "Modo de fallo (QMCOD)", value: aviso.QMCOD || "N/A" },
    { label: "Fecha Generación", value: aviso.fecha_generacion }
  ];
  infoItems.forEach(item => {
    const li = document.createElement("ui5-li");
    li.textContent = item.label;
    li.description = item.value || "N/A";
    avisoInfoLista.appendChild(li);
  });
  
  // Condiciones Meteorológicas
  const condMeteoLista = document.getElementById("condicionesMeteoLista");
  condMeteoLista.innerHTML = "";
  const condiciones = avisosCompletos.condiciones_evaluadas || {};
  const condItems = [
    { label: "Temperatura", value: `${condiciones.temperatura_actual || "N/A"}°C` },
    { label: "Humedad", value: `${condiciones.humedad || "N/A"}%` },
    { label: "Viento", value: `${condiciones.viento || "N/A"} km/h` },
    { label: "Visibilidad", value: `${condiciones.visibilidad || "N/A"} km` }
  ];
  condItems.forEach(item => {
    const li = document.createElement("ui5-li");
    li.textContent = item.label;
    li.description = item.value;
    condMeteoLista.appendChild(li);
  });
  
  // Datos MARWIS
  const marwisLista = document.getElementById("marwisLista");
  marwisLista.innerHTML = "";
  const marwisData = avisosCompletos.datos_marwis;
  if (marwisData && marwisData.measurements) {
    marwisData.measurements.slice(0, 5).forEach(sensor => {
      const li = document.createElement("ui5-li");
      li.textContent = sensor.SensorChannelName || "Sensor";
      li.description = `${sensor.Value || "N/A"} ${sensor.SensorChannelUnit || ""}`;
      marwisLista.appendChild(li);
    });
  }
  
  // Tareas del Procedimiento
  const tareasProcLista = document.getElementById("tareasProcedimientoLista");
  tareasProcLista.innerHTML = "";
  const tareas = aviso.tareas_procedimiento || [];
  tareas.forEach(tarea => {
    const li = document.createElement("ui5-li");
    li.textContent = tarea;
    li.icon = "task";
    tareasProcLista.appendChild(li);
  });
  
  // Resumen Completo de Tareas en Texto con Códigos SAP
  const resumenTexto = document.getElementById("resumenTareasTexto");
  if (resumenTexto) {
    let textoCompleto = `AVISO: ${aviso.nombre} (${aviso.tipo})\n`;
    textoCompleto += `Fecha: ${aviso.fecha_generacion}\n`;
    textoCompleto += `\n${"=".repeat(70)}\n`;
    textoCompleto += `CÓDIGOS SAP:\n`;
    textoCompleto += `${"=".repeat(70)}\n\n`;
    textoCompleto += `Clase de aviso (QMART)            = ${aviso.QMART || "N/A"}\n`;
    textoCompleto += `Descripción (QMTXT)               = ${aviso.QMTXT || aviso.nombre}\n`;
    textoCompleto += `Ubicación (TPLNR)                 = ${aviso.TPLNR || "N/A"}\n`;
    textoCompleto += `Centro de emplazamiento (SWERK)   = ${aviso.SWERK || "N/A"}\n`;
    textoCompleto += `Grupo planificador (INGRP)        = ${aviso.INGRP || "N/A"}\n`;
    textoCompleto += `Puesto de trabajo (GEWRK)         = ${aviso.GEWRK || "N/A"}\n`;
    textoCompleto += `Prioridad (PRIOK)                 = ${aviso.PRIOK || aviso.prioridad || "N/A"}\n`;
    textoCompleto += `Grupo modo de fallo (QMGRP)       = ${aviso.QMGRP || "N/A"}\n`;
    textoCompleto += `Modo de fallo (QMCOD)             = ${aviso.QMCOD || "N/A"}\n`;
    
    textoCompleto += `\n${"=".repeat(70)}\n`;
    textoCompleto += `TAREAS A REALIZAR SEGÚN PROCEDIMIENTO:\n`;
    textoCompleto += `${"=".repeat(70)}\n\n`;
    
    tareas.forEach((tarea, idx) => {
      textoCompleto += `${idx + 1}. ${tarea}\n`;
    });
    
    textoCompleto += `\n${"=".repeat(70)}\n`;
    textoCompleto += `CONDICIONES METEOROLÓGICAS:\n`;
    textoCompleto += `${"=".repeat(70)}\n\n`;
    textoCompleto += `- Temperatura: ${condiciones.temperatura_actual || "N/A"}°C\n`;
    textoCompleto += `- Humedad: ${condiciones.humedad || "N/A"}%\n`;
    textoCompleto += `- Viento: ${condiciones.viento || "N/A"} km/h\n`;
    textoCompleto += `- Visibilidad: ${condiciones.visibilidad || "N/A"} km\n`;
    
    if (marwisData && marwisData.measurements) {
      textoCompleto += `\n${"=".repeat(70)}\n`;
      textoCompleto += `DATOS MARWIS (PISTA):\n`;
      textoCompleto += `${"=".repeat(70)}\n\n`;
      marwisData.measurements.slice(0, 5).forEach(sensor => {
        textoCompleto += `- ${sensor.SensorChannelName || "Sensor"}: ${sensor.Value || "N/A"} ${sensor.SensorChannelUnit || ""}\n`;
      });
    }
    
    resumenTexto.textContent = textoCompleto;
  }
}

async function descargarAvisoJSON() {
  if (!avisosData) return;
  
  const dataStr = JSON.stringify(avisosData, null, 2);
  const blob = new Blob([dataStr], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `aviso_${avisosData.fecha_evaluacion || new Date().toISOString()}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

/**
 * Renderiza el forecast de las próximas horas (hora actual + 3 horas)
 * @param {Array} forecastHoras - Array de objetos con datos por hora
 */
function renderForecastHoras(forecastHoras) {
  const card = document.getElementById("forecastHorasCard");
  const container = document.getElementById("forecastHorasContainer");
  
  if (!card || !container) {
    console.warn("Elementos de forecast no encontrados");
    return;
  }
  
  // Limpiar contenedor
  container.innerHTML = "";
  
  if (!forecastHoras || forecastHoras.length === 0) {
    card.style.display = "none";
    return;
  }
  
  // Mostrar card
  card.style.display = "block";
  
  // Crear tarjetas para cada hora
  forecastHoras.forEach((hora, index) => {
    const horaCard = document.createElement("div");
    horaCard.style.cssText = `
      padding: 1rem;
      background-color: var(--sapGroup_ContentBackground);
      border: 1px solid var(--sapGroup_BorderColor);
      border-radius: 0.5rem;
      text-align: center;
    `;
    
    // Determinar icono según condiciones
    let icono = "🌤️";
    if (hora.snowfall > 0) icono = "❄️";
    else if (hora.rain > 0 || hora.precipitation > 0.1) icono = "🌧️";
    else if (hora.cloud_cover >= 80) icono = "☁️";
    else if (hora.cloud_cover >= 50) icono = "⛅";
    else if (hora.cloud_cover < 20) icono = "☀️";
    
    // Determinar color de temperatura
    let tempColor = "var(--sapTextColor)";
    if (hora.temperature_2m < 0) tempColor = "#0066cc";
    else if (hora.temperature_2m > 25) tempColor = "#cc3300";
    
    // Indicador de hora actual
    const esHoraActual = index === 0;
    const etiquetaHora = esHoraActual ? `${hora.hora} (Actual)` : hora.hora;
    
    horaCard.innerHTML = `
      <div style="font-size: 2rem; margin-bottom: 0.5rem;">${icono}</div>
      <div style="font-weight: bold; margin-bottom: 0.25rem; ${esHoraActual ? 'color: var(--sapBrandColor);' : ''}">${etiquetaHora}</div>
      <div style="font-size: 1.5rem; font-weight: bold; color: ${tempColor}; margin-bottom: 0.5rem;">${hora.temperature_2m}°C</div>
      <div style="font-size: 0.875rem; color: var(--sapTextColor);">
        <div>💧 ${hora.relative_humidity_2m}%</div>
        <div>💨 ${hora.wind_speed_10m} km/h</div>
        <div>☁️ ${hora.cloud_cover}%</div>
        ${hora.precipitation > 0 ? `<div>🌧️ ${hora.precipitation} mm</div>` : ''}
        ${hora.snowfall > 0 ? `<div>❄️ ${hora.snowfall} cm</div>` : ''}
        <div>👁️ ${(hora.visibility / 1000).toFixed(1)} km</div>
      </div>
    `;
    
    container.appendChild(horaCard);
  });
}

export default function init() {
  const citySelect = document.getElementById("citySelect");
  const dateInput = document.getElementById("dateInput");
  const weatherButton = document.getElementById("weatherButton");
  const weatherMessage = document.getElementById("weatherMessage");

  const climaResumen = document.getElementById("climaResumen");
  const condicionesAdversas = document.getElementById("condicionesAdversas");
  const llmAnswer = document.getElementById("llmAnswer");
  const fuentesList = document.getElementById("fuentesList");
  const workflowInfo = document.getElementById("workflowInfo");
  
  const verDetalleBtn = document.getElementById("verDetalleAvisoBtn");
  const avisoPopover = document.getElementById("avisoDetallePopover");
  const descargarBtn = document.getElementById("descargarAvisoJson");
  const cerrarBtn = document.getElementById("cerrarPopover");

  if (!citySelect || !dateInput || !weatherButton) {
    console.warn("Elementos de la página Consulta Clima no encontrados");
    return;
  }

  // Pre-cargar fecha de hoy en formato YYYY-MM-DD
  dateInput.value = todayISO();
  
  // Configuración del modo simulación
  const simulacionToggle = document.getElementById("simulacionToggle");
  const simulacionPanel = document.getElementById("simulacionPanel");
  
  if (simulacionToggle && simulacionPanel) {
    simulacionToggle.addEventListener("change", (e) => {
      modoSimulacion = e.target.checked;
      simulacionPanel.style.display = modoSimulacion ? "block" : "none";
      
      if (modoSimulacion) {
        showMessage(weatherMessage, "Modo Simulación activado. Los datos serán generados sintéticamente.", "Information");
        setTimeout(() => hideMessage(weatherMessage), 3000);
      }
    });
  }
  
  // Event listeners para avisos
  if (verDetalleBtn && avisoPopover) {
    verDetalleBtn.addEventListener("click", () => {
      if (avisoSeleccionado && avisosData) {
        renderPopoverDetalle(avisoSeleccionado, avisosData);
        avisoPopover.showAt(verDetalleBtn);
      }
    });
  }
  
  if (descargarBtn) {
    console.log("✅ Botón de descarga JSON encontrado:", descargarBtn);
    descargarBtn.addEventListener("click", () => {
      console.log("🔽 Click en descargar JSON detectado");
      descargarAvisoJSON();
    });
  } else {
    console.error("❌ Botón de descarga JSON NO encontrado");
  }
  
  if (cerrarBtn && avisoPopover) {
    cerrarBtn.addEventListener("click", () => avisoPopover.close());
  }
  
  // Botón de descarga JSON en la nueva sección
  const descargarBtnNuevo = document.getElementById("descargarAvisoJsonBtn");
  if (descargarBtnNuevo) {
    console.log("✅ Botón de descarga JSON (nuevo) encontrado:", descargarBtnNuevo);
    descargarBtnNuevo.addEventListener("click", () => {
      console.log("🔽 Click en descargar JSON (nuevo) detectado");
      descargarAvisoJSON();
    });
  } else {
    console.error("❌ Botón de descarga JSON (nuevo) NO encontrado");
  }

  const consultar = async () => {
    // Obtener el valor seleccionado del dropdown
    const selectedOption = citySelect.selectedOption;
    const ciudad = selectedOption ? selectedOption.value : "riogrande";
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
      let result;
      
      // Modo Simulación
      if (modoSimulacion) {
        // Obtener escenario seleccionado del dropdown
        const escenarioSelect = document.getElementById('escenarioSelect');
        const selectedOption = escenarioSelect ? escenarioSelect.selectedOption : null;
        const escenario = selectedOption ? selectedOption.value : 'nieve';
        
        showMessage(weatherMessage, `Modo Simulación: Escenario "${escenario}"`, "Information");
        result = await apiService.getSimulacion(escenario);
      } else {
        // Modo Normal
        result = await apiService.getWeather(ciudad, fecha);
      }

      if (!result || result.success === false) {
        const errMsg = (result && result.message) ? result.message : "Error obteniendo datos del clima";
        showMessage(weatherMessage, errMsg, "Negative");
        return;
      }

      const data = result.resultado || {};
      const analisis = data.condiciones_analizadas || null;
      const datosClima = data.datos_clima || null;

      // Resumen del clima (con metadata de Open-Meteo)
      climaResumen.textContent = formatClimaResumen(analisis, datosClima);
      renderCondicionesAdversas(condicionesAdversas, analisis ? analisis.condiciones_adversas : []);
      
      // Renderizar probabilidades de lluvia y nieve
      const pronostico = analisis ? analisis.pronostico : {};
      const probLluvia = pronostico.prob_lluvia ?? 0;
      const probNieve = pronostico.prob_nieve ?? 0;
      renderProbabilidades(probLluvia, probNieve);
      
      // Renderizar forecast de próximas horas (hora actual + 3 horas)
      if (datosClima && datosClima.forecast_proximas_horas) {
        console.log("📊 Forecast próximas horas:", datosClima.forecast_proximas_horas);
        renderForecastHoras(datosClima.forecast_proximas_horas);
      } else {
        // Ocultar card si no hay datos
        const forecastCard = document.getElementById("forecastHorasCard");
        if (forecastCard) {
          forecastCard.style.display = "none";
        }
      }

      // Respuesta LLM y fuentes
      llmAnswer.textContent = data.respuesta_llm || "Sin respuesta generada.";
      renderFuentes(fuentesList, data.fuentes || []);

      // Info de workflow
      renderWorkflowInfo(workflowInfo, data.workflow_info || null);
      
      // Generar avisos solo si hay condiciones adversas críticas
      const condicionesAdversasArray = analisis ? analisis.condiciones_adversas : [];
      if (condicionesAdversasArray && condicionesAdversasArray.length > 0 && analisis) {
        try {
          const avisosResult = await apiService.generarAvisos(analisis);
          if (avisosResult && avisosResult.success) {
            avisosData = avisosResult.avisos;
            // Solo renderizar si realmente se generaron avisos
            if (avisosData && avisosData.avisos_generados && avisosData.avisos_generados.length > 0) {
              console.log(`✅ ${avisosData.avisos_generados.length} aviso(s) generado(s)`);
              console.log("Avisos a renderizar:", avisosData.avisos_generados);
              renderAvisos(avisosData);
              console.log("✅ Card de avisos renderizada");
              const cardFinal = document.getElementById("avisosCard");
              console.log("Estado final de avisosCard:", cardFinal ? cardFinal.style.display : "NO EXISTE");
            } else {
              console.log("ℹ️ No se generaron avisos (condiciones no cumplen umbrales específicos)");
              // Ocultar card de avisos si no hay ninguno
              const avisosCard = document.getElementById("avisosCard");
              if (avisosCard) {
                avisosCard.style.display = "none";
              }
            }
          }
        } catch (errAvisos) {
          console.error("Error generando avisos:", errAvisos);
        }
      } else {
        console.log("ℹ️ Sin condiciones adversas detectadas - No se generan avisos");
        // Ocultar card de avisos
        const avisosCard = document.getElementById("avisosCard");
        if (avisosCard) {
          avisosCard.style.display = "none";
        }
      }

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
