#!/bin/bash

method=""
url=""
headers=""
data=""

while getopts ":m:u:h:d:" opt; do
  case $opt in
    m) method="$OPTARG" ;;
    u) url="$OPTARG" ;;
    h) headers="$OPTARG" ;;
    d) data="$OPTARG" ;;
    \?) echo "Opción inválida: -$OPTARG" >&2
        exit 1
        ;;
    :) echo "La opción -$OPTARG requiere un argumento." >&2
       exit 1
       ;;
  esac
done

if [ -z "$method" ] || [ -z "$url" ]; then
  echo "Uso: $0 -m <method> -u <url> -h <headers> -d <data>"
  exit 1
fi

python3 client.py -m "$method" -u "$url" -H "$headers" -d "$data"