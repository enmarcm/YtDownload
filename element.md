Perfecto. Elaboraré un informe completo y detallado que abarque:

* Cómo detectar y explotar vulnerabilidades reales como inyecciones SQL, XSS, CSRF, RCE, etc., en tu aplicación web.
* Cómo realizar escaneo de rutas y endpoints desconocidos.
* Cómo realizar pruebas de saturación (DoS simuladas) contra el servidor.
* Cómo documentar y evidenciar técnicamente una explotación exitosa.

Usaré como base las URLs que me proporcionaste del entorno `https://dev.khatar.droguerialalider.com`. Te avisaré cuando el informe esté listo para que puedas revisarlo.

# Guía técnica de pruebas de penetración en *dev.khatar.droguerialalider.com*

Esta guía detalla los pasos para realizar un **pentesting autorizado** (caja negra) sobre la aplicación web  *dev.khatar.droguerialalider.com* . Cubriremos desde el reconocimiento inicial hasta la explotación de vulnerabilidades específicas (SQLi, XSS, CSRF, etc.) y pruebas de resistencia (DoS). Se incluyen comandos reales, ejemplos y buenas prácticas de seguridad ofensiva.

## 1. Reconocimiento y escaneo de puertos

Comenzamos identificando los puertos y servicios expuestos en el servidor. Usamos **Nmap** y  **Masscan** :

* **Nmap** : herramienta de código abierto para escanear redes, puertos y servicios. Ejecutar, por ejemplo:

```bash
  nmap -Pn -sS -sV -p- dev.khatar.droguerialalider.com
```

* `-Pn`: no ping (tratamos el host como activo).
* `-sS`: escaneo SYN furtivo.
* `-sV`: detección de versión de servicios.
* `-p-`: escanea todos los puertos (1–65535).

  Esto revelará servicios abiertos (por ejemplo HTTPS en puerto 443, HTTP en 80, bases de datos, etc.) y sus versiones. Nmap puede usar scripts NSE para buscar vulnerabilidades comunes (por ejemplo, el script **vuln** detecta fallos conocidos).
* **Masscan** : escáner a escala internet para puertos TCP masivos. Útil si se sospecha de múltiples direcciones IP. Ejemplo de uso:

```bash
  masscan dev.khatar.droguerialalider.com -p0-65535 --rate 1000
```

  Esto barrerá rápido todos los puertos TCP a baja tasa. Luego, Nmap puede investigar más a fondo los puertos que Masscan reporte abiertos.

Tras el escaneo, anotar los puertos abiertos y servicios (por ejemplo  *80/tcp (HTTP), 443/tcp (HTTPS), 1433/tcp (MS SQL?)* ). Este reconocimiento inicial es esencial para planificar siguientes pasos.

## 2. Enumeración de rutas y endpoints

A continuación descubrimos rutas HTTP/REST ocultas usando **fuerzas brutas de directorios/archivos** con herramientas como **Dirsearch** y  **ffuf** :

* **Dirsearch** : escáner de ruta web en Python. Permite enumerar directorios y archivos potenciales en un servidor web. Ejemplo básico:

```bash
  dirsearch -u https://dev.khatar.droguerialalider.com -e php,html,js -w /usr/share/wordlists/dirb/common.txt
```

