# Telemáticos - MongoDB Dashboard

Dashboard web sencillo para la lectura y agregado de datos en MongoDB (`node-red` -> `json-pruebas`).

## 🚀 Requisitos

- [Node.js](https://nodejs.org/) (versión 18 o superior)

## 📦 Instalación

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/Thomas-ctrl23/telematicos.git
   cd telematicos
   ```

2. Instalar dependencias:
   ```bash
   npm install
   ```

3. Iniciar la aplicación:
   ```bash
   npm start
   ```

4. Abrir en el navegador:
   ```
   http://localhost:3000
   ```

## ⚙️ Configuración (.env)

El archivo `.env` contiene la configuración de conexión:

```env
PORT=3000
MONGODB_URI=mongodb://admin:admin@146.181.17.135:27017/?authSource=admin
DB_NAME=node-red
COLLECTION_NAME=json-pruebas
```

## 📋 Estructura

- `server.js`: API REST con Node.js y Express conectada a MongoDB.
- `public/`: Frontend con HTML5, CSS3 y JavaScript para lectura y agregado de registros en tiempo real.
