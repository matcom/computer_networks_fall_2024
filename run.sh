#!/bin/bash

# Replace the next shell command with the entrypoint of your solution

# echo $@

source env.sh

if [ "$PROTOCOL" -eq 1 ]; then
    python3 src/http_client.py "$@"
else
    echo "Error: Protocolo no soportado en run.sh"
    exit 1
fi