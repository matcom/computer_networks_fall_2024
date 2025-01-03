#!/bin/bash

# Iniciar el servidor
echo "Iniciando el servidor..."
./tests/http/server &
SERVER_PID=$!

# Esperar un poco para asegurarnos de que el servidor esté completamente iniciado
sleep 2

# Ejecutar las pruebas
echo "Ejecutando las pruebas..."
python3 /tests/http/tests.py

# Detener el servidor después de las pruebas
echo "Deteniendo el servidor..."
kill $SERVER_PID
