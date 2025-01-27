PROTOCOL=1

# Replace the next shell command with the entrypoint of your solution

# Asegurarse de que se proporcione el método, la URL, los encabezados y los datos
while getopts "m:u:h:d:" opt; do
  case $opt in
    m) method=$OPTARG ;;  # Método HTTP
    u) url=$OPTARG ;;     # URL
    h) headers=$OPTARG ;; # Encabezados
    d) data=$OPTARG ;;    # Cuerpo de la solicitud
    *) echo "Uso: run.sh -m <method> -u <url> [-h <headers>] [-d <data>]" 
       exit 1 ;;
  esac
done

# Proveer valores predeterminados si los encabezados o datos no se proporcionan
headers=${headers:-'{}'}
data=${data:-''}

# Ejecutar el script client.py con los parámetros
python3 client.py "$method" "$url" "$headers" "$data"