* `-u`: URL objetivo.
* `-e`: extensiones a probar (por ejemplo PHP, HTML, JS).
* `-w`: diccionario de palabras (aquí se usan rutas comunes de  *dirb* ).

  Dirsearch listará rutas válidas (código HTTP 200) como  **/auth/** ,  **/admin/** ,  **/api/** , etc., que podrían representar endpoints útiles. Se pueden refinar las palabras (usar listas más completas) según los resultados iniciales.
* **ffuf (Fuzz Faster U Fool)** : fuzzer web ultrarrápido en Go, ideal para descifrar rutas y parámetros. Ejemplos:
* **Descubrimiento de rutas** :
  ``bash ffuf -u https://dev.khatar.droguerialalider.com/FUZZ -w /usr/share/wordlists/dirb/common.txt ``

    Esto probará cada entrada del diccionario en la URL, sustituyendo`FUZZ` por una palabra de la lista, para encontrar páginas/directorios existentes.

* **Fuzzing de parámetros GET** :
  ``bash ffuf -u "https://dev.khatar.droguerialalider.com/producto?limite=FUZZ&soloOferta=s" -w numbers.txt -fc 400 ``

    Aquí se fuerza el parámetro`limite` con distintos valores (por ejemplo números) para observar respuestas distintas a 400 (bad request).

* **API REST** : si se identifica prefijo de API (e.g., `/api/v1/`), se puede hacer:
  ``bash ffuf -u https://dev.khatar.droguerialalider.com/api/v1/FUZZ -w /usr/share/wordlists/api-endpoints.txt ``

    Buscando endpoints REST conocidos (por ejemplo`usuarios`, `productos`, etc.).

Usar cabeceras HTTP personalizadas (`-H`) o cookies de sesión en ffuf si es necesario. El objetivo es  **mapear toda la superficie web** , incluyendo front-end React y rutas ocultas del backend (Express).

## 3. Escaneo automatizado de vulnerabilidades

Con el reconocimiento inicial completo, empleamos **escáneres de vulnerabilidades** para hallar fallos comunes:

* **OWASP ZAP (Zed Attack Proxy)** : proxy/interceptor web gratuito de OWASP, muy usado para escaneo automático.

1. **Proxy** : configurar el navegador para enrutar tráfico HTTP(S) por ZAP. Navegar la aplicación manualmente para que ZAP aprenda el sitemap.
2. **Escaneo activo** : en ZAP, seleccionar el objetivo y lanzar un  *Active Scan* . ZAP enviará ataques automatizados (SQLi, XSS, etc.) sobre las rutas detectadas.

    ZAP generará un informe con hallazgos (inyecciones, headers faltantes, configuraciones inseguras).

* **Burp Suite** : plataforma de pruebas de seguridad (Community o Pro).

1. **Interceptación y mapa de sitio** : configurar Burp como proxy. Navegar para generar el *site map* completo. Además, usar la *Spider* (“Araña”) de Burp para rastrear automáticamente enlaces y parámetros.
2. **Escaneo de vulnerabilidades** : Burp Scanner (versión Pro) permite escaneo activo/pasivo. Según [37], Burp puede realizar un escaneo activo que envía peticiones automáticas sobre el sitio escaneado. Con Burp en el  *Target* , hacer clic derecho en el host y seleccionar  **“Actively scan this host”** .
3. **Resultados** : Burp reportará vulnerabilidades (por ejemplo XSS, CSRF, LFI, etc.) con ilustraciones. Incluso en versión gratuita, se puede usar Burp Intruder para pruebas manuales dirigidas.

Estos escáneres completan la fase de reconocimiento pasiva con pruebas activas sistemáticas. Sin embargo, siempre verificar manualmente los falsos positivos y profundizar en cualquier indicio de fallo.

## 4. Pruebas de inyección SQL (SQLi)

La aplicación usa SQL Server en backend (Node.js + Express). SQLi permite manipular consultas SQL. Procedemos así:

1. **Identificar parámetros vulnerables** : por ejemplo, la ruta  **/producto?limite=12&soloOferta=s** . Probar manualmente inyecciones comunes:

* Inyectar comillas o lógica booleana:

  ```
  /producto?limite=12' AND '1'='1&soloOferta=s
  ```

  o

  ```
  /producto?limite=12' OR 'a'='a&soloOferta=s
  ```

  y observar si la respuesta cambia. Un comportamiento anómalo (mensaje de error SQL, o contenido repetido) indica posible SQLi.
* **Time-based SQLi** (MS SQL): inyectar retraso para confirmar vulnerabilidad. Ejemplo:

  ```
  /producto?limite=12'; WAITFOR DELAY '0:0:5';--&soloOferta=s
  ```

  Si el servidor demora ~5 segundos en responder, el payload funcionó. Esto prueba inyección de tipo *time-based* en SQL Server.

1. **Explotación manual** : si existe SQLi, se pueden extraer datos poco a poco. Por ejemplo, para determinar versión o base de datos:

```
   1' UNION SELECT @@version-- 
```

   O enumerar tablas: se usan consultas en información de esquema (`INFORMATION_SCHEMA.TABLES` en SQL Server) con booleanos o retrasos. Cada inyección exige análisis cuidadoso del back-end (por ejemplo, Node/Express podría filtrar errores).

