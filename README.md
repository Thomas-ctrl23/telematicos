# DataClean AI - Limpieza Inteligente de Datasets con Pandas

Aplicación web moderna y robusta para la depuración, estandarización y control de calidad de datasets (CSV y Excel), impulsada por **Python (Pandas)** en el backend y una interfaz de usuario en **React + Vite**, preparada para su despliegue en **Vercel**.

---

## Características Principales

1. **Uso de Pandas y NumPy en el Backend**:
   - Todo el análisis estadístico, manipulación y filtrado se realiza con Pandas de alto rendimiento.
2. **Eliminación de Celdas Faltantes (NaN)**:
   - Eliminación de filas con celdas vacías (`dropna(how='any')` o `dropna(how='all')`).
   - Umbral porcentual de vacíos por fila.
   - Detección y eliminación opcional de columnas 100% vacías.
3. **Eliminación de Filas Repetidas**:
   - Detección de duplicados exactos en todas las columnas o subconjuntos clave.
   - Estrategia de conservación: primera ocurrencia (`first`) o última (`last`).
4. **Tratamiento de Valores Extremos (Outliers)**:
   - Detección por **IQR** (Rango Intercuartílico Tukey 1.5×) o **Z-Score** (Desviación estándar 3.0σ).
   - Acciones: Eliminación de filas con anomalías o acotamiento a límites válidos (**Winsorizing / Clipping**).
5. **Corrección de Errores Tipográficos y Topográficos**:
   - Normalización de espacios en blanco y saltos superfluos.
   - Normalización de capitalización.
   - Algoritmo de agrupación difusa (**Fuzzy String Matching**) con umbral de similitud configurable (ej. unifica `Madird` a `Madrid`, `Barelona` a `Barcelona`).
6. **Previsualización y Auditoría**:
   - Vista previa interactiva de datos (paginación, búsqueda por celda).
   - Conmutador entre datos originales y datos limpios.
   - Registro de auditoría (*Audit Log*) paso a paso de cada acción realizada.
7. **Descarga Multi-formato**:
   - Exportación directa en **CSV** (UTF-8 con BOM) o **Excel (.xlsx)**.

---

## Ejecución en Local

### 1. Iniciar el Backend (FastAPI / Python)
En una terminal:
```bash
# Instalar dependencias
pip install -r requirements.txt

# Iniciar servidor de API en el puerto 8000
python -m uvicorn api.index:app --reload --port 8000
```
La API estará disponible en `http://127.0.0.1:8000` (documentación Swagger interactiva en `http://127.0.0.1:8000/api/docs`).

### 2. Iniciar el Frontend (React + Vite)
En otra terminal:
```bash
# Instalar dependencias de Node.js
npm install

# Iniciar servidor de desarrollo en el puerto 5173
npm run dev
```
Abre tu navegador en `http://localhost:5173`. Las peticiones `/api/*` se reenviarán automáticamente al backend local en el puerto 8000.

---

## Despliegue en Vercel

El proyecto cuenta con `vercel.json` y `requirements.txt` listos para desplegar tanto el frontend estático como las funciones serverless de Python.

### Opción A: Desde GitHub / GitLab / Bitbucket
1. Sube este proyecto a tu repositorio de GitHub.
2. Ve a [vercel.com](https://vercel.com) y selecciona **Add New Project**.
3. Importa el repositorio.
4. Vercel detectará la configuración automáticamente y desplegará:
   - El frontend compilado con `npm run build` en el CDN global.
   - Las rutas `/api/*` en Serverless Functions de Python (`@vercel/python`).

### Opción B: Con Vercel CLI
```bash
# Instalar Vercel CLI si no lo tienes
npm i -g vercel

# Desplegar
vercel
```

---

## Estructura del Código

```
├── api/
│   ├── index.py           # Endpoints FastAPI (/api/analyze, /api/clean, /api/export)
│   └── cleaner.py         # Motor de limpieza con Pandas
├── src/
│   ├── components/        # Componentes UI (Upload, Controls, Metrics, Table, AuditLog, Export)
│   ├── App.jsx            # Flujo de la aplicación
│   ├── index.css          # Estilos modernos Glassmorphism
│   └── main.jsx
├── tests/
│   └── test_cleaner.py    # Tests unitarios del motor Pandas
├── requirements.txt       # Dependencias Python para Vercel
├── vercel.json            # Configuración de despliegue en Vercel
├── package.json           # Dependencias de Vite & React
└── vite.config.js         # Proxy local y configuración de Vite
```
