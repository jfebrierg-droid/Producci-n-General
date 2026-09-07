import os
import io
import json
import pandas as pd
import openpyxl
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

# 1. Configurar la API de Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

# 2. Conectar a Google Drive usando las credenciales del Secret
def get_drive_service():
    creds_json = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
    creds = service_account.Credentials.from_service_account_info(
        creds_json, scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)

def buscar_correo_en_excel(nombre_extraido):
    """
    Busca el nombre extraído por Gemini en tu Excel maestro (Columna A: Nombre, Columna F: Correo).
    Ajusta el nombre del archivo de Excel según el que tengas en tu repositorio.
    """
    try:
        df = pd.read_excel("tu_archivo_excel.xlsx", sheet_name=0) # Cambia por el nombre real de tu Excel
        # Asumiendo que Columna A es 'Nombre' y Columna F es 'Correo' (índice 0 y 5)
        for _, row in df.iterrows():
            nombre_excel = str(row.iloc[0]).strip().lower()
            if nombre_extraido.strip().lower() in nombre_excel:
                correo = str(row.iloc[5]).strip()
                if "@" in correo:
                    return correo
    except Exception as e:
        print(f"Error leyendo el Excel: {e}")
    
    # Correo por defecto o fallback si no lo encuentra
    return "soporte.reembolso@humano.com.do"

def main():
    service = get_drive_service()
    folder_id = os.environ["GOOGLE_DRIVE_FOLDER_ID"]
    
    # Listar archivos de la carpeta en Google Drive
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, pageSize=50, fields="files(id, name, mimeType)").execute()
    files = results.get("files", [])
    
    pdf_files = [f for f in files if f["mimeType"] == "application/pdf"]
    txt_filenames = [f["name"] for f in files if f["name"].endswith("_destino.txt")]
    
    if not pdf_files:
        print("No hay archivos PDF pendientes por procesar.")
        return

    for file in pdf_files:
        pdf_name = file["name"]
        base_name = os.path.splitext(pdf_name)[0]
        txt_expected_name = f"{base_name}_destino.txt"
        
        # Si ya se procesó este PDF y existe el archivo de texto, lo omitimos
        if txt_expected_name in txt_filenames:
            continue
            
        print(f"Procesando PDF: {pdf_name}")
        
        # Descargar el PDF desde Google Drive
        request = service.files().get_media(fileId=file["id"])
        pdf_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(pdf_stream, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
            
        pdf_stream.seek(0)
        
        # --- PROCESAMIENTO CON GEMINI ---
        # Subimos el PDF temporalmente a la API de Gemini para extraer el campo "Vía" / Nombre
        sample_file = genai.upload_file(pdf_stream, mime_type="application/pdf")
        
        prompt = (
            "Extrae únicamente el nombre de la persona que aparece en el campo 'Vía' o solicitante. "
            "Trunca el resultado estrictamente al Primer Nombre y Primer Apellido, ignorando rutas o nombres secundarios."
        )
        
        response = model.generate_content([sample_file, prompt])
        nombre_extraido = response.text.strip()
        print(f"Gemini extrajo: {nombre_extraido}")
        
        # Buscar el correo correspondiente en el Excel local del repositorio
        correo_destino = buscar_correo_en_excel(nombre_extraido)
        print(f"Correo mapeado: {correo_destino}")
        
        # Crear el archivo de texto de respuesta (_destino.txt)
        txt_content = io.BytesIO(correo_destino.encode("utf-8"))
        media = MediaIoBaseUpload(txt_content, mimetype="text/plain", resumable=True)
        
        file_metadata = {
            "name": txt_expected_name,
            "parents": [folder_id]
        }
        
        service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        print(f"Creado y subido con éxito a Google Drive: {txt_expected_name}")

if __name__ == "__main__":
    main()