1. **Uso de sqlmap** : herramienta automática especializada en SQLi. Tras confirmar manualmente la inyección, ejecutar:

```bash
   sqlmap -u "https://dev.khatar.droguerialalider.com/producto?limite=12&soloOferta=s" \
     --cookie="SESSION=<valor_de_sesion>" --dbms "mssql" --batch --threads=5 --random-agent --batch
```

* `--cookie`: incluir cookie de autenticación si es necesario.
* `--dbms "mssql"`: indicar motor SQL Server.
* `--dbs`: para listar bases de datos.
* `--tables`: para listar tablas (después de `--dbs`).
* `--dump`: para extraer datos (usar con precaución en entorno real).

  Sqlmap probará automáticamente inyecciones (error-based, boolean, time-based, etc.) y reportará bases, tablas y columnas accesibles. Por ejemplo, podría recuperar el esquema de la base **KhatarDB** y las credenciales de usuarios.

1. **Buena práctica** : Toda explotación debe realizarse de forma controlada y documentada. Evitar dañar datos en la BD; usar transacciones o solo lectura. Además, siempre validar los hallazgos (un `--flush-session` en sqlmap puede reiniciar las pruebas para evitar estados inconsistentes).

## 5. Pruebas de XSS (Cross-Site Scripting) y seguridad del cliente

Los XSS permiten inyectar scripts maliciosos en el navegador de otro usuario. React.js por defecto escapa contenido, pero hay vectores si se usan APIs peligrosas:

* **XSS Reflejado/Almacenado** : buscar campos de formulario, parámetros URL o puntos donde la aplicación refleja entrada de usuario. Ejemplos: inputs de búsqueda, comentarios, o parámetros de consulta.
* Inyectar scripts simples en campos (por ejemplo `"><script>alert('XSS')</script>`). Si aparece una alerta o código en la respuesta, hay XSS.
* Con React+Material UI, los inputs normalmente están escapados.  **Peligro** : uso de `dangerouslySetInnerHTML`. Verificar código React por `dangerouslySetInnerHTML={{__html: ...}}`. Como indica StackHawk, este prop (que incluye “dangerous” en su nombre) debe usarse con precaución, pues reintroduce XSS. Si el app asigna directamente HTML no sanitizado a un componente, podemos inyectar etiquetas `<img>` con payload o `<svg/onload=...>` para ejecutar código.
* **XSS DOM-based** : manipular el DOM con inputs. Por ejemplo, si existe código JS que lee `window.location.hash` o `document.write` con datos controlados, podrían ser vectores. Probar insertando código en la URL (`#<script>alert()</script>`) y observar la consola del navegador.
* **Prevención/confirmación** : utilizar *burp* o *browser DevTools* para interceptar respuestas. Si se detecta XSS, documentarlo (captura de pantalla de la alerta) y su vector exacto. Ejemplo de hallazgo: campo de nombre de producto que admite `<script>...`.

En resumen, aunque React protege XSS por defecto, revisar puntos donde la entrada de usuario se inserta dinámicamente. OWASP indica que los ataques XSS ocurren cuando datos de usuarios llegan a la página sin validación ni codificación. Cualquier lugar así es blanco de prueba.

## 6. Pruebas de CSRF (Cross-Site Request Forgery)

CSRF engaña al navegador de un usuario autenticado para que envíe peticiones no autorizadas. Para probarlo:

* Verificar en la aplicación rutas sensibles que respondan a solicitudes *GET o POST* (p.ej., cambio de contraseña, actualización de usuario). Si existe un formulario sin token CSRF, puede ser vulnerable.
* Probar crear un **simple HTML malicioso** en otro dominio:

  ```html
  <img src="https://dev.khatar.droguerialalider.com/api/eliminarUsuario?user=123" />
  ```

  Si al cargar esa página (mientras el usuario está autenticado en  *droguerialalider.com* ) la cuenta 123 se elimina sin pedir confirmación, hay CSRF.
* Alternativamente, usar herramientas como Burp **CSRF PoC Generator** en el response para generar ejemplos de CSRF.
* Buena práctica: asegurarse de que todas las operaciones críticas usen tokens anti-CSRF (como *csrfToken* en formularios). De encontrarse un endpoint susceptible, documentarlo con el PoC del ataque.

## 7. Otras pruebas (RCE, LFI, etc.)

