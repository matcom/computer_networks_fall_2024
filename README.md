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
