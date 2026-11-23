# Guía de defensa: algoritmos implementados manualmente

**Proyecto:** BiblioEstructuras v3.0 — Programación Estructurada en Python  
**Integrantes:** Jean Martinez, Emanuel Mendoza y Jorge Suarez.

La lógica propia usa **funciones, arreglos (listas), diccionarios, ciclos y condiciones**, sin clases creadas por el equipo. Las estructuras y algoritmos que se evalúan se desarrollaron desde cero. Se mantiene **Flask** para la web y **json** para los archivos, porque son servicios de infraestructura, no los algoritmos pedidos.

## 1. Montículo mínimo (min-heap) propio

**Archivo:** `core/estructuras.py`.

Un min-heap se representa con una lista. Para un elemento en posición `i`:

- Su padre está en `(i - 1) // 2`.
- Su hijo izquierdo está en `2 * i + 1`.
- Su hijo derecho está en `2 * i + 2`.
- El padre siempre es menor o igual que sus hijos.

**Funciones propias:** `_subir`, `_hundir`, `crear_monticulo`, `insertar_monticulo`, `extraer_minimo`.

**Ejemplo:** si los valores son `[7, 2, 5, 1]`, `crear_monticulo` devuelve una disposición que tiene `1` en la raíz (no tiene por qué estar toda ordenada). `extraer_minimo` retira `1`, coloca el último elemento en la raíz y lo hunde intercambiándolo con su hijo menor hasta recuperar la propiedad del heap.

**Para qué sirve en la biblioteca:**

- Reservas pendientes: tupla `(fecha_de_solicitud, id_reserva)`. Sale primero la solicitud más antigua.
- Préstamos vencidos: tupla `(-dias_de_atraso, fecha_vencimiento, id)`. El mayor atraso tiene la clave negativa más pequeña, así que sale primero.

**Complejidad:** construcción desde una lista: O(k); inserción: O(log k); extraer el mínimo: O(log k); memoria: O(k).

## 2. Cola manual para búsqueda en anchura (BFS)

**Archivo:** `core/estructuras.py`; función `recomendar_bfs`.

En lugar de `deque`, se crea `cola = [(libro_id, 0)]` y `siguiente = 0`. Mientras `siguiente < len(cola)`, se procesa `cola[siguiente]`, luego se incrementa `siguiente` y se agregan al final los vecinos nuevos. Esto evita quitar el primer elemento de la lista, operación que obligaría a desplazar los elementos restantes.

**Grafo:** cada libro es un vértice y dos libros están conectados cuando comparten autor o categoría. Una coincidencia de autor aporta dos puntos y una de categoría aporta uno.

**Cómo funciona BFS:** visita primero los libros a una conexión de distancia, después los de dos, etc.; usa `visitados` para no recorrer repetidamente un mismo libro.

**Complejidad:** BFS O(V+E), espacio de cola y visitados O(V); **además** se construye el grafo en O(n²) y se ordenan las recomendaciones por inserción en O(V²) en el peor caso.

## 3. Ordenamiento por inserción

**Archivo:** `core/estructuras.py`; función `ordenamiento_insercion`.

Se copia la lista para no modificar el original. Desde la posición 1, se guarda el elemento que debe insertarse, se recorren hacia atrás los anteriores y se desplazan a la derecha los que sean mayores. Se inserta el elemento en el hueco correcto.

**Ejemplo:** `[5, 2, 4]` se transforma en `[2, 5, 4]` y después en `[2, 4, 5]`.

Se usa para ordenar libros por título o ISBN, usuarios, préstamos, reservas y recomendaciones. Permite indicar una **clave** y orden descendente, y conserva el orden original si hay empates.

**Complejidad:** peor caso O(n²); mejor caso O(n) cuando está previamente ordenada; memoria auxiliar O(n) por la copia. Es menos eficiente que `sorted` para listas grandes, pero permite demostrar el algoritmo sin utilizarlo.

## 4. Árbol binario de búsqueda (BST)

**Archivo:** `core/estructuras.py`; funciones `construir_arbol_isbn` y `buscar_en_arbol`.