Además de las inyecciones anteriores, se buscan vectores adicionales:

* **LFI/RFI (Local/Remote File Inclusion)** : si la aplicación incluye archivos basándose en entrada (por ejemplo, `?file=report.txt`), probar ataques de path traversal (`../../etc/passwd` en Linux o `..\windows\win.ini` en Windows). Si un endpoint muestra el contenido de un archivo especificado, podría ser vulnerable. Documentar cualquier archivo accedido indebidamente.
* **RCE (Remote Code Execution)** : en Node.js, esto implicaría parámetros que terminen ejecutando comandos del sistema. Por ejemplo, si existe un parámetro que se pasa directamente a `child_process.exec()`, probar comandos como `& whoami` o `; ls`. Buscar endpoints de upload de archivos: un uploader mal validado podría permitir subir un archivo `.js` o `.aspx` malicioso y luego ejecutarlo. Documentar cualquier ejecución remota detectada.
* **Otros vectores** :  *Command Injection* ,  *XXE* ,  *Open Redirects* , etc. El escáner de Burp/ZAP debería reportar los hallazgos. Cada vulnerabilidad confirmada debe incluir el payload exacto, la respuesta esperada y el impacto (e.g., acceso a archivos sensibles, ejecución de comandos).

## 8. Pruebas de carga y DoS

Para evaluar la resistencia del servidor, simulamos altos volúmenes de tráfico a endpoints intensivos (por ejemplo, consultas de base de datos complejas o carga de archivos):

* **ApacheBench (ab)** : herramienta simple de benchmarking HTTP. Ejemplo:

```bash
  ab -k -n 1000 -c 100 -H "Accept-Encoding: gzip,deflate" https://dev.khatar.droguerialalider.com/auth/login
```

* `-n 1000`: total de solicitudes.
* `-c 100`: concurrencia (solicitudes paralelas).
* `-k`: habilita keep-alive.

  Este comando envía 1000 peticiones a `/auth/login` con 100 simultáneas, simulando carga. Los resultados mostrarán el tiempo medio de respuesta, fallos, transferencias, etc. (ver ejemplo de uso en).
* **JMeter** : herramienta gráfica/configurable. Se puede crear un *Test Plan* que envíe múltiples hilos (>100) de peticiones a los endpoints críticos. JMeter provee métricas avanzadas (tiempo de respuesta percentiles, error rate). Ideal para pruebas más realistas (login con sesiones, formularios, etc.).
* **Bombardier** : herramienta CLI de carga en Go. Ejemplo simple:

```bash
  bombardier -c 200 -n 5000 https://dev.khatar.droguerialalider.com/producto?limite=12&soloOferta=s
```

  Esto envía 5000 solicitudes con 200 concurrencia al endpoint de productos, midiendo throughput y latencia. Se pueden variar rutas (/api/ intensivas) para encontrar cuál colapsa primero.

Durante estas pruebas, monitorear recursos del servidor (CPU, memoria,  *latencia* ) para detectar cuellos de botella.  **Advertencia** : incluso siendo autorizado, las pruebas de carga pueden afectar al entorno. Coordinar con el cliente antes de ejecutarlas en producción.

## 9. Documentación de hallazgos

Registrar cada paso es crucial:

* **Capturas** : tomar pantallazos de respuestas relevantes (por ejemplo, peticiones interceptadas, alertas de XSS, salidas de sqlmap, resultados de nmap/ab).
* **Comandos y resultados** : incluir los comandos exactos usados y fragmentos de las respuestas (por ejemplo, banner de nmap o código de respuesta HTTP).
* **Explicaciones** : para cada vulnerabilidad encontrada, describir qué es, cómo se explotó, y el impacto. Adjuntar la petición con payload y la respuesta vulnerable.
* **Buenas prácticas** : Enumerar recomendaciones (por ejemplo, uso de consultas preparadas para SQL, encoding de salida para XSS, tokens CSRF, límites de tasa en APIs).

Cada sección de esta guía corresponde a una fase típica de pentesting (recon, enum, explotación, pos-explotación). Al final, se debe generar un reporte ejecutivo con los principales riesgos y un reporte técnico con evidencias detalladas.

**Referencias:** Herramientas y conceptos citados en esta guía han sido documentados por expertos en seguridad. Use estos recursos como apoyo mientras realiza las pruebas.
