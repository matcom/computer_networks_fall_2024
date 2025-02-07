#!/bin/bash

# Replace the next shell command with the entrypoint of your solution

while getopts ":m:u:h:d:" opt; do
  case $opt in
    m) method="$OPTARG" ;;
    u) url="$OPTARG" ;;
    H) headers="$OPTARG" ;;
    d) data="$OPTARG" ;;
    *) echo "Uso: $0 -m <method> -u <url> -h <headers> -d <data>"
       exit 1
       ;;
  esac
done

# Llamar al script de Python con los argumentos
python3 client.py -m "$method" -u "$url" -H "$headers" -d "$data"