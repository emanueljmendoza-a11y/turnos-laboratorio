# Análisis de notación asintótica — BiblioEstructuras

## Variables

- **n**: número de libros / tamaño del archivo o de una colección según el contexto.
- **V**: cantidad de vértices (libros) del grafo.
- **E**: cantidad de aristas (relaciones) del grafo.
- **k**: número de reservas pendientes para un mismo libro.
- **p**: número de préstamos activos o históricos según la operación.
- **r**: número total de reservas.
- **u**: número de usuarios.
- **s**: tamaño del JSON serializado en caracteres o bytes.

## 1. Listas

Los datos del JSON son **listas** de diccionarios. Agregar un libro a una lista es O(1) amortizado. Recorrer una lista para buscar un título o un usuario por identificador es **O(n)** en el peor caso. El filtrado por categoría recorre los libros, **O(n)**.

## 2. Árbol binario de búsqueda balanceado

Se ordena el catálogo por ISBN y se usa el elemento central como raíz, repitiendo el proceso con cada mitad. Ordenar por inserción propio cuesta **O(n²)** en el peor caso y construir los nodos con las mitades **O(n)**. El costo combinado de construir el índice es **O(n²)** en el peor caso. La altura del árbol queda en **O(log n)** y buscar un ISBN exacto sobre ese índice es **O(log n)**. **Limitación:** el índice no se mantiene entre peticiones, así que para cada búsqueda el costo total es **O(n²)** en el peor caso. No se debe afirmar que todo el proceso web cuesta O(log n).

## 3. Grafos + BFS

Cada libro es un vértice y se conectan dos libros si comparten autor y/o categoría. Comparar todos los pares lleva **O(n²)** y el grafo se almacena como diccionario de listas de vecinos. BFS explora cada vértice y cada arista como máximo un número constante de veces: **O(V+E)**. Tras BFS, las recomendaciones halladas se ordenan por distancia, afinidad y título: **O(V²)** en el peor caso (inserción propia). Además, se reconstruye el grafo por petición (**O(n²)**). Con un catálogo grande conviene reutilizar el grafo y agrupar libros por autor/categoría. La **cola de BFS** es una lista con un índice de lectura: insertar al final cuesta O(1) amortizado y avanzar el índice cuesta O(1), sin `deque` ni desplazamientos O(n).

## 4. Montículos (heaps)

Se emplea un **montículo mínimo programado a mano** en `core/estructuras.py`, representado por una lista. Se implementan las funciones `_subir`, `_hundir`, `crear_monticulo`, `insertar_monticulo` y `extraer_minimo`:

- Filtrar todas las reservas para obtener las k pendientes de un título cuesta **O(r)**.
- `crear_monticulo(elementos)`: construcción desde el último nodo interior y hundimiento de cada uno en **O(k)**. Por tanto `heap_reservas_pendientes()` completa cuesta **O(r+k)**.
- `extraer_minimo(monticulo)`: retira la raíz, pone el último elemento arriba y la hunde en **O(log k)**. `insertar_monticulo()` añade al final y hace subir el nuevo elemento en **O(log k)**.
- Para reservas: prioridad por fecha más antigua, usando tuplas `(creada_en, id)`.
- Para vencimientos: prioridad por *más días de atraso*, usando `(-dias, fecha, id)`.
- Extraer **todas** las reservas de un libro, una por una, cuesta **O(k log k)** tras construir el heap. `prestamos_vencidos_heap()` construye otro heap manual sobre préstamos vencidos.

## 5. Persistencia JSON

`json.load()` y `json.dump()` procesan todo el contenido, por tanto son **O(s)** en tiempo y memoria en función del tamaño del JSON, no de una sola entidad. Cada modificación escribe de nuevo el archivo completo. La validación de integridad es **O(n+u+p+r)** en promedio, gracias a conjuntos y diccionarios. Es una elección sencilla y defendible para un proyecto académico.

## 6. Optimización adicional: ocupación de ejemplares

En vez de recorrer todos los préstamos y reservas por cada libro de un catálogo, `_ocupacion_por_libro()` realiza una única pasada por libros, préstamos y reservas y acumula los ejemplares ocupados en un diccionario. Esto cuesta **O(n+p+r)** en tiempo y **O(n)** en memoria auxiliar. Luego obtener la disponibilidad de cada título es O(1) promedio. El catálogo aún ordena los libros por título en **O(n²)** en el peor caso.

`_asignar_reservas()` construye una cola de prioridad y consulta los ejemplares libres una sola vez. Asignar k reservas cuesta **O(n+p+r+k log k)** en tiempo aproximado, incluida la construcción de sus índices.

## 7. Complejidad espacial

- Listas: **O(n)**.
- Árbol BST: **O(n)** nodos, además de la lista ordenada.
- Grafo: **O(V + E)**, con hasta **O(n²)** aristas si todos los libros comparten una categoría.
- Heap: **O(k)**.

## 8. Ejemplos de explicación ante el profesor

**Pregunta:** ¿Por qué no buscas el ISBN con una lista?

**Respuesta:** la lista requiere comparar hasta n registros, O(n). Al construir el BST balanceado, la búsqueda sobre el índice toma O(log n). Sin embargo, reconstruir el árbol antes de cada petición implica O(n²) en el peor caso; es una comparación de costos con y sin índice persistente.

**Pregunta:** ¿Dónde intervienen los grafos?

**Respuesta:** cada libro es un nodo y una arista indica autor/categoría común. BFS descubre libros relacionados y su distancia en la red.

**Pregunta:** ¿Qué problema resuelve un heap?

**Respuesta:** elegir la reserva más antigua o el préstamo más atrasado sin tener que reordenar toda la lista después de cada extracción.

**Pregunta:** ¿Qué pasa al cerrar la app?

**Respuesta:** la información queda en `data/biblioteca.json` y se recupera al iniciarla de nuevo.

## 9. Algoritmos sin funciones de ordenamiento ni fecha predefinidas

- `ordenamiento_insercion(lista, clave, inverso)`: recorre los elementos desde la segunda posición y desplaza los mayores hacia la derecha. Peor caso **O(n²)**, mejor **O(n)** para una lista ya ordenada; memoria extra **O(n)** porque ordena una copia.
- `normalizar(texto)`: compara cada carácter con dos mapas estáticos de letras. Dado que el alfabeto usado tiene tamaño fijo, cuesta **O(m)** para un texto de m caracteres.
- `fecha_a_dias(fecha)`: comprueba fecha gregoriana y calcula un ordinal con fórmula de bisiestos. `dias_a_fecha()` busca el año con una búsqueda binaria en el rango fijo 1–9999, después recorre hasta 12 meses. No usa módulos de cálculo de fechas. `time.localtime` solo aporta el **día y la hora actuales** desde el reloj.
- `diferencia_dias(desde, hasta)`: resta los dos ordinales para calcular mora; `sumar_dias` suma al ordinal y vuelve a fecha ISO.

**Importante:** la versión 3.0 elige claridad pedagógica sobre el máximo rendimiento: ordenar por inserción es peor que un algoritmo O(n log n) para miles de libros. Los módulos JSON y Flask se mantienen, porque almacenar datos y mostrar la web son requisitos distintos de programar los algoritmos manuales.
