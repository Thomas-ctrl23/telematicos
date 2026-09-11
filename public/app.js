// Estado de la aplicación
let records = [];
let isSubmitting = false;

// Elementos del DOM
const tableBody = document.getElementById('table-body');
const emptyState = document.getElementById('empty-state');
const addForm = document.getElementById('add-data-form');
const uidInput = document.getElementById('uid-input');
const nombreInput = document.getElementById('nombre-input');
const btnSubmit = document.getElementById('btn-submit');
const btnRefresh = document.getElementById('btn-refresh');
const searchInput = document.getElementById('search-input');
const toastContainer = document.getElementById('toast-container');

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
  loadData();
  setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
  addForm.addEventListener('submit', handleAddData);

  btnRefresh.addEventListener('click', () => {
    loadData(true);
  });

  searchInput.addEventListener('input', (e) => {
    filterData(e.target.value.trim().toLowerCase());
  });
}

// Cargar datos desde la API
async function loadData(showToastOnSuccess = false) {
  try {
    const res = await fetch('/api/data');
    if (!res.ok) throw new Error('Error al consultar datos');
    
    records = await res.json();
    renderTable(records);

    if (showToastOnSuccess) {
      showToast('Datos actualizados', 'success');
    }
  } catch (err) {
    console.error(err);
    tableBody.innerHTML = `
      <tr>
        <td colspan="4" class="text-center" style="color: var(--accent-danger); padding: 24px;">
          ⚠️ Error al cargar los datos. Revisa la conexión con MongoDB.
        </td>
      </tr>
    `;
    showToast('Error al conectar con la base de datos', 'error');
  }
}

// Renderizar tabla
function renderTable(dataToRender) {
  tableBody.innerHTML = '';

  if (!dataToRender || dataToRender.length === 0) {
    emptyState.style.display = 'flex';
    return;
  }

  emptyState.style.display = 'none';

  dataToRender.forEach((item) => {
    const tr = document.createElement('tr');
    const itemId = item._id ? item._id.toString() : '';

    tr.innerHTML = `
      <td>
        <span class="uid-badge">
          ${escapeHtml(item.uid || '-')}
          <button class="copy-btn" onclick="copyToClipboard('${escapeHtml(item.uid)}')", title="Copiar UID">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
          </button>
        </span>
      </td>
      <td>
        <span class="user-name">${escapeHtml(item.nombre || '-')}</span>
      </td>
      <td>
        <span class="id-badge">${escapeHtml(itemId)}</span>
      </td>
      <td style="text-align: right;">
        <button class="btn btn-danger" onclick="deleteRecord('${itemId}', '${escapeHtml(item.nombre)}')", title="Eliminar registro">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
        </button>
      </td>
    `;
    tableBody.appendChild(tr);
  });
}

// Manejar creación de registro
async function handleAddData(e) {
  e.preventDefault();
  if (isSubmitting) return;

  const uid = uidInput.value.trim();
  const nombre = nombreInput.value.trim();

  if (!uid || !nombre) {
    showToast('Por favor completa el UID y Nombre', 'error');
    return;
  }

  setSubmitting(true);

  try {
    const res = await fetch('/api/data', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ uid, nombre })
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || 'Error al guardar');
    }

    showToast(`Guardado: ${nombre}`, 'success');
    uidInput.value = '';
    nombreInput.value = '';
    uidInput.focus();

    await loadData();
  } catch (err) {
    console.error(err);
    showToast(err.message || 'Error al guardar el registro', 'error');
  } finally {
    setSubmitting(false);
  }
}

// Eliminar registro
async function deleteRecord(id, nombre) {
  if (!confirm(`¿Eliminar "${nombre}"?`)) {
    return;
  }

  try {
    const res = await fetch(`/api/data/${id}`, {
      method: 'DELETE'
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || 'No se pudo eliminar');
    }

    showToast('Registro eliminado', 'success');
    loadData();
  } catch (err) {
    showToast(err.message || 'Error al eliminar', 'error');
  }
}


// Filtrar datos en tiempo real
function filterData(query) {
  if (!query) {
    renderTable(records);
    return;
  }

  const filtered = records.filter(item => {
    const uidMatch = item.uid && item.uid.toLowerCase().includes(query);
    const nombreMatch = item.nombre && item.nombre.toLowerCase().includes(query);
    return uidMatch || nombreMatch;
  });

  renderTable(filtered);
}

// Copiar al portapapeles
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    showToast(`Copiado: ${text}`, 'success');
  }).catch(() => {
    showToast('No se pudo copiar', 'error');
  });
}

// Estado del botón de envío
function setSubmitting(state) {
  isSubmitting = state;
  const btnText = btnSubmit.querySelector('.btn-text');
  const btnSpinner = btnSubmit.querySelector('.btn-spinner');
  
  btnSubmit.disabled = state;
  if (state) {
    btnText.style.display = 'none';
    btnSpinner.style.display = 'inline-flex';
  } else {
    btnText.style.display = 'inline-flex';
    btnSpinner.style.display = 'none';
  }
}

// Notificaciones Toast
function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${type === 'success' ? '✓' : '✕'}</span>
    <span>${escapeHtml(message)}</span>
  `;

  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Escapar HTML para evitar XSS
function escapeHtml(string) {
  if (!string) return '';
  const entityMap = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
    '/': '&#x2F;'
  };
  return String(string).replace(/[&<>"'/]/g, s => entityMap[s]);
}

window.deleteRecord = deleteRecord;
window.copyToClipboard = copyToClipboard;
