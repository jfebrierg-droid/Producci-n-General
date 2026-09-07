import os
import io
import json
import pandas as pd
import openpyxl
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

# Llave oficial configurada en los secretos de GitHub
GEMINI_KEYS_ENV_VARS = ["GEMINI_API_REEMBOLSO"]

def generar_con_gemini_rotativo(pdf_stream, prompt):
    """
    Procesa el contenido con Gemini utilizando la llave de API configurada.
    """
    keys_disponibles = [os.environ.get(var) for var in GEMINI_KEYS_ENV_VARS if os.environ.get(var)]
    
    if not keys_disponibles:
        raise ValueError("❌ No se encontró la llave 'GEMINI_API_REEMBOLSO' configurada en los secretos de GitHub.")

    api_key = keys_disponibles[0]
    try:
        print("🔄 Procesando con Gemini usando la llave 'GEMINI_API_REEMBOLSO'...")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Subir archivo al entorno temporal de Gemini
        pdf_stream.seek(0)
        sample_file = genai.upload_file(pdf_stream, mime_type="application/pdf")
        
        response = model.generate_content([sample_file, prompt])
        resultado = response.text.strip()
        print("✅ ¡Gemini respondió con éxito!")
        return resultado
    except Exception as e:
        raise Exception(f"❌ Error al conectar con Gemini: {e}")

def get_drive_service():
    creds_json = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
    creds = service_account.Credentials.from_service_account_info(
        creds_json, scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)

def buscar_correo_en_excel(nombre_extraido):
    try:
        excel_filename = "Contactos_Cumpleanos_Megacentro_Automatizacion_ULTIMA_VERSION_10000_MENSAJES (1).xlsx"
        df = pd.read_excel(excel_filename, sheet_name=0)
        
        for _, row in df.iterrows():
            nombre_excel = str(row.iloc[0]).strip().lower()
            if nombre_extraido.strip().lower() in nombre_excel:
                correo = str(row.iloc[5]).strip()
                if "@" in correo:
                    return correo
    except Exception as e:
        print(f"Error leyendo el Excel: {e}")
    
    return "soporte.reembolso@humano.com.do"

def main():
    service = get_drive_service()
    folder_id = os.environ["GOOGLE_DRIVE_FOLDER_ID"]
    
    try:
        folder_info = service.files().get(fileId=folder_id, fields="name").execute()
        folder_name = folder_info.get("name", "Desconocida")
        print(f"==================================================")
        print(f"🔎 CONECTADO A GOOGLE DRIVE")
        print(f"📂 Carpeta objetivo: '{folder_name}'")
        print(f"🆔 ID de carpeta: {folder_id}")
        print(f"==================================================")
    except Exception as e:
        print(f"❌ Error crítico: La cuenta de servicio NO tiene acceso a la carpeta. Detalles: {e}")
        return

    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, pageSize=100, fields="files(id, name, mimeType)").execute()
    files = results.get("files", [])
    
    print(f"\n📋 Total de elementos encontrados en '{folder_name}': {len(files)}")
    for f in files:
        print(f"   - [Elemento] Nombre: '{f['name']}' | Tipo: {f['mimeType']}")
    print("-" * 50)
    
    pdf_files = [f for f in files if "pdf" in f["mimeType"].lower() or f["name"].lower().endswith(".pdf")]
    txt_filenames = [f["name"] for f in files if f["name"].endswith("_destino.txt")]
    
    if not pdf_files:
        print("⚠️ Advertencia: No se detectaron archivos PDF válidos en esta carpeta.")
        return

    for file in pdf_files:
        pdf_name = file["name"]
        base_name = os.path.splitext(pdf_name)[0]
        txt_expected_name = f"{base_name}_destino.txt"
        
        if txt_expected_name in txt_filenames:
            print(f"⏭️ Omitiendo '{pdf_name}' porque ya tiene su archivo de salida '{txt_expected_name}'.")
            continue
            
        print(f"\n🚀 ¡Procesando nuevo PDF detectado: '{pdf_name}'!")
        
        request = service.files().get_media(fileId=file["id"])
        pdf_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(pdf_stream, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
            
        pdf_stream.seek(0)
        
        prompt = (
            "Extrae únicamente el nombre de la persona que aparece en el campo 'Vía' o solicitante. "
            "Trunca el resultado estrictamente al Primer Nombre y Primer Apellido, ignorando rutas o nombres secundarios."
        )
        
        try:
            nombre_extraido = generar_con_gemini_rotativo(pdf_stream, prompt)
            print(f"🤖 Gemini extrajo: {nombre_extraido}")
        except Exception as err:
            print(f"❌ No se pudo procesar '{pdf_name}': {err}")
            continue
        
        correo_destino = buscar_correo_en_excel(nombre_extraido)
        print(f"📧 Correo mapeado: {correo_destino}")
        
        txt_content = io.BytesIO(correo_destino.encode("utf-8"))
        media = MediaIoBaseUpload(txt_content, mimetype="text/plain", resumable=True)
        
        file_metadata = {
            "name": txt_expected_name,
            "parents": [folder_id]
        }
        
        service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        print(f"✅ ¡Archivo de salida creado con éxito: '{txt_expected_name}'!")

if __name__ == "__main__":
    main()
