# BiblioEstructuras — Proyecto final de Programación Estructurada

**Versión 3.0 — algoritmos manuales (noviembre de 2026).** Sistema de gestión de biblioteca elaborado con **Python (funciones, sin clases propias), Flask, HTML, CSS y archivos JSON**. Todos los datos, validaciones, búsquedas, algoritmos y operaciones se gestionan en Python. HTML/CSS muestran la interfaz en el navegador. No utiliza base de datos externa ni JavaScript para ejecutar la lógica de negocio.

## Requisitos

- Python 3.10 o posterior.
- Flask (única dependencia externa; el resto usa funciones propias y módulos estándar para JSON, hora actual, seguridad y archivos).

## Instalar y ejecutar en Windows (PowerShell)

Descomprime el ZIP y abre una terminal **dentro de la carpeta `biblioteca_estructurada`**, donde está `app.py`.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Si PowerShell bloquea la activación, puedes usar directamente:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

Abre **http://127.0.0.1:5000** en tu navegador. Para detener, pulsa `Ctrl + C`.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

## ¿Qué incluye?

- Panel con estadísticas y préstamos vencidos priorizados.
- Catálogo: añadir, editar, eliminar (si no tiene historial), buscar por título/autor/ISBN y filtrar por categoría.
- Usuarios: registrar, consultar, editar y eliminar lectores sin movimientos históricos.
- Préstamos: prestar, ver historial, devolver, límite de 3 préstamos activos por persona y duración de 14 días.
- Reservas: cuando no hay copias libres, solicitar turno; al devolver un libro, se aparta automáticamente para quien reservó primero; cancelar y recoger la reserva mediante un nuevo préstamo.
- Recomendaciones mediante un grafo y BFS con **cola implementada como lista + índice**, sin `deque`.
- Montículo mínimo construido manualmente con arreglo (`crear_monticulo`, `insertar_monticulo`, `extraer_minimo`) y sin `heapq`.
- Ordenamiento por inserción propio para catálogo, usuarios, reservas y recomendaciones; sin `sorted()` ni `.sort()`.
- Normalización manual de tildes y mayúsculas y fechas calculadas por aritmética del calendario gregoriano; sin `unicodedata`, `casefold()` ni `datetime`.
- Página **Estructuras y Big O** para explicar la complejidad de cada operación, con cantidades reales del grafo.
- Guardado persistente en `data/biblioteca.json` con escritura atómica, comprobación de referencias y bloqueo entre hilos.
- Validación de ISBN-10 (incluyendo X) e ISBN-13 mediante dígitos de control, fechas, correos, cantidades y reglas de integridad.
- Descarga de respaldo desde **Descargar respaldo JSON** en el menú lateral (incluye datos de usuarios; consérvalo de forma privada).
- Un enlace **Prestar** junto a las reservas listas completa más fácilmente la recogida de libros.

En el **primer inicio** se crean automáticamente diez libros, tres lectores, un préstamo vencido y una reserva pendiente para probar el flujo. El archivo JSON **no se sobrescribe** en los siguientes inicios. Si deseas reiniciar los ejemplos, detén el servidor, haz una copia de seguridad y elimina `data/biblioteca.json`; luego vuelve a iniciar.

## Ejemplo para demostrar las reservas

1. Abre el panel. El libro **1984** aparece prestado a Ana y con vencimiento pasado.
2. En la sección **Reservas** verás una solicitud `pendiente` de Carlos para **1984**.
3. Ve a **Préstamos**, pulsa **Devolver** en el préstamo de 1984.
4. Regresa a **Reservas**: la solicitud de Carlos cambia a **lista para recoger**. La copia se aparta para él.
5. Ve a **Nuevo préstamo**, selecciona Carlos y 1984. Al guardar, la reserva pasa a **cumplida**.

## Estructura del proyecto

```text
biblioteca_estructurada/
├── app.py                      # Rutas y formularios Flask
├── core/
│   ├── __init__.py
│   ├── estructuras.py          # BST, BFS manual, grafo, heap propio y ordenamiento
│   ├── calendario.py            # Fechas y diferencias con aritmética gregoriana
│   ├── biblioteca.py           # Reglas del negocio, solo funciones
│   └── datos.py                # Persistencia JSON
├── data/
│   ├── ejemplo_biblioteca.json # JSON de referencia incluido
│   └── biblioteca.json         # Se genera en el primer inicio
├── templates/                  # Interfaz HTML con Jinja
├── static/
│   └── estilos.css             # Estilos responsivos
├── tests/
│   ├── test_sistema.py         # 24 verificaciones funcionales
│   ├── test_validaciones.py    # 77 verificaciones adicionales
│   ├── test_algoritmos_manual.py # 65 pruebas de algoritmos escritos a mano
│   ├── test_plantillas.py      # 16 renderizados Jinja2
│   └── test_flask.py           # Pruebas de HTTP con Flask instalado
├── ANALISIS_BIG_O.md           # Explicación de estructuras y complejidades
├── ALGORITMOS_IMPLEMENTADOS_A_MANO.md # Guía de defensa de cada algoritmo
├── VALIDACIONES_Y_MEJORAS.md   # Cambios, pruebas ejecutadas y pruebas pendientes
├── verificar.py                # Ejecuta todas las suites de prueba
└── requirements.txt
```

