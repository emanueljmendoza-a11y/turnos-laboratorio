"""Pruebas de los algoritmos manuales; no requieren Flask ni servidores.

Se usan ejemplos con respuesta conocida para verificar implementaciones propias.
"""

from pathlib import Path
import ast
import sys

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from core import calendario
from core.estructuras import (
    a_minusculas, normalizar, ordenamiento_insercion,
    construir_arbol_isbn, buscar_en_arbol, construir_grafo,
    recomendar_bfs, crear_monticulo, insertar_monticulo, extraer_minimo,
    heap_reservas_pendientes, reservas_por_prioridad, prestamos_vencidos_heap,
)

TOTAL = 0


def comprobar(condicion, mensaje):
    global TOTAL
    if not condicion:
        raise AssertionError(mensaje)
    TOTAL += 1
    print(f"[OK {TOTAL:02d}] {mensaje}")


def falla_valor(accion, mensaje):
    try:
        accion()
    except ValueError:
        comprobar(True, mensaje)
        return
    raise AssertionError(mensaje)


def probar_ordenamientos():
    entrada = [8, -2, 8, 0, 3, 1, 99, -7]
    comprobar(ordenamiento_insercion(entrada) == [-7, -2, 0, 1, 3, 8, 8, 99], "Inserción ascendente")
    comprobar(ordenamiento_insercion(entrada, inverso=True) == [99, 8, 8, 3, 1, 0, -2, -7], "Inserción descendente")
    comprobar(entrada == [8, -2, 8, 0, 3, 1, 99, -7], "La lista original no se modifica")
    comprobar(ordenamiento_insercion([]) == [] and ordenamiento_insercion([4]) == [4], "Listas vacías y unitarias")
    personas = [{"nombre": "B", "nota": 10}, {"nombre": "A", "nota": 9}, {"nombre": "C", "nota": 10}]
    salida = ordenamiento_insercion(personas, clave=lambda p: p["nota"])
    comprobar([x["nombre"] for x in salida] == ["A", "B", "C"], "Ordenamiento estable con clave")


def probar_textos():
    comprobar(a_minusculas("ÁRBOL Niño MÉXICO") == "árbol niño méxico", "Minúsculas con mapa propio")
    comprobar(normalizar("ÁÉÍÓÚ Ü Ñ") == "aeiou u n", "Mapa de vocales y eñe")
    comprobar(normalizar("Cancio\u0301n") == "cancion", "Acentos combinantes")
    comprobar(normalizar("ADMINISTRACIÓN") == "administracion", "Normalización de consultas")


def probar_heaps():
    numeros = [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    monticulo = crear_monticulo(numeros)
    comprobar(numeros[0] == 9 and monticulo[0] == 0, "Heapify hecho a mano sin alterar el origen")
    resultado = []
    while monticulo:
        resultado.append(extraer_minimo(monticulo))
    comprobar(resultado == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], "Hundimiento y extracción ordenada")
    monticulo = []
    for elemento in (3, -5, 3, 11, -2):
        insertar_monticulo(monticulo, elemento)
    salida = []
    while monticulo:
        salida.append(extraer_minimo(monticulo))
    comprobar(salida == [-5, -2, 3, 3, 11], "Subida, negativos y empates")
    try:
        extraer_minimo([])
    except IndexError:
        comprobar(True, "No extrae de un heap vacío")
    else:
        raise AssertionError("Heap vacío debía fallar")
    # Prueba grande: el arreglo sigue el orden de prioridad con claves negativas.
    grande = crear_monticulo([(-i, i) for i in range(500)])
    comprobar(extraer_minimo(grande) == (-499, 499), "Min-heap maneja 500 prioridades")
    reserva = [
        {"id": "R3", "libro_id": "A", "creada_en": "2026-01-02T10:00:00", "estado": "pendiente"},
        {"id": "R2", "libro_id": "B", "creada_en": "2026-01-01T00:00:00", "estado": "pendiente"},
        {"id": "R1", "libro_id": "A", "creada_en": "2026-01-01T10:00:00", "estado": "pendiente"},
        {"id": "R4", "libro_id": "A", "creada_en": "2026-01-01T10:00:00", "estado": "pendiente"},
        {"id": "R0", "libro_id": "A", "creada_en": "2025-01-01T10:00:00", "estado": "cancelada"},
    ]
    h = heap_reservas_pendientes(reserva, "A")
    comprobar(len(h) == 3 and h[0][1] == "R1", "Reservas filtran por libro y estado")
    comprobar([r["id"] for r in reservas_por_prioridad(reserva, "A")] == ["R1", "R4", "R3"], "Reservas FIFO y desempate por ID")
    prestamos = [
        {"id": "P2", "vence_en": "2026-01-07", "devuelto_en": None},
        {"id": "P1", "vence_en": "2026-01-05", "devuelto_en": None},
        {"id": "P3", "vence_en": "2026-01-03", "devuelto_en": "2026-01-04"},
        {"id": "P4", "vence_en": "2026-01-10", "devuelto_en": None},
    ]
    comprobar(prestamos_vencidos_heap(prestamos, "2026-01-10") == [("P1", 5), ("P2", 3)], "Vencimientos descartan devueltos y futuros")


