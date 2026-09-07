import os
import io
import json
import pandas as pd
import openpyxl
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

# Configurar la API de Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

def get_drive_service():
    creds_json = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
    creds = service_account.Credentials.from_service_account_info(
        creds_json, scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)

def buscar_correo_en_excel(nombre_extraido):
    """
    Busca el nombre extraído en el Excel (Asegúrate de cambiar 'tu_archivo_excel.xlsx' 
    por el nombre exacto de tu archivo en el repositorio).
    """
    try:
        df = pd.read_excel("tu_archivo_excel.xlsx", sheet_name=0)
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
    
    # Listar archivos de la carpeta
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, pageSize=50, fields="files(id, name, mimeType)").execute()
    files = results.get("files", [])
    
    print(f"--- Archivos encontrados en Drive ---")
    for f in files:
        print(f"-> Nombre: {f['name']} | Tipo: {f['mimeType']}")
    print("-------------------------------------")
    
    pdf_files = [f for f in files if f["mimeType"] == "application/pdf"]
    txt_filenames = [f["name"] for f in files if f["name"].endswith("_destino.txt")]
    
    if not pdf_files:
        print("No se encontraron archivos PDF pendientes.")
        return

    for file in pdf_files:
        pdf_name = file["name"]
        base_name = os.path.splitext(pdf_name)[0]
        txt_expected_name = f"{base_name}_destino.txt"
        
        if txt_expected_name in txt_filenames:
            print(f"Omitiendo '{pdf_name}' porque ya tiene su archivo _destino.txt creado.")
            continue
            
        print(f"¡Procesando PDF nuevo: {pdf_name}!")
        
        # Descargar PDF
        request = service.files().get_media(fileId=file["id"])
        pdf_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(pdf_stream, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
            
        pdf_stream.seek(0)
        
        # Procesar con Gemini
        sample_file = genai.upload_file(pdf_stream, mime_type="application/pdf")
        prompt = (
            "Extrae únicamente el nombre de la persona que aparece en el campo 'Vía' o solicitante. "
            "Trunca el resultado estrictamente al Primer Nombre y Primer Apellido, ignorando rutas o nombres secundarios."
        )
        response = model.generate_content([sample_file, prompt])
        nombre_extraido = response.text.strip()
        print(f"Gemini extrajo: {nombre_extraido}")
        
        # Buscar correo y generar archivo de texto
        correo_destino = buscar_correo_en_excel(nombre_extraido)
        print(f"Correo mapeado: {correo_destino}")
        
        txt_content = io.BytesIO(correo_destino.encode("utf-8"))
        media = MediaIoBaseUpload(txt_content, mimetype="text/plain", resumable=True)
        
        file_metadata = {
            "name": txt_expected_name,
            "parents": [folder_id]
        }
        
        service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        print(f"¡Creado y subido con éxito: {txt_expected_name}!")

if __name__ == "__main__":
    main()
