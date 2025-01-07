# Tester de Cliente FTP

Este proyecto incluye un script `run.sh` que te permite interactuar con un servidor FTP utilizando varios comandos. 

El script ejecuta un script de Python `tester.py` que a su vez utiliza `ftpclient.py` para realizar operaciones FTP.

## Ejecución

Para ejecutar el script, debes darle permisos de ejecución al archivo `run.sh` con el siguiente comando

  ```bash
chmod +x run.sh
   ```

Y luego ejecutarlo con el siguiente comando

  ```bash
sudo ./run.sh -s 127.0.0.1 -p 2121 -u user -pw pass "ls" 
```