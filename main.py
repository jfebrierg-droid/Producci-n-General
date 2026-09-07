def main():
    service = get_drive_service()
    folder_id = os.environ["GOOGLE_DRIVE_FOLDER_ID"]
    
    # Listar todos los archivos de la carpeta
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, pageSize=50, fields="files(id, name, mimeType)").execute()
    files = results.get("files", [])
    
    print(f"Archivos encontrados en la carpeta de Drive: {[f['name'] for f in files]}")
    
    pdf_files = [f for f in files if f["mimeType"] == "application/pdf"]
    txt_filenames = [f["name"] for f in files if f["name"].endswith("_destino.txt")]
    
    if not pdf_files:
        print("No se encontraron archivos PDF en la carpeta.")
        return

    for file in pdf_files:
        pdf_name = file["name"]
        base_name = os.path.splitext(pdf_name)[0]
        txt_expected_name = f"{base_name}_destino.txt"
        
        # Si ya existe el archivo de texto, lo saltamos
        if txt_expected_name in txt_filenames:
            print(f"Omitiendo {pdf_name}, ya tiene su archivo de destino.")
            continue
            
        print(f"¡Procesando PDF nuevo: {pdf_name}!")
        
        # Descargar el PDF
        request = service.files().get_media(fileId=file["id"])
        pdf_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(pdf_stream, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
            
        pdf_stream.seek(0)
        
        # Procesamiento con Gemini
        sample_file = genai.upload_file(pdf_stream, mime_type="application/pdf")
        prompt = (
            "Extrae únicamente el nombre de la persona que aparece en el campo 'Vía' o solicitante. "
            "Trunca el resultado estrictamente al Primer Nombre y Primer Apellido, ignorando rutas o nombres secundarios."
        )
        response = model.generate_content([sample_file, prompt])
        nombre_extraido = response.text.strip()
        print(f"Gemini extrajo: {nombre_extraido}")
        
        correo_destino = buscar_correo_en_excel(nombre_extraido)
        print(f"Correo mapeado: {correo_destino}")
        
        # Crear y subir el archivo _destino.txt
        txt_content = io.BytesIO(correo_destino.encode("utf-8"))
        media = MediaIoBaseUpload(txt_content, mimetype="text/plain", resumable=True)
        
        file_metadata = {
            "name": txt_expected_name,
            "parents": [folder_id]
        }
        
        service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        print(f"Creado y subido con éxito: {txt_expected_name}")
