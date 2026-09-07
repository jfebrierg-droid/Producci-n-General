def obtener_datos_desde_drive_imagen(file_id):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    print("Descargando imagen desde Google Drive...")
    response = requests.get(url, timeout=30)
    if response.status_code != 200:
        raise Exception(f"No se pudo descargar la imagen de Google Drive. Código HTTP: {response.status_code}")

    image_path = "temp_ranking_drive.jpg"
    with open(image_path, "wb") as f:
        f.write(response.content)

    img = Image.open(image_path)
    prompt = """
    Analiza esta imagen que contiene un reporte o tabla de producción de seguros del equipo MEGAPODEROSOS.
    Extrae la información de TODOS los intermediarios que aparecen y sus montos en los siguientes ramos:
    1. local
    2. inter (internacional)
    3. vida
    4. auto (auto, hogar y empresa)

    Devuelve la información estrictamente en formato de lista JSON de diccionarios, exactamente con estas claves:
    [
      {"intermediario": "Nombre del Intermediario", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
      ...
    ]
    Reglas importantes:
    - Incluye a TODOS los intermediarios visibles en la imagen.
    - Si un intermediario no tiene valor o aparece en cero/vacío, asigna el valor como "0.00".
    - Devuelve ÚNICAMENTE o exclusivamente el bloque JSON válido, sin texto adicional.
    """

    # Lista de modelos actuales recomendados
    modelos_a_probar = ['gemini-3.6-flash', 'gemini-2.5-flash']
    texto_respuesta = None

    # Rotamos entre llaves y modelos con manejo de reintentos por alta demanda
    for index, api_key in enumerate(API_KEYS_GEMINI):
        if not api_key: 
            continue
        client = genai.Client(api_key=api_key)
        for modelo in modelos_a_probar:
            for intento in range(2): # Reintentar hasta 2 veces por modelo en caso de saturación temporal
                try:
                    print(f"Intentando con {modelo} (Key #{index + 1}, Intento {intento + 1})...")
                    response = client.models.generate_content(model=modelo, contents=[img, prompt])
                    if response and response.text:
                        texto_respuesta = response.text
                        break
                except Exception as e:
                    print(f" -> Falló con {modelo}: {e}")
                    time.sleep(2) # Pausa breve antes de reintentar
                    continue
            if texto_respuesta: 
                break
        if texto_respuesta: 
            break

    if os.path.exists(image_path): 
        os.remove(image_path)
        
    if not texto_respuesta: 
        raise Exception("Error al procesar con IA: Los servidores están experimentando alta demanda. Por favor, intenta de nuevo en unos segundos.")

    match = re.search(r"\[.*\]", texto_respuesta, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    else:
        raise Exception(f"No se pudo interpretar la respuesta como JSON. Respuesta recibida:\n{texto_respuesta}")
