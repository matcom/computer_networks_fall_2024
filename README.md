# Servidor y Cliente FTP

Implementación de un servidor y cliente FTP en Python, desarrollado como proyecto para la clase de Redes de Computadoras.

## Características

### Servidor
- Manejo de usuarios básico
- Operaciones con archivos y directorios
- Soporte para comandos FTP estándar
- Transferencia de archivos en modo ASCII y binario
- Sistema de permisos básico

### Cliente
- Interfaz de línea de comandos interactiva
- Descarga automática de archivos a carpeta "Downloads"
- Soporte completo de comandos FTP
- Manejo de errores y feedback al usuario

## Comandos Soportados

### Comandos de Acceso y Control
- `USER` - Especifica el usuario
- `PASS` - Especifica la contraseña
- `ACCT` - Especifica la cuenta del usuario
- `QUIT` - Cierra la conexión
- `REIN` - Reinicia la conexión
- `NOOP` - No realiza ninguna operación

### Comandos de Navegación
- `PWD` - Muestra el directorio actual
- `CWD` - Cambia el directorio de trabajo
- `CDUP` - Cambia al directorio padre
- `LIST` - Lista archivos y directorios
- `NLST` - Lista nombres de archivos

### Comandos de Gestión de Archivos
- `MKD` - Crea un directorio
- `RMD` - Elimina un directorio
- `DELE` - Elimina un archivo
- `RNFR` - Especifica el archivo a renombrar
- `RNTO` - Especifica el nuevo nombre

### Comandos de Transferencia
- `RETR` - Recupera/descarga un archivo
- `STOR` - Almacena/sube un archivo
- `STOU` - Almacena un archivo con nombre único
- `APPE` - Añade datos a un archivo existente
- `REST` - Reinicia transferencia desde un punto específico
- `ABOR` - Aborta la operación en progreso

### Comandos de Configuración
- `PORT` - Especifica dirección y puerto para conexión
- `PASV` - Entra en modo pasivo
- `TYPE` - Establece el tipo de transferencia
- `STRU` - Establece la estructura de archivo
- `MODE` - Establece el modo de transferencia
- `ALLO` - Reserva espacio

### Comandos de Información
- `SYST` - Muestra información del sistema
- `STAT` - Retorna estado actual
- `HELP` - Muestra la ayuda
- `SITE` - Comandos específicos del sitio
- `SMNT` - Monta una estructura de sistema de archivos

## Uso

### Iniciar el Servidor
```bash
python server.py
```

### Iniciar el Cliente
```bash
python client.py
```

### Ejemplos de Uso

1. Conectar al servidor:
   ```
   FTP> USER anonymous
   FTP> PASS anonymous
   ```

2. Navegar y listar archivos:
   ```
   FTP> PWD
   FTP> LIST
   FTP> CWD carpeta
   ```

3. Transferir archivos:
   ```
   FTP> STOR archivo.txt
   FTP> RETR documento.pdf
   ```

## Requisitos
- Python 3.6+
- Bibliotecas estándar de Python (socket, os, pathlib)
# Repositorio para la entrega de proyectos de la asignatura de Redes de Computadoras. Otoño 2024 - 2025

### Requisitos para la ejecución de las pruebas:

1. Ajustar la variable de entorno `procotol` dentro del archivo `env.sh` al protocolo correspondiente. 

2. Modificar el archivo `run.sh` con respecto a la ejecución de la solución propuesta.

### Ejecución de los tests:

1. En cada fork del proyecto principal, en el apartado de `actions` se puede ejecutar de forma manual la verificación del código propuesto.

2. Abrir un `pull request` en el repo de la asignatura a partir de la propuesta con la solución.

### Descripción general del funcionamineto de las pruebas:

Todas las pruebas siguen un modelo de ejecución simple. Cada comprobación ejecuta un llamado al scrip `run.sh` contenido en la raíz del proyecto, inyectando los parametros correspondientes.

La forma de comprobación es similar a todos los protocolos y se requiere que el ejecutable provisto al script `run.sh` sea capaz de, en cada llamado, invocar el método o argumento provisto y terminar la comunicación tras la ejecución satisfactoria del metodo o funcionalidad provista.

### Argumentos provistos por protocolo:

#### HTTP:
1. -m method. Ej. `GET`
2. -u url. Ej `http://localhost:4333/example`
3. -h header. Ej `{}` o `{"User-Agent": "device"}`
4. -d data. Ej `Body content`

#### SMTP:
1. -p port. Ej. `25`
2. -u host. Ej `127.0.0.1`
3. -f from_mail. Ej. `user1@uh.cu`
4. -f to_mail. Ej. `user2@uh.cu`
5. -s subject. Ej `"Email for testing purposes"`
6. -b body. Ej `"Body content"`
7. -h header. Ej `{}` o ```{\\"CC\\":\\ \\"cc@examplecom\\"}```

#### FTP:
1. -p port. Ej. `21`
2. -h host. Ej `127.0.0.1`
3. -u user. Ej. `user`
4. -w pass. Ej. `pass`
5. -c command. Ej `STOR`
6. -a first argument. Ej `"tests/ftp/new.txt"`
7. -b second argument. Ej `"new.txt"`

#### IRC
1. -p port. Ej. `8080`
2. -H host. Ej `127.0.0.1`
3. -n nick. Ej. `TestUser1`
4. -c command. Ej `/nick`
5. -a argument. Ej `"NewNick"`

### Comportamiento de la salida esperada por cada protocolo:

1. ``HTTP``: Json con formato ```{"status": 200, "body": "server output"}```

2. ``SMTP``: Json con formato ```{"status_code": 333, "message": "server output"}```

3. ``FTP``: Salida Unificada de cada interacción con el servidor.

4. ``IRC``:  Salida Unificada de cada interacción con el servidor.
