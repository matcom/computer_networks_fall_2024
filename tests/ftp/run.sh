#!/bin/bash

# Mostrar ayuda si no se proporcionan suficientes argumentos
if [ "$#" -lt 9 ]; then
  echo "Uso: $0 -s server -p puerto -u user -pw pass \"command\""
  exit 1
fi

# Parsear los argumentos
while [[ "$#" -gt 0 ]]; do
  case $1 in
    -s) server="$2"; shift ;;
    -p) port="$2"; shift ;;
    -u) user="$2"; shift ;;
    -pw) pass="$2"; shift ;;
    *) command="$1" ;;
  esac
  shift
done

# Ejecutar el script de Python con los parámetros proporcionados
python3 tester.py -s $server -p $port -u $user -pw $pass -c "$command"
