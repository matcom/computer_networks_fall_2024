#!/bin/bash

# Iniciar el servidor
echo "Iniciando el servidor..."
./tests/http/server &
SERVER_PID=$!
e
# Esperar un poco para asegurarnos de que el servidor esté completamente iniciado
sleep 2

curl http://localhost:8080/

# Ejecutar las pruebas
echo "Ejecutando las pruebas..."
python3 ./tests/http/tests.py

if [[ $? -ne 0 ]]; then
  echo "HTTP test failed"
  exit 1
fi
