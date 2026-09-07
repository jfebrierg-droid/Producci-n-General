import os
import io
import json
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google import genai
from google.genai import types

def generar_con_gemini(pdf_stream, prompt):
    """
    Procesa el PDF utilizando el nuevo SDK oficial de Google GenAI.
    """
    api_key = os.environ.get("GEMINI_API_REEMBOLSO")
    if not api_key:
        raise ValueError("❌ No se encontró la variable GEMINI_API_REEMBOLSO en los secretos.")
    
    client = genai.Client(api_key=api_key.strip())
    
    print("🔄 Subiendo PDF a Gemini para análisis con el nuevo cliente...")
    pdf_stream.seek(0)
    
    uploaded_file = client.files.upload(
        file=pdf_stream,
        config=types.UploadFileConfig(mime_type="application/pdf")
    )
    
    print("🤖 Generando respuesta con Gemini...")
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[uploaded_file, prompt]
    )
    
    return response.text.strip()

def get_drive_service():
    creds_json = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
    creds = service_account.Credentials.from_service_account_info(
        creds_json, scopes=[
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/documents" # Scope necesario para Google Docs
        ]
    )
    # Necesitamos tanto el servicio de Drive como el de Docs
    drive_service = build("drive", "v3", credentials=creds)
    docs_service = build("docs", "v1", credentials=creds)
    return drive_service, docs_service

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
    drive_service, docs_service = get_drive_service()
    folder_id = os.environ["GOOGLE_DRIVE_FOLDER_ID"]
    
    try:
        folder_info = drive_service.files().get(fileId=folder_id, fields="name", supportsAllDrives=True).execute()
        folder_name = folder_info.get("name", "Desconocida")
        print(f"==================================================")
        print(f"🔎 CONECTADO A GOOGLE DRIVE")
        print(f"📂 Carpeta objetivo: '{folder_name}'")
        print(f"🆔 ID de carpeta: {folder_id}")
        print(f"==================================================")
    except Exception as e:
        print(f"❌ Error crítico en Google Drive: {e}")
        return

    query = f"'{folder_id}' in parents and trashed = false"
    results = drive_service.files().list(q=query, pageSize=100, fields="files(id, name, mimeType)", includeItemsFromAllDrives=True, supportsAllDrives=True).execute()
    files = results.get("files", [])
    
    print(f"\n📋 Total de elementos encontrados en '{folder_name}': {len(files)}")
    for f in files:
        print(f"   - [Elemento] Nombre: '{f['name']}' | Tipo: {f['mimeType']}")
    print("-" * 50)
    
    pdf_files = [f for f in files if "pdf" in f["mimeType"].lower() or f["name"].lower().endswith(".pdf")]
    
    # Ahora buscamos documentos de Google en lugar de archivos .txt
    existing_docs = {f["name"]: f["id"] for f in files if f["mimeType"] == "application/vnd.google-apps.document"}
    
    if not pdf_files:
        print("⚠️ Advertencia: No se detectaron archivos PDF válidos en esta carpeta.")
        return

    for file in pdf_files:
        pdf_name = file["name"]
        base_name = os.path.splitext(pdf_name)[0]
        doc_expected_name = f"{base_name}_destino" # Nombre sin extensión para el Google Doc
        
        if doc_expected_name in existing_docs:
            print(f"⏭️ Omitiendo '{pdf_name}' porque ya tiene su documento de salida '{doc_expected_name}'.")
            continue
            
        print(f"\n🚀 ¡Procesando nuevo PDF detectado: '{pdf_name}'!")
        
        request = drive_service.files().get_media(fileId=file["id"])
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
            nombre_extraido = generar_con_gemini(pdf_stream, prompt)
            print(f"🤖 Gemini extrajo: {nombre_extraido}")
        except Exception as err:
            print(f"❌ Error al procesar con Gemini: {err}")
            continue
        
        correo_destino = buscar_correo_en_excel(nombre_extraido)
        print(f"📧 Correo mapeado: {correo_destino}")
        
        # --- NUEVA ESTRATEGIA: Crear un Google Doc (0 bytes de cuota) ---
        print(f"📝 Creando Documento de Google nativo para evitar límites de almacenamiento...")
        try:
            # 1. Crear el Google Doc vacío en la carpeta destino
            file_metadata = {
                'name': doc_expected_name,
                'mimeType': 'application/vnd.google-apps.document',
                'parents': [folder_id]
            }
            doc = drive_service.files().create(body=file_metadata, supportsAllDrives=True).execute()
            doc_id = doc.get('id')
            
            # 2. Escribir el correo electrónico dentro del documento usando la API de Google Docs
            requests = [
                {
                    'insertText': {
                        'location': {
                            'index': 1,
                        },
                        'text': correo_destino
                    }
                }
            ]
            docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
            
            print(f"✅ ¡Documento de salida creado y escrito con éxito: '{doc_expected_name}'!")
            
        except Exception as drive_err:
            print(f"❌ Error al crear el Documento de Google: {drive_err}")
            raise drive_err

if __name__ == "__main__":
    main()