El catálogo se ordena por ISBN con inserción propia y se elige el elemento central como raíz. La mitad izquierda contiene claves menores y la derecha mayores. Este proceso recursivo produce un árbol aproximadamente balanceado. La búsqueda recorre solo una rama en cada paso.

**Complejidad:** ordenar O(n²) en el peor caso, construir nodos O(n), buscar en árbol ya construido O(log n). La búsqueda completa desde la interfaz web reconstruye primero el índice y, por ello, cuesta O(n²) en el peor caso. La estructura se implementa con diccionarios enlazados por claves `izquierda` y `derecha`.

## 5. Normalización propia de búsquedas

**Archivo:** `core/estructuras.py`; funciones `a_minusculas` y `normalizar`.

Se recorre el texto carácter a carácter. Un mapa fijo transforma `A-Z`, `ÁÉÍÓÚÜÑ` en sus correspondientes minúsculas. Otro mapa sustituye `áéíóúüñ` por `aeiouun`. También se ignoran marcas combinantes de tilde del español.

**Ejemplo:** `"ADMINISTRACIÓN"` se convierte en `"administracion"` y `"NIÑO"` en `"nino"`.

**Limitación:** está diseñada para español, no es un normalizador universal de todos los idiomas. Su complejidad es O(m) para textos de m caracteres porque el tamaño del mapa es constante.

## 6. Fechas y días de retraso sin datetime

**Archivo:** `core/calendario.py`.

- `es_bisiesto`: un año es bisiesto si es múltiplo de 400 o si es múltiplo de 4 pero no de 100.
- `fecha_a_dias`: valida el formato `AAAA-MM-DD`, comprueba que el día exista y calcula su ordinal desde el 1 de enero del año 1.
- `dias_a_fecha`: invierte el ordinal por búsqueda binaria del año y recorre los meses.
- `sumar_dias`: convierte a ordinal, suma días y convierte de nuevo.
- `diferencia_dias`: resta ordinales; si vence el 5 y hoy es 10, el atraso es de 5 días.
- `validar_fecha_hora`: comprueba de forma manual la fecha y hora ISO almacenada en JSON.

**Ejemplo:** `sumar_dias("2024-02-28", 2)` devuelve `"2024-03-01"` porque 2024 fue bisiesto.

La fecha y hora actuales se obtienen de `time.localtime` y `time.time_ns` (reloj del equipo). No se usa una biblioteca para **calcular**, validar o sumar fechas. El cálculo funciona con el calendario gregoriano extendido a años 1–9999.

## 7. Lectura y escritura JSON

**Archivo:** `core/datos.py`.

Los registros se guardan en listas de diccionarios: `libros`, `usuarios`, `prestamos`, `reservas`. `json.load` y `json.dump` se mantienen por ser el requisito de persistencia. Antes de guardar se comprueba la integridad y se utiliza un archivo temporal; al completarse la operación se reemplaza el original, disminuyendo el riesgo de corrupción.

## 8. Pruebas para demostrar al profesor

En la carpeta del proyecto:

```powershell
py tests/test_algoritmos_manual.py
py verificar.py
```

La suite manual verifica 65 casos: ordenamientos, empates y prioridades del heap, BFS, BST, mayúsculas y tildes, cálculos entre años (incluidos 1900 y 2000), fechas imposibles y ausencia de llamadas a las funciones algorítmicas prohibidas.

Si aún no se ha instalado Flask, las pruebas de lógica funcionan igualmente. Para levantar la interfaz:

```powershell
py -m pip install -r requirements.txt
py app.py
```

Abre `http://127.0.0.1:5000`.

## 9. Respuesta breve para defender «sin funciones predefinidas»

> Los algoritmos evaluados están hechos con funciones propias. Ordenamos con inserción, usamos un arreglo para el min-heap, una lista e índice para BFS, mapas de caracteres para normalizar búsquedas y aritmética gregoriana para fechas. No usamos `heapq`, `deque`, `sorted`, `unicodedata` ni `datetime`. Sí usamos funciones fundamentales de Python y los módulos Flask y JSON porque corresponden a la interfaz y al almacenamiento, no a las implementaciones de las estructuras de datos.
