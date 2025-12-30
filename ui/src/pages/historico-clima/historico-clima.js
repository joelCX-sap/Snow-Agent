import { consultarHistorico } from '../../services/api.js';

let datosActuales = [];
let paginaActual = 1;
const registrosPorPagina = 50;

export function init() {
  console.log('Inicializando página de históricos de clima');
  
  // Cargar estilos
  loadStyles();
  
  // Configurar event listeners
  setupEventListeners();
  
  // Establecer fechas por defecto (últimos 7 días)
  setDefaultDates();
}

function loadStyles() {
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = '/src/pages/historico-clima/historico-clima.css';
  document.head.appendChild(link);
}

function setDefaultDates() {
  const fechaFin = new Date();
  const fechaInicio = new Date();
  fechaInicio.setDate(fechaInicio.getDate() - 7);
  
  const fechaInicioInput = document.getElementById('fechaInicio');
  const fechaFinInput = document.getElementById('fechaFin');
  
  if (fechaInicioInput && fechaFinInput) {
    fechaInicioInput.value = formatDate(fechaInicio);
    fechaFinInput.value = formatDate(fechaFin);
  }
}

function formatDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function setupEventListeners() {
  const btnConsultar = document.getElementById('btnConsultar');
  const btnLimpiar = document.getElementById('btnLimpiar');
  const btnExportar = document.getElementById('btnExportar');
  const form = document.getElementById('historicoForm');
  
  if (btnConsultar) {
    btnConsultar.addEventListener('click', handleConsultar);
  }
  
  if (btnLimpiar) {
    btnLimpiar.addEventListener('click', handleLimpiar);
  }
  
  if (btnExportar) {
    btnExportar.addEventListener('click', handleExportar);
  }
  
  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      handleConsultar();
    });
  }
}

async function handleConsultar() {
  const fechaInicioInput = document.getElementById('fechaInicio');
  const fechaFinInput = document.getElementById('fechaFin');
  const limiteInput = document.getElementById('limite');
  
  console.log('Inputs encontrados:', { fechaInicioInput, fechaFinInput, limiteInput });
  
  const fechaInicio = fechaInicioInput?.value;
  const fechaFin = fechaFinInput?.value;
  const limite = parseInt(limiteInput?.value) || 100;
  
  console.log('Valores obtenidos:', { fechaInicio, fechaFin, limite });
  
  // Validar campos
  if (!fechaInicio || !fechaFin) {
    mostrarError('Por favor, seleccione ambas fechas');
    return;
  }
  
  // Validar que fecha inicio sea menor que fecha fin
  if (new Date(fechaInicio) > new Date(fechaFin)) {
    mostrarError('La fecha de inicio debe ser anterior a la fecha de fin');
    return;
  }
  
  // Mostrar loading
  mostrarLoading(true);
  ocultarError();
  ocultarResultados();
  
  try {
    const resultado = await consultarHistorico(fechaInicio, fechaFin, limite);
    
    if (resultado.success && resultado.datos) {
      datosActuales = resultado.datos;
      paginaActual = 1;
      mostrarResultados(resultado);
      habilitarExportacion(true);
    } else {
      mostrarError(resultado.message || 'Error al consultar los datos históricos');
      habilitarExportacion(false);
    }
  } catch (error) {
    console.error('Error en consulta:', error);
    mostrarError('Error al consultar los datos históricos: ' + error.message);
    habilitarExportacion(false);
  } finally {
    mostrarLoading(false);
  }
}

function handleLimpiar() {
  // Limpiar formulario
  setDefaultDates();
  document.getElementById('limite').value = '100';
  
  // Ocultar resultados y errores
  ocultarResultados();
  ocultarError();
  habilitarExportacion(false);
  
  datosActuales = [];
  paginaActual = 1;
}

function handleExportar() {
  if (datosActuales.length === 0) {
    mostrarError('No hay datos para exportar');
    return;
  }
  
  try {
    // Crear CSV
    const headers = [
      'ID', 'Fecha', 'Hora', 'Temperatura', 'Temp Máx', 'Temp Mín',
      'Humedad', 'Punto Rocío', 'Velocidad Viento', 'Dirección Viento',
      'Ráfaga Viento', 'Presión', 'Lluvia', 'Radiación Solar', 'Índice UV'
    ];
    
    let csv = headers.join(',') + '\n';
    
    datosActuales.forEach(registro => {
      const fila = [
        registro.id,
        registro.fecha,
        registro.hora,
        registro.temperatura,
        registro.temp_max,
        registro.temp_min,
        registro.humedad,
        registro.punto_rocio,
        registro.velocidad_viento,
        registro.direccion_viento,
        registro.rafaga_viento,
        registro.presion,
        registro.lluvia,
        registro.radiacion_solar,
        registro.indice_uv
      ];
      csv += fila.join(',') + '\n';
    });
    
    // Descargar archivo
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    const fechaInicio = document.getElementById('fechaInicio')?.value || 'inicio';
    const fechaFin = document.getElementById('fechaFin')?.value || 'fin';
    const nombreArchivo = `historico_clima_${fechaInicio}_${fechaFin}.csv`;
    
    link.setAttribute('href', url);
    link.setAttribute('download', nombreArchivo);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
  } catch (error) {
    console.error('Error exportando:', error);
    mostrarError('Error al exportar los datos: ' + error.message);
  }
}

