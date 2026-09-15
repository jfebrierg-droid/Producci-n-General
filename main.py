import io
import json
import os
import time
from google.api_core.exceptions import ResourceExhausted
from google.genai import types
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google import genai
import pandas as pd


def generar_con_gemini(pdf_stream, prompt):
  """Procesa el PDF utilizando el nuevo SDK oficial de Google GenAI,

  con soporte de respaldo automático entre múltiples API keys.
  """
  secretos_keys = ["GEMINI_API_REEMBOLSO", "GEMINI_API_REEMBOLSO_2"]
  api_keys_disponibles = []

  for nombre_secreto in secretos_keys:
    key_val = os.environ.get(nombre_secreto)
    if key_val and key_val.strip():
      api_keys_disponibles.append((nombre_secreto, key_val.strip()))

  if not api_keys_disponibles:
    raise ValueError(
        "❌ No se encontró ninguna variable de API Key de Gemini configurada"
        " en los secretos."
    )

  last_exception = None

  for nombre_secreto, api_key in api_keys_disponibles:
    try:
      print(
          f"🔄 Subiendo PDF a Gemini utilizando la clave '{nombre_secreto}'..."
      )
      client = genai.Client(api_key=api_key)

      pdf_stream.seek(0)
      uploaded_file = client.files.upload(
          file=pdf_stream,
          config=types.UploadFileConfig(mime_type="application/pdf"),
      )

      print("🤖 Generando respuesta con Gemini...")
      response = client.models.generate_content(
          model="gemini-3.6-flash", contents=[uploaded_file, prompt]
      )

      return response.text.strip()

    except ResourceExhausted as err_rate:
      print(
          f"⚠️ La clave '{nombre_secreto}' alcanzó el límite de cuota (429"
          " RESOURCE_EXHAUSTED)."
      )
      last_exception = err_rate
      print("🔄 Intentando con la siguiente API key disponible...")
      continue
    except Exception as err:
      print(f"❌ Error inesperado con '{nombre_secreto}': {err}")
      last_exception = err
      continue

  raise last_exception


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

    # Limpiamos y separamos las palabras del nombre extraído para hacer una búsqueda flexible
    palabras_extraidas = [
        p.strip().lower() for p in nombre_extraido.split() if len(p.strip()) > 2
    ]

    for _, row in df.iterrows():
      nombre_excel = str(row.iloc[0]).strip().lower()

      # Verificamos si alguna palabra clave importante coincide en el registro de Excel
      coincidencias = sum(
          1 for palabra in palabras_extraidas if palabra in nombre_excel
      )

      if coincidencias >= 1:
        correo = str(row.iloc[5]).strip()
        if "@" in correo:
          print(
              f"✅ Coincidencia encontrada en Excel para '{nombre_extraido}'"
              f" con el registro '{row.iloc[0]}'"
          )
          return correo
  except Exception as e:
    print(f"Error leyendo el Excel: {e}")

  return None


def main():
  service = get_drive_service()
  folder_id = os.environ["GOOGLE_DRIVE_FOLDER_ID"]

  try:
    folder_info = (
        service.files()
        .get(fileId=folder_id, fields="name", supportsAllDrives=True)
        .execute()
    )
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
  results = (
      service.files()
      .list(
          q=query,
          pageSize=100,
          fields="files(id, name, mimeType)",
          includeItemsFromAllDrives=True,
          supportsAllDrives=True,
      )
      .execute()
  )
  files = results.get("files", [])

  print(f"\n📋 Total de elementos encontrados en '{folder_name}': {len(files)}")
  for f in files:
    print(f"    - [Elemento] Nombre: '{f['name']}' | Tipo: {f['mimeType']}")
  print("-" * 50)

  pdf_files = [
      f
      for f in files
      if "pdf" in f["mimeType"].lower() or f["name"].lower().endswith(".pdf")
  ]

  if not pdf_files:
    print("⚠️ Advertencia: No se detectaron archivos PDF válidos en esta carpeta.")
    return

  for file in pdf_files:
    pdf_name = file["name"]

    if "[" in pdf_name and "@" in pdf_name:
      print(
          f"⏭️ Omitiendo '{pdf_name}' porque ya fue procesado y renombrado."
      )
      continue

    print(f"\n🚀 ¡Procesando nuevo PDF detectado: '{pdf_name}'!")

    request = service.files().get_media(fileId=file["id"])
    pdf_stream = io.BytesIO()
    downloader = MediaIoBaseDownload(pdf_stream, request)
    done = False
    while not done:
      _, done = downloader.next_chunk()

    pdf_stream.seek(0)

    # Prompt actualizado para extraer el texto completo del campo Vía sin recortar arbitrariamente
    prompt = (
        "Extrae únicamente el nombre completo que aparece en el campo 'Vía' o"
        " solicitante (antes de cualquier barra '/' si hay varios)."
        " Devuélvelo tal cual aparece, sin recortar los apellidos."
    )

    max_intentos = 3
    nombre_extraido = None

    for intento in range(max_intentos):
      try:
        nombre_extraido = generar_con_gemini(pdf_stream, prompt)
        print(f"🤖 Gemini extrajo: {nombre_extraido}")
        break
      except ResourceExhausted as err_rate:
        if intento < max_intentos - 1:
          print(
              "⚠️ Límite de las API keys alcanzado (429). Esperando 15"
              f" segundos para reintentar (Intento {intento + 1}/{max_intentos})..."
          )
          time.sleep(15)
        else:
          print("❌ Se agotaron los reintentos y las API keys disponibles.")
          raise err_rate
      except Exception as err:
        print(f"❌ Error al procesar con Gemini: {err}")
        break

    if not nombre_extraido:
      continue

    correo_destino = buscar_correo_en_excel(nombre_extraido)

    if not correo_destino:
      print(
          f"⚠️ El nombre extraído ('{nombre_extraido}') no coincide con"
          " ningún registro válido en el Excel."
      )
      print(
          f"⏭️ Omitiendo renombrado para el archivo '{pdf_name}'. Se mantendrá"
          " con su nombre original."
      )
      continue

    print(f"📧 Correo mapeado: {correo_destino}")

    base_name = os.path.splitext(pdf_name)[0]
    nuevo_nombre_pdf = f"{base_name} [{correo_destino}].pdf"

    try:
      service.files().update(
          fileId=file["id"],
          body={"name": nuevo_nombre_pdf},
          supportsAllDrives=True,
      ).execute()
      print(f"✅ ¡Archivo renombrado exitosamente a: '{nuevo_nombre_pdf}'!")
    except Exception as rename_err:
      print(f"❌ Error al renombrar el archivo en Drive: {rename_err}")
      raise rename_err

    print("⏳ Esperando 6 segundos antes de procesar el siguiente archivo...")
    time.sleep(6)


if __name__ == "__main__":
  main()
