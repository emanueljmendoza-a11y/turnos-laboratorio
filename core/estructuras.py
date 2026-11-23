"""Estructuras originales con algoritmos hechos a mano, solo funciones.

- Ordenamiento por inserción, sin sorted() ni .sort().
- Montículo mínimo de arreglo, sin heapq.
- BFS con cola de lista e índice, sin deque.
- Normalización con un mapa de caracteres, sin unicodedata/casefold.
- Árbol BST balanceado y grafo de listas de adyacencia.
"""

from core.calendario import diferencia_dias, fecha_hoy


# Correspondencias 1 a 1; conserva la Ñ como n para búsquedas sin tildes.
_MAYUSCULAS = "ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ"
_MINUSCULAS = "abcdefghijklmnopqrstuvwxyzáéíóúüñ"
_CON_TILDE = "áéíóúüñ"
_SIN_TILDE = "aeiouun"


def a_minusculas(texto):
    """Conversión manual de letras latinas mayúsculas; conserva las tildes."""
    resultado = []
    for caracter in str(texto):
        reemplazo = caracter
        for indice in range(len(_MAYUSCULAS)):
            if caracter == _MAYUSCULAS[indice]:
                reemplazo = _MINUSCULAS[indice]
                break
        resultado.append(reemplazo)
    return "".join(resultado)


def normalizar(texto):
    """Convierte a minúsculas y reemplaza acentos escritos y combinantes."""
    resultado = []
    for caracter in a_minusculas(texto):
        if caracter in "\u0301\u0308\u0303":  # tildes Unicode separadas
            continue
        reemplazo = caracter
        for indice in range(len(_CON_TILDE)):
            if caracter == _CON_TILDE[indice]:
                reemplazo = _SIN_TILDE[indice]
                break
        resultado.append(reemplazo)
    return "".join(resultado)


def ordenamiento_insercion(elementos, clave=None, inverso=False):
    """Ordena una COPIA con inserción. O(n²) peor caso; O(n) mejor caso.

    No usa sort/sorted, muta solamente la copia y es estable para claves iguales.
    """
    copia = elementos[:]
    if clave is None:
        clave = lambda elemento: elemento
    for i in range(1, len(copia)):
        actual = copia[i]
        llave_actual = clave(actual)
        j = i - 1
        while j >= 0:
            llave_j = clave(copia[j])
            debe_mover = llave_j < llave_actual if inverso else llave_j > llave_actual
            if not debe_mover:
                break
            copia[j + 1] = copia[j]
            j -= 1
        copia[j + 1] = actual
    return copia


def construir_arbol_isbn(libros):
    """Ordena por inserción O(n²) y forma un BST balanceado O(n)."""
    ordenados = ordenamiento_insercion(libros, clave=lambda libro: libro["isbn"])

    def construir(inicio, fin):
        if inicio > fin:
            return None
        medio = (inicio + fin) // 2
        return {
            "clave": ordenados[medio]["isbn"],
            "libro": ordenados[medio],
            "izquierda": construir(inicio, medio - 1),
            "derecha": construir(medio + 1, fin),
        }

    return construir(0, len(ordenados) - 1)


def buscar_en_arbol(raiz, isbn):
    """Búsqueda iterativa BST O(log n) tras construir el árbol."""
    actual = raiz
    while actual is not None:
        if isbn == actual["clave"]:
            return actual["libro"]
        if isbn < actual["clave"]:
            actual = actual["izquierda"]
        else:
            actual = actual["derecha"]
    return None


def buscar_lineal(libros, consulta):
    termino = normalizar(consulta.strip())
    resultados = []
    for libro in libros:
        datos_texto = libro["titulo"] + " " + libro["autor"] + " " + libro["categoria"] + " " + libro["isbn"]
        if termino in normalizar(datos_texto):
            resultados.append(libro)
    return resultados


def construir_grafo(libros):
    """Grafo no dirigido: se conectan libros por autor o categoría O(n²)."""
    grafo = {libro["id"]: [] for libro in libros}
    for i in range(len(libros)):
        for j in range(i + 1, len(libros)):
            a, b = libros[i], libros[j]
            puntos = 0
            if normalizar(a["autor"]) == normalizar(b["autor"]):
                puntos += 2
            if normalizar(a["categoria"]) == normalizar(b["categoria"]):
                puntos += 1
            if puntos:
                grafo[a["id"]].append((b["id"], puntos))
                grafo[b["id"]].append((a["id"], puntos))
    return grafo


