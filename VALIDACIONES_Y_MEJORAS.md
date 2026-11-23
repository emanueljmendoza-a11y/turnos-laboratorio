# Validaciones, correcciones y mejoras — BiblioEstructuras

## Resumen de la revisión

El proyecto continúa usando **programación estructurada** (funciones, listas,
árbol BST, grafo, BFS, heaps y JSON), sin clases propias para la lógica de negocio.
**Flask es la única dependencia principal externa.**

### Errores o riesgos corregidos

1. **ISBN sin código de control:** antes se aceptaba cualquier secuencia de 10 o 13 dígitos, aunque fuese inválida. Ahora se comprueba el dígito de control del ISBN-10 (incluido `X`) y del ISBN-13. Los ISBN previamente guardados se conservan por compatibilidad y se deben corregir al editarlos.
2. **JSON con referencias o estados incoherentes:** la lectura solo comprobaba que existieran cuatro listas. Ahora se validan identificadores únicos, ISBN únicos, correos duplicados, datos obligatorios, fechas, claves foráneas, reservas y préstamos duplicados, y ocupación frente al total de ejemplares.
3. **Transacciones que podían guardar registros inconsistentes:** antes de reemplazar el JSON ahora se revalida todo su contenido. Si la validación falla, el original se conserva sin cambios.
4. **Búsqueda ineficiente:** una búsqueda por título ya no reconstruye el árbol BST innecesariamente. El árbol se construye solo para consultas con forma de ISBN completo.
5. **Disponibilidad calculada repetidamente:** el catálogo y las métricas ahora acumulan los ejemplares prestados y reservados en un diccionario con una sola pasada; la asignación de reservas también evita recomputar el total por cada turno.
6. **Recorrido del grafo con ordenamientos redundantes:** BFS recorre directamente las listas de adyacencia y las recomendaciones se ordenan una sola vez al final.
7. **Validaciones insuficientes de formularios:** se normalizan nombres y correos, se revisan longitudes, cantidades, años y estados y se rechazan entradas incorrectas con mensajes específicos.

### Nuevas funciones y medidas defensivas

- Editar usuarios; eliminarlos únicamente si no tienen historial de préstamos ni reservas.
- Descargar un **respaldo JSON** desde la interfaz.
- Botón **Prestar** para las reservas listas, con el usuario y libro preseleccionados.
- Protección CSRF ya presente, más límite de tamaño del cuerpo, respuesta 413 amigable y cabeceras `Content-Security-Policy`, `X-Frame-Options`, `Referrer-Policy`, `X-Content-Type-Options` y `Cache-Control`.
- `json.dump()` utiliza escritura temporal, `fsync` y `os.replace` para reducir el riesgo de dejar un archivo incompleto durante un guardado. Esto **no equivale** a una base de datos transaccional ni a un respaldo automático.
- Mensajes de error entendibles si se encuentra un JSON dañado, sin sobrescribirlo.

## Resultado comprobado

| Suite | Verificaciones | Resultado en el entorno de revisión |
| --- | ---: | --- |
| `tests/test_sistema.py` | 24 | Pasaron |
| `tests/test_validaciones.py` | 77 | Pasaron |
| `tests/test_plantillas.py` | 16 | Pasaron (13 plantillas y 3 variantes) |
| `python -m compileall -q .` | Todos los módulos Python | Pasó |
| `tests/test_flask.py` | Varios escenarios HTTP | **No ejecutado**: Flask no está instalado y la red no permitió descargarlo |

Se probó además que las modificaciones rechazadas **no sobrescriben el JSON**, las
altas concurrentes dentro de un proceso no pierden registros y el archivo de
demostración sigue teniendo estados coherentes.

## Cómo repetir la batería en tu computadora

En la raíz del proyecto, después de instalar las dependencias:

```bash
python verificar.py
```

O una por una:

```bash
python tests/test_sistema.py
python tests/test_validaciones.py
python tests/test_plantillas.py
python tests/test_flask.py
```

Cada suite usa su propio archivo temporal. Si las pruebas HTTP fallan, revisa
primero la instalación `python -m pip install -r requirements.txt`. Para ejecutar
la aplicación normalmente utiliza `python app.py`.

## Limitaciones conocidas

- Es un sistema **educativo y local**, sin cuentas de administrador ni permisos
  diferenciados. No debe publicarse en Internet con información real de lectores.
- El archivo JSON se carga y reescribe completo en cada modificación. El bloqueo
  protege los hilos **de un solo proceso**, pero no varios servidores independientes.
- Los índices BST y el grafo se crean por petición; sirven para demostrar las
  estructuras, no para competir en rendimiento con una base de datos.
- No se implementó caducidad automática de reservas listas ni sanciones por mora:
  no fueron solicitadas y requerirían definir reglas de la biblioteca.


## Revisión 3.0 — eliminación de algoritmos predefinidos

Se cambió la implementación, manteniendo los menús y las reglas de negocio:

- `heapq.heapify`/`heapq.heappop` → `crear_monticulo`, `insertar_monticulo`, `_subir`, `_hundir`, `extraer_minimo`.
- `collections.deque` → lista con índice de lectura para BFS.
- `sorted()`/`.sort()` → `ordenamiento_insercion`, empleado en árbol ISBN, listas de usuarios, catálogo, historial y recomendaciones.
- `unicodedata`/`.casefold()` → `a_minusculas` y `normalizar` mediante mapeo de caracteres.
- `datetime.date` y `timedelta` → `core/calendario.py` con funciones de suma, validación y diferencia de días gregorianos. `time` solamente consulta el reloj local.
- `sum`, `any`, `all`, `max`, `zip` en la lógica → recorridos propios con bucles y acumuladores.

**Resultados de pruebas ejecutadas en esta versión:** 24 pruebas funcionales, 77 validaciones de integridad, 65 pruebas de algoritmos manuales, 16 renderizados Jinja y compilación de todos los módulos Python. La ejecución HTTP con Flask todavía se marca como pendiente mientras la dependencia no esté disponible en el entorno; en la computadora del estudiante se ejecuta con `python verificar.py` tras instalar Flask.

La complejidad del ordenamiento del catálogo y de construir el BST cambió a **O(n²)** en el peor caso (inserción propia). BFS mantiene **O(V+E)**; el ordenamiento final de sus hallazgos es **O(V²)** con inserción. El heap propio conserva **O(k)** para construirlo y **O(log k)** para cada extracción.