## ¿Dónde están las estructuras?

| Estructura | Archivo | Funciones |
| --- | --- | --- |
| Listas de diccionarios | `core/biblioteca.py` | `listar_libros`, `listar_prestamos`, `listar_usuarios` |
| Árbol binario de búsqueda (BST) | `core/estructuras.py` | `construir_arbol_isbn`, `buscar_en_arbol` |
| Grafo por listas de adyacencia | `core/estructuras.py` | `construir_grafo`, `recomendar_bfs` |
| Montículos | `core/estructuras.py` | `crear_monticulo`, `insertar_monticulo`, `extraer_minimo`, `heap_reservas_pendientes`, `prestamos_vencidos_heap` |
| Ordenamiento por inserción | `core/estructuras.py` | `ordenamiento_insercion` |
| Cola BFS | `core/estructuras.py` | `recomendar_bfs` (lista e índice) |
| Aritmética del calendario | `core/calendario.py` | `fecha_a_dias`, `dias_a_fecha`, `sumar_dias`, `diferencia_dias` |
| JSON | `core/datos.py` | `leer`, `cambiar`, `guardar_sin_bloqueo` |
| Big O | `ANALISIS_BIG_O.md` y `/algoritmos` | Costos teóricos y explicación |

**Nota académica:** el árbol BST se construye desde una lista ordenada cuando se busca un ISBN completo; esto evita degeneraciones, pero la construcción cuesta O(n²) en el peor caso. Por lo tanto, la búsqueda *dentro de un árbol ya construido* cuesta O(log n), pero la operación web total que reconstruye el índice cuesta O(n²) en el peor caso. El grafo también se reconstruye desde el catálogo, con O(n²), antes del recorrido BFS.

## Ejecutar las pruebas

```bash
python tests/test_sistema.py
```

Puedes ejecutar todas las pruebas juntas con:

```bash
python verificar.py
```

O ejecutarlas de manera individual:

```bash
python tests/test_validaciones.py
python tests/test_algoritmos_manual.py
python tests/test_plantillas.py
python tests/test_flask.py
```

Las suites de lógica usan datos temporales y no modifican la biblioteca real. `test_plantillas.py` requiere Jinja2, incluido al instalar Flask. La prueba `test_flask.py` usa el cliente HTTP de pruebas de Flask y comprueba rutas, formularios, protección CSRF, exportación y cabeceras. Si Flask no está instalado, el script informa que no pudo ejecutarse.

En la revisión v3 se ejecutaron correctamente **24 comprobaciones básicas + 77 ampliadas + 65 de algoritmos manuales + 16 renderizaciones**, además de la compilación de los módulos. Las pruebas HTTP reales quedaron sin ejecutar en el entorno de revisión por falta de Flask y acceso a la descarga de paquetes; deben realizarse tras instalar `requirements.txt`.

## Alcance y limitaciones

Aplicación **académica para ejecución local** en `127.0.0.1` con el servidor de desarrollo de Flask. Los formularios POST tienen tokens CSRF y la interfaz incluye cabeceras defensivas, pero eso no reemplaza la autenticación. No incluye inicio de sesión, roles, respaldos automáticos (sí permite exportación manual) ni edición simultánea desde múltiples procesos o servidores. Se utiliza un bloqueo y escritura atómica para solicitudes dentro del mismo proceso. **No debe exponerse a Internet sin agregar autenticación, autorización y una base de datos/almacenamiento preparado para concurrencia.**


## Qué significa «sin funciones predefinidas» en esta versión

Las **estructuras, ordenamientos, recorridos y cálculos de fechas** se programaron mediante funciones, `for`, `while`, condicionales, listas y diccionarios. No aparecen en la lógica ni `heapq`, `deque`, `sorted`, `.sort`, `unicodedata`, `.casefold`, `datetime`, `timedelta`, `sum`, `any`, `all`, `max` o `zip`.

**No** significa «Python sin biblioteca estándar»: `json` se mantiene porque el proyecto necesita archivos JSON; `time.localtime` permite leer el reloj del equipo (las operaciones sobre fechas son propias); `re` valida formularios y `uuid` crea identificadores. Flask y Jinja sirven únicamente como tecnología web. El código usa operaciones fundamentales como `len`, `range`, `.append`, `.pop`, listas y diccionarios.

### Importante para el análisis Big O

Se eligió **ordenamiento por inserción**, fácil de explicar con ciclos. Ordenar y construir el BST desde cero pasa a **O(n²)** en el peor caso; buscar en un BST ya construido sigue siendo **O(log n)**. El BFS solo requiere **O(V+E)**, pero las recomendaciones luego se ordenan por inserción en **O(V²)** en el peor caso. La página de algoritmos y `ANALISIS_BIG_O.md` ya lo reflejan.