def recomendar_bfs(libros, libro_id, limite=5):
    """Recorrido BFS O(V+E) más inserción O(V²) de recomendaciones."""
    grafo = construir_grafo(libros)
    if libro_id not in grafo or limite <= 0:
        return []
    indice = {libro["id"]: libro for libro in libros}
    cola = [(libro_id, 0)]
    siguiente = 0
    visitados = {libro_id}
    encontrados = []

    while siguiente < len(cola):
        actual, distancia = cola[siguiente]
        siguiente += 1
        for vecino, afinidad in grafo[actual]:
            if vecino in visitados:
                continue
            visitados.add(vecino)
            cola.append((vecino, distancia + 1))
            encontrados.append({
                "libro": indice[vecino],
                "distancia": distancia + 1,
                "afinidad": afinidad,
            })

    encontrados = ordenamiento_insercion(
        encontrados,
        clave=lambda item: (item["distancia"], -item["afinidad"], item["libro"]["titulo"]),
    )
    return encontrados[:limite]


def _hundir(monticulo, indice):
    """Repara hacia abajo un min-heap: O(log n)."""
    cantidad = len(monticulo)
    while True:
        izquierdo = 2 * indice + 1
        derecho = 2 * indice + 2
        menor = indice
        if izquierdo < cantidad and monticulo[izquierdo] < monticulo[menor]:
            menor = izquierdo
        if derecho < cantidad and monticulo[derecho] < monticulo[menor]:
            menor = derecho
        if menor == indice:
            break
        monticulo[indice], monticulo[menor] = monticulo[menor], monticulo[indice]
        indice = menor


def _subir(monticulo, indice):
    """Repara hacia arriba un min-heap: O(log n)."""
    while indice > 0:
        padre = (indice - 1) // 2
        if monticulo[padre] <= monticulo[indice]:
            break
        monticulo[padre], monticulo[indice] = monticulo[indice], monticulo[padre]
        indice = padre


def crear_monticulo(elementos):
    """Construcción bottom-up O(n), sin heapq.heapify."""
    monticulo = elementos[:]
    indice = len(monticulo) // 2 - 1
    while indice >= 0:
        _hundir(monticulo, indice)
        indice -= 1
    return monticulo


def insertar_monticulo(monticulo, elemento):
    """Inserción por subida O(log n)."""
    monticulo.append(elemento)
    _subir(monticulo, len(monticulo) - 1)


def extraer_minimo(monticulo):
    """Extrae la raíz de menor valor y repara el heap O(log n)."""
    if not monticulo:
        raise IndexError("No se puede extraer de un montículo vacío.")
    minimo = monticulo[0]
    ultimo = monticulo.pop()
    if monticulo:
        monticulo[0] = ultimo
        _hundir(monticulo, 0)
    return minimo


def heap_reservas_pendientes(reservas, libro_id):
    """Filtra O(r) y construye heap O(k), priorizado por fecha FIFO."""
    elementos = []
    for reserva in reservas:
        if reserva["libro_id"] == libro_id and reserva["estado"] == "pendiente":
            elementos.append((reserva["creada_en"], reserva["id"]))
    return crear_monticulo(elementos)


def reservas_por_prioridad(reservas, libro_id):
    monticulo = heap_reservas_pendientes(reservas, libro_id)
    por_id = {reserva["id"]: reserva for reserva in reservas}
    resultado = []
    while monticulo:
        _, reserva_id = extraer_minimo(monticulo)
        resultado.append(por_id[reserva_id])
    return resultado


def prestamos_vencidos_heap(prestamos, hoy=None):
    """Maximiza días vencidos mediante clave -dias en min-heap propio."""
    if hoy is None:
        hoy = fecha_hoy()
    # Permite en pruebas solo el texto ISO; evita depender de objetos datetime.
    if not isinstance(hoy, str):
        raise ValueError("El día de consulta debe ser AAAA-MM-DD.")
    elementos = []
    for prestamo in prestamos:
        if prestamo["devuelto_en"] is not None:
            continue
        dias = diferencia_dias(prestamo["vence_en"], hoy)
        if dias > 0:
            elementos.append((-dias, prestamo["vence_en"], prestamo["id"]))
    monticulo = crear_monticulo(elementos)
    resultado = []
    while monticulo:
        negativos, _, prestamo_id = extraer_minimo(monticulo)
        resultado.append((prestamo_id, -negativos))
    return resultado


def estadisticas_grafo(grafo):
    vertices = len(grafo)
    aristas = 0
    for vecinos in grafo.values():
        aristas += len(vecinos)
    return {"vertices": vertices, "aristas": aristas // 2}
