import express from 'express';
import cors from 'cors';
import { MongoClient, ObjectId } from 'mongodb';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://admin:admin@146.181.17.135:27017/?authSource=admin';
const DB_NAME = process.env.DB_NAME || 'node-red';
const COLLECTION_NAME = process.env.COLLECTION_NAME || 'json-pruebas';

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

let client;
let db;
let collection;

async function connectToMongo() {
  try {
    client = new MongoClient(MONGODB_URI, {
      serverSelectionTimeoutMS: 5000,
      connectTimeoutMS: 10000,
    });
    await client.connect();
    db = client.db(DB_NAME);
    collection = db.collection(COLLECTION_NAME);
    console.log(`[MongoDB] Conectado exitosamente a la base de datos: ${DB_NAME}, colección: ${COLLECTION_NAME}`);
  } catch (error) {
    console.error('[MongoDB] Error al conectar:', error.message);
  }
}


// Endpoint para leer todos los datos
app.get('/api/data', async (req, res) => {
  try {
    if (!collection) await connectToMongo();
    const records = await collection.find({}).sort({ _id: -1 }).toArray();
    res.json(records);
  } catch (error) {
    console.error('Error al obtener datos:', error);
    res.status(500).json({ error: 'Error al obtener datos de MongoDB', details: error.message });
  }
});

// Endpoint para agregar un nuevo dato
app.post('/api/data', async (req, res) => {
  try {
    const { uid, nombre } = req.body;

    if (!uid || !nombre) {
      return res.status(400).json({ error: 'Campos requeridos: "uid" y "nombre"' });
    }

    if (!collection) await connectToMongo();

    const newDoc = {
      uid: String(uid).trim(),
      nombre: String(nombre).trim()
    };

    const result = await collection.insertOne(newDoc);
    res.status(201).json({
      success: true,
      message: 'Dato agregado exitosamente',
      insertedId: result.insertedId,
      document: { _id: result.insertedId, ...newDoc }
    });
  } catch (error) {
    console.error('Error al insertar dato:', error);
    res.status(500).json({ error: 'Error al guardar en MongoDB', details: error.message });
  }
});

// Endpoint opcional para eliminar un registro
app.delete('/api/data/:id', async (req, res) => {
  try {
    const { id } = req.params;
    if (!collection) await connectToMongo();

    let query = {};
    if (ObjectId.isValid(id)) {
      query = { _id: new ObjectId(id) };
    } else {
      query = { _id: id };
    }

    const result = await collection.deleteOne(query);
    if (result.deletedCount === 0) {
      return res.status(404).json({ error: 'Registro no encontrado' });
    }

    res.json({ success: true, message: 'Registro eliminado' });
  } catch (error) {
    res.status(500).json({ error: 'Error al eliminar registro', details: error.message });
  }
});

// Iniciar servidor
app.listen(PORT, async () => {
  console.log(`[Servidor] Dashboard corriendo en http://localhost:${PORT}`);
  await connectToMongo();
});
