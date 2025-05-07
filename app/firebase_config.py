import json
import os
import firebase_admin
from firebase_admin import credentials, storage
from dotenv import load_dotenv

load_dotenv()

firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS")
if not firebase_credentials_path:
    raise ValueError("FIREBASE_CREDENTIALS no está definido en .env o está vacío.")

# Asegurarse de que la ruta sea correcta
firebase_credentials_path = os.path.join(os.path.dirname(__file__), '..', firebase_credentials_path)

# Cargar el archivo de credenciales
try:
    with open(firebase_credentials_path, 'r') as f:
        firebase_credentials = json.load(f)
except Exception as e:
    raise ValueError(f"Error al cargar el archivo de credenciales: {e}")

storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET")
if not storage_bucket:
    raise ValueError("FIREBASE_STORAGE_BUCKET no está definido en .env o está vacío.")
storage_bucket = storage_bucket.strip()

# Inicializar Firebase solo una vez
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_credentials)
    firebase_admin.initialize_app(cred, {"storageBucket": storage_bucket})

bucket = storage.bucket()