function mostrarResultados(resultado) {
  const container = document.getElementById('resultadosContainer');
  if (!container) return;
  
  // Mostrar estadísticas
  mostrarEstadisticas(resultado);
  
  // Mostrar tabla con paginación
  mostrarTabla();
  
  container.style.display = 'block';
}

function mostrarEstadisticas(resultado) {
  const estadisticasDiv = document.getElementById('estadisticas');
  if (!estadisticasDiv) return;
  
  // Calcular estadísticas
  const totalRegistros = resultado.total_registros || 0;
  
  let tempPromedio = 0;
  let tempMax = -Infinity;
  let tempMin = Infinity;
  
  if (datosActuales.length > 0) {
    datosActuales.forEach(registro => {
      const temp = parseFloat(registro.temperatura);
      if (!isNaN(temp)) {
        tempPromedio += temp;
        tempMax = Math.max(tempMax, temp);
        tempMin = Math.min(tempMin, temp);
      }
    });
    tempPromedio = (tempPromedio / datosActuales.length).toFixed(1);
  }
  
  estadisticasDiv.innerHTML = `
    <div style="background: var(--sapTile_Background); border: 1px solid var(--sapTile_BorderColor); border-radius: 0.5rem; padding: 1rem; text-align: center;">
      <div style="font-size: 0.875rem; color: var(--sapContent_LabelColor); margin-bottom: 0.5rem;">Total Registros</div>
      <div style="font-size: 1.5rem; font-weight: bold; color: var(--sapTextColor);">${totalRegistros}</div>
    </div>
    <div style="background: var(--sapTile_Background); border: 1px solid var(--sapTile_BorderColor); border-radius: 0.5rem; padding: 1rem; text-align: center;">
      <div style="font-size: 0.875rem; color: var(--sapContent_LabelColor); margin-bottom: 0.5rem;">Temp. Promedio</div>
      <div style="font-size: 1.5rem; font-weight: bold; color: var(--sapIndicationColor_5);">${tempPromedio}°C</div>
    </div>
    <div style="background: var(--sapTile_Background); border: 1px solid var(--sapTile_BorderColor); border-radius: 0.5rem; padding: 1rem; text-align: center;">
      <div style="font-size: 0.875rem; color: var(--sapContent_LabelColor); margin-bottom: 0.5rem;">Temp. Máxima</div>
      <div style="font-size: 1.5rem; font-weight: bold; color: var(--sapNegativeColor);">${tempMax !== -Infinity ? tempMax.toFixed(1) : 'N/A'}°C</div>
    </div>
    <div style="background: var(--sapTile_Background); border: 1px solid var(--sapTile_BorderColor); border-radius: 0.5rem; padding: 1rem; text-align: center;">
      <div style="font-size: 0.875rem; color: var(--sapContent_LabelColor); margin-bottom: 0.5rem;">Temp. Mínima</div>
      <div style="font-size: 1.5rem; font-weight: bold; color: var(--sapPositiveColor);">${tempMin !== Infinity ? tempMin.toFixed(1) : 'N/A'}°C</div>
    </div>
  `;
}