def probar_bst_y_grafos():
    libros = [
        {"id": "C", "isbn": "003", "titulo": "C", "autor": "Juan", "categoria": "Ciencia"},
        {"id": "A", "isbn": "001", "titulo": "A", "autor": "Ana", "categoria": "Ciencia"},
        {"id": "E", "isbn": "005", "titulo": "E", "autor": "Pedro", "categoria": "Drama"},
        {"id": "D", "isbn": "004", "titulo": "D", "autor": "Juan", "categoria": "Drama"},
        {"id": "B", "isbn": "002", "titulo": "B", "autor": "Ana", "categoria": "Ciencia"},
    ]
    raiz = construir_arbol_isbn(libros)
    comprobar(raiz["clave"] == "003", "La raíz usa el índice medio balanceado")
    comprobar(buscar_en_arbol(raiz, "001")["id"] == "A" and buscar_en_arbol(raiz, "005")["id"] == "E", "BST encuentra hojas")
    comprobar(buscar_en_arbol(raiz, "006") is None, "BST rechaza clave ausente")
    grafo = construir_grafo(libros)
    comprobar(len(grafo["A"]) == 2 and len(grafo["E"]) == 1, "Grafo construido por autor y categoría")
    items = recomendar_bfs(libros, "A", limite=10)
    comprobar([r["libro"]["id"] for r in items] == ["B", "C", "D", "E"], "BFS visita vecinos y niveles sucesivos")
    comprobar([r["distancia"] for r in items] == [1, 1, 2, 3], "BFS guarda distancia mínima")
    comprobar(recomendar_bfs(libros, "NO EXISTE") == [], "BFS rechaza identificador inexistente")
    comprobar(recomendar_bfs(libros, "A", limite=2)[0]["libro"]["id"] == "B", "Recomendaciones priorizan afinidad")


def probar_calendario():
    comprobar(calendario.fecha_a_dias("0001-01-01") == 1, "Origen del calendario gregoriano")
    comprobar(calendario.es_bisiesto(2000) and not calendario.es_bisiesto(1900), "Regla siglos y múltiplos de 400")
    comprobar(calendario.es_bisiesto(2024) and not calendario.es_bisiesto(2025), "Bisiestos del año común")
    comprobar(calendario.diferencia_dias("2024-02-28", "2024-03-01") == 2, "Diferencia sobre febrero bisiesto")
    comprobar(calendario.diferencia_dias("1900-02-28", "1900-03-01") == 1, "Diferencia sobre siglo no bisiesto")
    comprobar(calendario.sumar_dias("1999-12-31", 60) == "2000-02-29", "Suma cruzando el año 2000")
    comprobar(calendario.sumar_dias("2024-03-01", -2) == "2024-02-28", "Resta días con año bisiesto")
    comprobar(calendario.sumar_dias("2026-12-29", 14) == "2027-01-12", "Vencimiento cruzando de año")
    for fecha in ("0001-01-01", "0004-02-29", "0100-02-28", "0400-02-29", "1582-10-15", "1900-03-01", "2000-02-29", "2024-12-31", "9999-12-31"):
        comprobar(calendario.dias_a_fecha(calendario.fecha_a_dias(fecha)) == fecha, f"Ida y vuelta: {fecha}")
    for invalida in ("2025-02-29", "1900-02-29", "2026-13-01", "2026-00-01", "2026-04-31", "2026-1-10", "2026-01-1", "0000-01-01", "2026-02-30", "abcd-12-01"):
        falla_valor(lambda v=invalida: calendario.fecha_a_dias(v), f"Fecha inválida: {invalida}")
    comprobar(calendario.validar_fecha_hora("2026-11-20T07:30:00.000001"), "ISO con microsegundos")
    comprobar(calendario.validar_fecha_hora("2026-11-20T07:30:00"), "ISO sin fracción")
    for invalida in ("2026-02-29T10:00:00", "2026-11-20T25:00:00", "2026-11-20T10:66:00", "2026-11-20T10:10:65", "2026-11-20T10:00:00."):
        falla_valor(lambda v=invalida: calendario.validar_fecha_hora(v), f"Timestamp inválido: {invalida}")
    comprobar(len(calendario.fecha_hoy()) == 10 and len(calendario.fecha_hora_actual()) == 26, "Consulta reloj compatible con JSON")


def probar_ausencia_de_atajos():
    prohibidos = {"heapq", "deque", "unicodedata", "datetime", "date", "timedelta"}
    llamadas_prohibidas = {"sorted", "sum", "any", "all", "max", "min", "zip"}
    for ruta in (RAIZ / "core/estructuras.py", RAIZ / "core/calendario.py", RAIZ / "core/biblioteca.py", RAIZ / "core/datos.py", RAIZ / "app.py"):
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Import):
                for alias in nodo.names:
                    if alias.name.split(".")[0] in prohibidos:
                        raise AssertionError(f"Import prohibido en {ruta.name}: {alias.name}")
            if isinstance(nodo, ast.ImportFrom):
                if (nodo.module or "").split(".")[0] in prohibidos:
                    raise AssertionError(f"Módulo prohibido en {ruta.name}: {nodo.module}")
            if isinstance(nodo, ast.Call):
                if isinstance(nodo.func, ast.Name) and nodo.func.id in llamadas_prohibidas:
                    raise AssertionError(f"Función predefinida prohibida en {ruta.name}: {nodo.func.id}")
                if isinstance(nodo.func, ast.Attribute) and nodo.func.attr in ("sort", "casefold", "heappop", "heapify"):
                    raise AssertionError(f"Método prohibido en {ruta.name}: {nodo.func.attr}")
        comprobar(True, f"Sin funciones algorítmicas prohibidas en {ruta.name}")


def ejecutar_pruebas():
    probar_ordenamientos()
    probar_textos()
    probar_heaps()
    probar_bst_y_grafos()
    probar_calendario()
    probar_ausencia_de_atajos()
    print(f"\nRESULTADO: {TOTAL} comprobaciones de algoritmos manuales correctas.")


if __name__ == "__main__":
    ejecutar_pruebas()
