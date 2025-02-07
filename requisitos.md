### ✅ **Requisitos clave del cliente HTTP según RFC 9110**

1. **Métodos HTTP bien implementados** : Soportar `GET`, `POST`, `PUT`, `DELETE`, `HEAD`, `OPTIONS`, etc.
2. **Encabezados HTTP correctos** : Manejo adecuado de `User-Agent`, `Accept`, `Host`, `Content-Type`, etc.
3. **Manejo de respuestas y códigos de estado** : Interpretar códigos como `200 OK`, `404 Not Found`, `500 Internal Server Error`, etc.
4. **Conexión persistente** : Soportar `Connection: keep-alive` cuando sea posible.
5. **Soporte para redirecciones (`3xx`)** : Seguir redirecciones si es necesario.
6. **Manejo de errores y excepciones** : Detectar `timeouts`, respuestas inválidas, problemas de conexión.
7. **Compatibilidad con HTTPS** : Uso de `SSL/TLS` con `requests` o `http.client` de Python.
8. **Soporte para compresión (`Accept-Encoding`)** : Permitir `gzip` o `deflate` cuando sea necesario.
