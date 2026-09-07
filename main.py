import os
import glob
import pandas as pd
from google import genai

# Cargar la llave de Gemini desde los secretos de GitHub
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Rutas basadas en la estructura exacta de tu repositorio
LOCAL_DIR = "./Devoluciones de Reembolso - Automate"
EXCEL_PATH = "./Contactos_Cumpleanos_Megacentro_Automatizacion_ULTIMA_VERSION_10000_MENSAJES (1).xlsx"

def extraer_intermediario_con_gemini(pdf_path):
    """Extrae el primer nombre y primer apellido del intermediario principal ignorando barras y nombres adicionales."""
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        print(f"Analizando con Gemini el archivo: {pdf_path}")
        uploaded_file = client.files.upload(file=pdf_path)
        
        prompt = (
            "Analiza este documento de reembolso de Humano Seguros. "
            "Busca el campo 'Vía:'. Este campo puede contener nombres separados por una barra diagonal (/). "
            "Toma únicamente la primera persona antes de la barra. "
            "Extrae exclusivamente su PRIMER NOMBRE y su PRIMER APELLIDO (ignora segundos nombres o apellidos adicionales). "
            "Devuelve ÚNICAMENTE esos dos términos (Ejemplo: 'Ruddy Arias'), sin texto adicional."
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[uploaded_file, prompt]
        )
        
        intermediario = response.text.strip()
        print(f"Intermediario simplificado por Gemini para búsqueda: {intermediario}")
        client.files.delete(name=uploaded_file.name)
        return intermediario
    except Exception as e:
        print(f"Error procesando el PDF con Gemini: {e}")
        return None

def buscar_correo_en_excel(intermediario):
    """Busca el correo basándose en la coincidencia del nombre abreviado en la columna 'Nombre'."""
    if not os.path.exists(EXCEL_PATH):
        print(f"Error: No se encuentra el archivo Excel en la ruta: {EXCEL_PATH}")
        return None
    
    try:
        df = pd.read_excel(EXCEL_PATH)
        
        # Buscamos coincidencias flexibles con el primer nombre y apellido en la columna 'Nombre'
        match = df[df['Nombre'].astype(str).str.contains(intermediario, case=False, na=False)]
        
        if not match.empty:
            correo = match.iloc[0]['Correo']
            if pd.notna(correo) and "@" in str(correo):
                print(f"Correo encontrado para '{intermediario}': {correo}")
                return str(correo).strip()
                
        print(f"No se encontró un correo válido en la columna 'Correo' para: {intermediario}")
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
        
        # 1. Extraer y simplificar el nombre del intermediario usando Gemini
        intermediario = extraer_intermediario_con_gemini(pdf_path)
        if not intermediario:
            intermediario = "Desconocido"
            
        # 2. Buscar el correo en el Excel maestro usando columnas 'Nombre' y 'Correo'
        correo_destino = buscar_correo_en_excel(intermediario)
        
        # Si no se encuentra, por seguridad se redirige a tu correo
        if not correo_destino:
            print(f"Aviso: No se halló el correo para '{intermediario}'. Redirigiendo a jfebrier@humano.com.do por defecto.")
            correo_destino = "jfebrier@humano.com.do"
            
        # 3. Guardar el resultado en un archivo de texto (*_destino.txt) para Power Automate
        base_name = os.path.splitext(pdf_path)[0]
        txt_output_path = f"{base_name}_destino.txt"
        
        with open(txt_output_path, "w", encoding="utf-8") as f:
            f.write(correo_destino)
            
        print(f"Resultado guardado exitosamente en: {txt_output_path} con el destinatario: {correo_destino}")

if __name__ == "__main__":
    main()
