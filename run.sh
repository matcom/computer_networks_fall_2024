#!/bin/bash

# Obtener los parámetros
while getopts "p:u:f:t:s:b:h:" opt; do
  case $opt in
    p) port="$OPTARG" ;;         # Puerto SMTP (Ej: 25)
    u) host="$OPTARG" ;;         # Dirección del servidor SMTP (Ej: 127.0.0.1)
    f) from_mail="$OPTARG" ;;    # Remitente (Ej: user1@uh.cu)
    t) to_mail="$OPTARG" ;;      # Destinatarios (Ej: ["user2@uh.cu", "user3@uh.cu"])
    s) subject="$OPTARG" ;;      # Asunto (Ej: "Email for testing purposes")
    b) body="$OPTARG" ;;         # Cuerpo del correo (Ej: "Body content")
    h) header="$OPTARG" ;;       # Headers en formato JSON (Ej: {} o {"CC": "cc@example.com"})
    *) echo "Uso: $0 -p port -u host -f from_mail -t to_mail -s subject -b body -h header" ;;
  esac
done

# Ejecutar el cliente SMTP
python3 - <<END
import json
from src.client import SMTPClient

host = "$host"
port = int("$port") 
sender = "$from_mail"

try:
    recipients = json.loads('$to_mail') 
    if not isinstance(recipients, list):
        raise ValueError("Los destinatarios deben ser una lista.")
except json.JSONDecodeError:
    raise ValueError("Formato incorrecto para los destinatarios. Debe ser una lista en formato JSON.")

subject = "$subject"
body = "$body"

try:
    headers = json.loads('$header') if '$header' else {}
    if not isinstance(headers, dict):
        raise ValueError("El parámetro header debe ser un diccionario JSON.")
except json.JSONDecodeError:
    raise ValueError("Formato incorrecto para los headers. Debe ser un JSON válido.")

client = SMTPClient(host, port)
client.connect()
client.send_mail(sender, recipients, subject, body, headers)
client.disconnect()
END
