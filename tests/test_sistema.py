"""Pruebas estructuradas sin clases, dependencias externas ni servidor.

Desde la raíz: python tests/test_sistema.py
"""

from pathlib import Path
from tempfile import TemporaryDirectory
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import biblioteca, datos
from core.estructuras import (
    buscar_en_arbol, construir_arbol_isbn, construir_grafo,
    heap_reservas_pendientes, prestamos_vencidos_heap, recomendar_bfs,
)


def comprobar(condicion, mensaje):
    if not condicion:
        raise AssertionError(mensaje)
    print("[OK]", mensaje)


def debe_fallar(accion, mensaje):
    try:
        accion()
    except ValueError:
        print("[OK]", mensaje)
        return
    raise AssertionError(mensaje)


def probar_estructuras():
    base = datos.leer()
    arbol = construir_arbol_isbn(base["libros"])
    encontrado = buscar_en_arbol(arbol, "9780451524935")
    comprobar(encontrado["titulo"] == "1984", "Árbol BST encuentra ISBN exacto")
    comprobar(buscar_en_arbol(arbol, "9999999999") is None, "BST devuelve None si ISBN falta")
    grafo = construir_grafo(base["libros"])
    comprobar("LIB005" in [id_ for id_, _ in grafo["LIB004"]], "Grafo conecta libros del mismo autor")
    recomendaciones = recomendar_bfs(base["libros"], "LIB004")
    comprobar(len(recomendaciones) >= 2, "BFS descubre recomendaciones")
    vencidos = prestamos_vencidos_heap(base["prestamos"])
    comprobar(vencidos[0][0] == "PRE001" and vencidos[0][1] > 0, "Heap prioriza préstamo vencido")
    heap = heap_reservas_pendientes(base["reservas"], "LIB004")
    comprobar(heap[0][1] == "RES001", "Heap contiene reserva pendiente")


def probar_ciclo_prestamo_reserva():
    comprobar(biblioteca.obtener_libro("LIB004")["disponibles"] == 0, "Libro agotado sin existencias libres")
    debe_fallar(
        lambda: biblioteca.crear_prestamo("USU003", "LIB004"),
        "Se rechaza préstamo si el libro está agotado",
    )
    libro_id = biblioteca.devolver_prestamo("PRE001")
    comprobar(libro_id == "LIB004", "La devolución devuelve el identificador del libro")
    reservas = biblioteca.listar_reservas()
    comprobar(any(r["id"] == "RES001" and r["estado"] == "lista" for r in reservas), "Se asigna la primera reserva automáticamente")
    comprobar(biblioteca.obtener_libro("LIB004")["disponibles"] == 0, "Una copia apartada no se ofrece al público")
    debe_fallar(
        lambda: biblioteca.crear_prestamo("USU003", "LIB004"),
        "No se puede quitar la copia a quien la reservó",
    )
    prestamo_id = biblioteca.crear_prestamo("USU002", "LIB004")
    comprobar(any(r["id"] == "RES001" and r["estado"] == "cumplida" for r in biblioteca.listar_reservas()), "Recoger libro cumple la reserva")
    biblioteca.devolver_prestamo(prestamo_id)
    comprobar(biblioteca.obtener_libro("LIB004")["disponibles"] == 1, "La devolución restablece el ejemplar")


def probar_orden_prioridad():
    id_prestamo = biblioteca.crear_prestamo("USU001", "LIB010")
    r1 = biblioteca.crear_reserva("USU002", "LIB010")
    r2 = biblioteca.crear_reserva("USU003", "LIB010")
    biblioteca.devolver_prestamo(id_prestamo)
    por_id = {r["id"]: r for r in biblioteca.listar_reservas()}
    comprobar(por_id[r1]["estado"] == "lista" and por_id[r2]["estado"] == "pendiente", "Primera reserva recibe prioridad FIFO")
    biblioteca.cancelar_reserva(r1)
    por_id = {r["id"]: r for r in biblioteca.listar_reservas()}
    comprobar(por_id[r1]["estado"] == "cancelada" and por_id[r2]["estado"] == "lista", "Cancelar reserva libera y reasigna al siguiente")
    recibido = biblioteca.crear_prestamo("USU003", "LIB010")
    comprobar(bool(recibido), "El segundo usuario recoge su reserva")
    debe_fallar(
        lambda: biblioteca.crear_prestamo("USU003", "LIB010"),
        "No se permite préstamo doble del mismo título al mismo usuario",
    )


def probar_catalogo():
    formulario = {
        "isbn": "0306406152", "titulo": "Algoritmos prácticos",
        "autor": "Autora de prueba", "categoria": "Informática",
        "anio": "2026", "ejemplares": "2", "descripcion": "Creado por pruebas.",
    }
    nuevo = biblioteca.crear_libro(formulario)
    comprobar(biblioteca.obtener_libro(nuevo)["titulo"] == "Algoritmos prácticos", "Alta de libro persistida en JSON")
    encontrados, _ = biblioteca.listar_libros("0306406152")
    comprobar(len(encontrados) == 1 and encontrados[0]["id"] == nuevo, "Buscar ISBN del libro recién creado")
    debe_fallar(lambda: biblioteca.crear_libro(formulario), "ISBN duplicado rechazado")
    biblioteca.editar_libro(nuevo, {**formulario, "titulo": "Algoritmos avanzados", "ejemplares": "3"})
    comprobar(biblioteca.obtener_libro(nuevo)["ejemplares"] == 3, "Edición de ejemplares guardada")
    biblioteca.eliminar_libro(nuevo)
    comprobar(not biblioteca.listar_libros("0306406152")[0], "Eliminación sin historial permitida")
    debe_fallar(lambda: biblioteca.eliminar_libro("LIB004"), "No se elimina libro con historial de préstamos")


def ejecutar_pruebas():
    ruta_original = datos.RUTA_DATOS
    with TemporaryDirectory() as carpeta:
        datos.RUTA_DATOS = Path(carpeta) / "biblioteca.json"
        try:
            probar_estructuras()
            probar_ciclo_prestamo_reserva()
            probar_orden_prioridad()
            probar_catalogo()
        finally:
            datos.RUTA_DATOS = ruta_original
    print("\nTodas las pruebas terminaron correctamente.")


if __name__ == "__main__":
    ejecutar_pruebas()
