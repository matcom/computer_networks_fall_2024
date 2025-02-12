


#!/bin/bash
# Configuración básica del servidor HTTP
#python3 src/http_server.py --host 0.0.0.0 --port 8080
#echo $@

python3 -m pytest tests/http/ -v
PROTOCOL=1  # HTTP
echo "PROTOCOL=${PROTOCOL}" >> "$GITHUB_ENV"