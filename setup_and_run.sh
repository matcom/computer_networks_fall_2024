#!/bin/bash
source env.sh
pip3 install -r requirements.txt
python3 src/http_server.py &  # Iniciar servidor en background
SERVER_PID=$!
sleep 2  # Esperar inicio
./run.sh  # Ejecutar tests
kill $SERVER_PID  # Detener servidor