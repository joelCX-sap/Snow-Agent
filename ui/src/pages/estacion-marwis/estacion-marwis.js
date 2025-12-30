import { apiService } from '../../services/api.js';

let datos = null;

export function init() {
  // Registrar eventos
  const btnActualizar = document.getElementById('btnActualizar');
  if (btnActualizar) {
    btnActualizar.addEventListener('click', handleActualizar);
  }

  // Cargar datos iniciales
  cargarDatos();
}

async function handleActualizar() {
  mostrarLoading(true);
  mostrarError('');
  try {
    const resp = await apiService.refreshStationData();
    if (!resp.success) {
      throw new Error(resp.message || 'Error actualizando datos');
    }
    datos = resp;
    renderInfo(datos);
    renderTabla(datos.sensors || []);
  } catch (e) {
    mostrarError(e.message || 'Error desconocido');
  } finally {
    mostrarLoading(false);
  }
}

async function cargarDatos() {
  mostrarLoading(true);
  mostrarError('');
  try {
    const resp = await apiService.getStationData();
    if (!resp.success) {
      // Si aún no existe el JSON, mostrar mensaje y tabla vacía
      mostrarError(resp.message || 'No hay datos disponibles. Presione Actualizar para generarlos.');
      renderTabla([]);
      renderInfo(null);
      return;
    }
    datos = resp;
    renderInfo(datos);
    renderTabla(datos.sensors || []);
  } catch (e) {
    mostrarError(e.message || 'Error cargando datos');
  } finally {
    mostrarLoading(false);
  }
}

function renderInfo(data) {
  const info = document.getElementById('info');
  if (!info) return;

  if (!data) {
    info.innerHTML = `
      <div style="color: var(--sapContent_LabelColor); font-size: 0.875rem;">
        No hay datos de estación. Presione "Actualizar" para obtener los datos desde ViewMondo.
      </div>
    `;
    return;
  }

  const total = typeof data.total === 'number' ? data.total : ((data.sensors || []).length);
  info.innerHTML = `
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; margin-bottom: 0.5rem;">
      <div style="background: var(--sapTile_Background); border: 1px solid var(--sapTile_BorderColor); border-radius: 0.5rem; padding: 0.75rem;">
        <div style="font-size: .75rem; color: var(--sapContent_LabelColor);">Total Sensores</div>
        <div style="font-weight: 700;">${total}</div>
      </div>
    </div>
  `;
}

function renderTabla(sensors) {
  const tabla = document.getElementById('tablaMarwis');
  if (!tabla) return;

  const tbody = tabla.querySelector('tbody') || (() => {
    const tb = document.createElement('tbody');
    tabla.appendChild(tb);
    return tb;
  })();

  tbody.innerHTML = '';

  if (!sensors || sensors.length === 0) {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 3;
    td.textContent = 'No Data';
    td.style.textAlign = 'center';
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }

  sensors.forEach(s => {
    const tr = document.createElement('tr');

    const tdName = document.createElement('td');
    tdName.textContent = s.SensorChannelName || '—';
    tr.appendChild(tdName);

    const tdUnit = document.createElement('td');
    tdUnit.textContent = s.SensorChannelUnit || '—';
    tr.appendChild(tdUnit);

    const tdType = document.createElement('td');
    tdType.textContent = (s.SensorTypeId !== undefined && s.SensorTypeId !== null) ? s.SensorTypeId : '—';
    tr.appendChild(tdType);

    tbody.appendChild(tr);
  });
}

function mostrarLoading(show) {
  const loading = document.getElementById('loading');
  if (loading) {
    loading.style.display = show ? 'block' : 'none';
  }
  const btn = document.getElementById('btnActualizar');
  if (btn) btn.disabled = !!show;
}

function mostrarError(msg) {
  const cont = document.getElementById('errorContainer');
  const span = document.getElementById('errorMessage');
  if (!cont || !span) return;

  if (msg) {
    span.textContent = msg;
    cont.style.display = 'block';
  } else {
    cont.style.display = 'none';
    span.textContent = '';
  }
}

export function cleanup() {
  datos = null;
}
