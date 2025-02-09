# Documentación del Cliente IRC

## Estructura del Proyecto

El proyecto consta de tres archivos principales:

### Server.py

**Descripción**: Implementa el servidor IRC que maneja las conexiones de los clientes y procesa los comandos.

**Clases**:
- `IRCServer`: Clase principal que implementa la funcionalidad del servidor

**Métodos principales**:
- `__init__`: Inicializa el servidor con host y puerto
- `start`: Inicia el servidor y acepta conexiones
- `handle_client`: Maneja la conexión individual de cada cliente
- `process_command`: Procesa los comandos recibidos de los clientes
- `send_private_message`: Envía mensajes privados entre usuarios o a canales
- `change_nick`: Cambia el nickname de un usuario
- `join_channel`: Une a un usuario a un canal
- `part_channel`: Remueve a un usuario de un canal

### Client.py

**Descripción**: Implementa el cliente IRC que se conecta al servidor.

**Clases**:
- `IRCClient`: Clase principal para el cliente IRC

**Métodos principales**:
- `__init__`: Inicializa el cliente con host, puerto y nickname
- `connect`: Establece la conexión con el servidor
- `send_command`: Envía comandos al servidor
- `receive_response`: Recibe respuestas del servidor
- `handle_command`: Procesa los comandos del usuario
- `start_receiving`: Inicia el hilo de recepción de mensajes

### init_client.py

**Descripción**: Script de inicio que proporciona una interfaz de línea de comandos para el cliente IRC.

**Funcionalidades**:
- Solicita al usuario los datos de conexión (host, puerto, nickname)
- Inicializa y conecta el cliente IRC
- Maneja la entrada del usuario para enviar comandos
- Mantiene la conexión activa hasta que el usuario decide salir

**Flujo de trabajo**:
1. Solicita datos de conexión
2. Establece la conexión con el servidor
3. Inicia el hilo de recepción de mensajes
4. Procesa los comandos del usuario
5. Mantiene el bucle hasta que el usuario sale

## Comandos Soportados

El cliente IRC soporta los siguientes comandos:

- `/nick <nuevo_nick>`: Cambia el nickname del usuario
- `/join <canal>`: Une al usuario a un canal
- `/part <canal>`: Sale de un canal
- `/privmsg <destino> <mensaje>`: Envía un mensaje privado a un usuario o canal
- `/notice <destino> <mensaje>`: Envía una notificación a un canal
- `/list`: Lista los canales disponibles
- `/names <canal>`: Lista los usuarios en un canal
- `/whois <usuario>`: Obtiene información sobre un usuario
- `/topic <canal> [tema]`: Muestra o cambia el tema de un canal
- `/quit`: Sale del servidor IRC 