function mostrarTabla() {
  const tabla = document.getElementById('tablaHistoricos');
  if (!tabla) return;

  // Obtener o crear tbody
  const tbody = tabla.querySelector('tbody') || (() => {
    const tb = document.createElement('tbody');
    tabla.appendChild(tb);
    return tb;
  })();

  // Limpiar filas existentes
  tbody.innerHTML = '';

  // Calcular paginación
  const inicio = (paginaActual - 1) * registrosPorPagina;
  const fin = inicio + registrosPorPagina;
  const datosPagina = datosActuales.slice(inicio, fin);

  // Sin datos
  if (datosPagina.length === 0) {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 12;
    td.textContent = 'No Data';
    td.style.textAlign = 'center';
    tr.appendChild(td);
    tbody.appendChild(tr);
    actualizarPaginacion();
    return;
  }

  // Crear filas
  datosPagina.forEach(registro => {
    const tr = document.createElement('tr');

    const temp = parseFloat(registro.temperatura);
    const viento = parseFloat(registro.velocidad_viento);

    let claseTemp = 'valor-temperatura';
    if (!isNaN(temp) && temp < 5) claseTemp += ' frio';
    else if (!isNaN(temp) && temp > 25) claseTemp += ' calor';

    let claseViento = 'valor-viento';
    if (!isNaN(viento) && viento > 30) claseViento += ' fuerte';

    const mkTd = (value) => {
      const td = document.createElement('td');
      const v = (value === undefined || value === null || value === '') ? 'N/A' : value;
      td.textContent = v;
      return td;
    };

    // ID, Fecha, Hora
    tr.appendChild(mkTd(registro.id));
    tr.appendChild(mkTd(registro.fecha));
    tr.appendChild(mkTd(registro.hora));

    // Temperatura con estilo
    const tdTemp = document.createElement('td');
    const spanTemp = document.createElement('span');
    spanTemp.className = claseTemp;
    spanTemp.textContent = (registro.temperatura === undefined || registro.temperatura === null || registro.temperatura === '') ? 'N/A' : registro.temperatura;
    tdTemp.appendChild(spanTemp);
    tr.appendChild(tdTemp);

    // Máx / Mín
    tr.appendChild(mkTd(registro.temp_max));
    tr.appendChild(mkTd(registro.temp_min));

    // Humedad con estilo
    const tdHum = document.createElement('td');
    const spanHum = document.createElement('span');
    spanHum.className = 'valor-humedad';
    spanHum.textContent = (registro.humedad === undefined || registro.humedad === null || registro.humedad === '') ? 'N/A' : registro.humedad;
    tdHum.appendChild(spanHum);
    tr.appendChild(tdHum);

    // Viento con estilo
    const tdViento = document.createElement('td');
    const spanViento = document.createElement('span');
    spanViento.className = claseViento;
    spanViento.textContent = (registro.velocidad_viento === undefined || registro.velocidad_viento === null || registro.velocidad_viento === '') ? 'N/A' : registro.velocidad_viento;
    tdViento.appendChild(spanViento);
    tr.appendChild(tdViento);

    // Dirección, Ráfaga, Presión
    tr.appendChild(mkTd(registro.direccion_viento));
    tr.appendChild(mkTd(registro.rafaga_viento));
    tr.appendChild(mkTd(registro.presion));

    // Lluvia con estilo
    const tdLluvia = document.createElement('td');
    const spanLluvia = document.createElement('span');
    spanLluvia.className = 'valor-lluvia';
    spanLluvia.textContent = (registro.lluvia === undefined || registro.lluvia === null || registro.lluvia === '') ? 'N/A' : registro.lluvia;
    tdLluvia.appendChild(spanLluvia);
    tr.appendChild(tdLluvia);

    tbody.appendChild(tr);
  });

  // Actualizar paginación
  actualizarPaginacion();
}

function actualizarPaginacion() {
  const paginacionDiv = document.getElementById('paginacion');
  if (!paginacionDiv) return;
  
  const totalPaginas = Math.ceil(datosActuales.length / registrosPorPagina);
  
  if (totalPaginas <= 1) {
    paginacionDiv.innerHTML = '';
    return;
  }
  
  paginacionDiv.innerHTML = `
    <ui5-button id="btnPaginaAnterior" design="Transparent" ${paginaActual === 1 ? 'disabled' : ''}>
      Anterior
    </ui5-button>
    <span style="padding: 0 1rem;">Página ${paginaActual} de ${totalPaginas}</span>
    <ui5-button id="btnPaginaSiguiente" design="Transparent" ${paginaActual === totalPaginas ? 'disabled' : ''}>
      Siguiente
    </ui5-button>
  `;
  
  // Event listeners para paginación
  const btnAnterior = document.getElementById('btnPaginaAnterior');
  const btnSiguiente = document.getElementById('btnPaginaSiguiente');
  
  if (btnAnterior) {
    btnAnterior.addEventListener('click', () => {
      if (paginaActual > 1) {
        paginaActual--;
        mostrarTabla();
      }
    });
  }
  
  if (btnSiguiente) {
    btnSiguiente.addEventListener('click', () => {
      if (paginaActual < totalPaginas) {
        paginaActual++;
        mostrarTabla();
      }
    });
  }
}

function ocultarResultados() {
  const container = document.getElementById('resultadosContainer');
  if (container) {
    container.style.display = 'none';
  }
}

function mostrarLoading(mostrar) {
  const loading = document.getElementById('loadingIndicator');
  if (loading) {
    loading.style.display = mostrar ? 'flex' : 'none';
  }
}

function mostrarError(mensaje) {
  const errorContainer = document.getElementById('errorContainer');
  const errorMessage = document.getElementById('errorMessage');
  
  if (errorContainer && errorMessage) {
    errorMessage.textContent = mensaje;
    errorContainer.style.display = 'block';
    
    // Auto-ocultar después de 5 segundos
    setTimeout(() => {
      ocultarError();
    }, 5000);
  }
}

function ocultarError() {
  const errorContainer = document.getElementById('errorContainer');
  if (errorContainer) {
    errorContainer.style.display = 'none';
  }
}

function habilitarExportacion(habilitar) {
  const btnExportar = document.getElementById('btnExportar');
  if (btnExportar) {
    btnExportar.disabled = !habilitar;
  }
}

export function cleanup() {
  console.log('Limpiando página de históricos de clima');
  datosActuales = [];
  paginaActual = 1;
}
