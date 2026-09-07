import os
import glob
import pandas as pd
from google import genai

# Cargar la llave de Gemini desde los secretos de GitHub
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Rutas de trabajo actualizadas con el nombre exacto de tu Excel
LOCAL_DIR = "./Devoluciones de Reembolso - Automate"
EXCEL_PATH = "./Contactos_Cumpleanos_Megacentro_Automatizacion_ULTIMA_VERSION_10000_MENSAJES (1).xlsx"

def extraer_intermediario_con_gemini(pdf_path):
    """Sube el PDF a Gemini para extraer el texto exacto del campo 'Vía:'."""
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        print(f"Analizando con Gemini el archivo: {pdf_path}")
        uploaded_file = client.files.upload(file=pdf_path)
        
        prompt = (
            "Analiza este documento de reembolso de Humano Seguros. "
            "Busca el campo 'Vía:' o el nombre del corredor / intermediario asociado. "
            "Devuelve ÚNICAMENTE el nombre exacto del intermediario o corredor encontrado, sin texto adicional."
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[uploaded_file, prompt]
        )
        
        intermediario = response.text.strip()
        print(f"Intermediario identificado por Gemini: {intermediario}")
        client.files.delete(name=uploaded_file.name)
        return intermediario
    except Exception as e:
        print(f"Error procesando el PDF con Gemini: {e}")
        return None

def buscar_correo_en_excel(intermediario):
    """Busca el correo del intermediario en tu archivo Excel maestro."""
    if not os.path.exists(EXCEL_PATH):
        print(f"Error: No se encuentra el archivo Excel en la ruta: {EXCEL_PATH}")
        return None
    
    try:
        # Cargamos el Excel (puedes ajustar los nombres de las columnas 'Intermediario' y 'Correo' si en tu archivo se llaman diferente)
        df = pd.read_excel(EXCEL_PATH)
        
        # Intentamos buscar coincidencias parciales o exactas en las columnas de texto
        match = df[df.astype(str).apply(lambda row: row.str.contains(intermediario, case=False, na=False)).any(axis=1)]
        
        if not match.empty:
            # Buscamos una columna que comúnmente tenga el correo o tomamos la primera celda con '@'
            for col in match.columns:
                val = str(match.iloc[0][col])
                if "@" in val:
                    print(f"Correo encontrado en Excel para '{intermediario}': {val}")
                    return val
                    
            print(f"Se halló coincidencia para '{intermediario}', pero no se detectó una columna de correo válida.")
            return None
        else:
            print(f"No se encontró coincidencia en el Excel para: {intermediario}")
            return None
    except Exception as e:
        print(f"Error leyendo el archivo Excel: {e}")
        return None

def main():
    print("Iniciando análisis de PDFs con Python y Gemini...")
    
    if not os.path.exists(LOCAL_DIR):
        print(f"La carpeta local {LOCAL_DIR} no existe. Creando directorio...")
        os.makedirs(LOCAL_DIR, exist_ok=True)

    archivos_pdf = glob.glob(os.path.join(LOCAL_DIR, "*.pdf"))
    
    if not archivos_pdf:
        print("No hay archivos PDF pendientes por procesar en la carpeta.")
        return
    
    for pdf_path in archivos_pdf:
        print(f"\nProcesando archivo: {pdf_path}")
        
        # 1. Extraer intermediario usando Gemini
        intermediario = extraer_intermediario_con_gemini(pdf_path)
        if not intermediario:
            intermediario = "Desconocido"
            
        # 2. Buscar el correo en el Excel maestro
        correo_destino = buscar_correo_en_excel(intermediario)
        
        # Si no se encuentra en el Excel, por seguridad lo mandamos a tu correo
        if not correo_destino:
            print(f"Aviso: No se halló el correo para '{intermediario}'. Redirigiendo a jfebrier@humano.com.do por defecto.")
            correo_destino = "jfebrier@humano.com.do"
            
        # 3. Guardar el resultado en un archivo de texto (*_destino.txt) junto al PDF
        # Power Automate leerá este archivo para saber a quién reenviar el correo original
        base_name = os.path.splitext(pdf_path)[0]
        txt_output_path = f"{base_name}_destino.txt"
        
        with open(txt_output_path, "w", encoding="utf-8") as f:
            f.write(correo_destino)
            
        print(f"Resultado guardado exitosamente en: {txt_output_path} con el destinatario: {correo_destino}")

if __name__ == "__main__":
    main()
