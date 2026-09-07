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
        folder_info = service.files().get(fileId=folder_id, fields="name", supportsAllDrives=True).execute()
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
    results = service.files().list(q=query, pageSize=100, fields="files(id, name, mimeType)", includeItemsFromAllDrives=True, supportsAllDrives=True).execute()
    files = results.get("files", [])
    
    print(f"\n📋 Total de elementos encontrados en '{folder_name}': {len(files)}")
    for f in files:
        print(f"   - [Elemento] Nombre: '{f['name']}' | Tipo: {f['mimeType']}")
    print("-" * 50)
    
    pdf_files = [f for f in files if "pdf" in f["mimeType"].lower() or f["name"].lower().endswith(".pdf")]
    
    if not pdf_files:
        print("⚠️ Advertencia: No se detectaron archivos PDF válidos en esta carpeta.")
        return

    for file in pdf_files:
        pdf_name = file["name"]
        
        # Si el archivo ya tiene el correo integrado en el nombre, lo omitimos para no reprocesarlo
        if "[" in pdf_name and "@" in pdf_name:
            print(f"⏭️ Omitiendo '{pdf_name}' porque ya fue procesado y renombrado.")
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
            nombre_extraido = generar_con_gemini(pdf_stream, prompt)
            print(f"🤖 Gemini extrajo: {nombre_extraido}")
        except Exception as err:
            print(f"❌ Error al procesar con Gemini: {err}")
            continue
        
        correo_destino = buscar_correo_en_excel(nombre_extraido)
        print(f"📧 Correo mapeado: {correo_destino}")
        
        # --- SOLUCIÓN DEFINITIVA: Renombrar el archivo existente para incluir el correo ---
        # Esto no crea archivos nuevos, por lo que la cuenta de servicio tiene permiso total.
        base_name = os.path.splitext(pdf_name)[0]
        nuevo_nombre_pdf = f"{base_name} [{correo_destino}].pdf"
        
        try:
            service.files().update(
                fileId=file["id"],
                body={"name": nuevo_nombre_pdf},
                supportsAllDrives=True
            ).execute()
            print(f"✅ ¡Archivo renombrado exitosamente a: '{nuevo_nombre_pdf}'!")
        except Exception as rename_err:
            print(f"❌ Error al renombrar el archivo en Drive: {rename_err}")
            raise rename_err

if __name__ == "__main__":
    main()
