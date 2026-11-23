"""Pruebas de regresión sin librerías externas ni clases propias.

Desde la raíz: python tests/test_validaciones.py
Cada prueba usa un JSON temporal: nunca altera el archivo real del usuario.
"""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import biblioteca, datos
from core.estructuras import construir_arbol_isbn, buscar_en_arbol

VERIFICACIONES = 0


def comprobar(condicion, descripcion):
    global VERIFICACIONES
    if not condicion:
        raise AssertionError(descripcion)
    VERIFICACIONES += 1
    print(f"[OK {VERIFICACIONES:02d}] {descripcion}")


def debe_fallar(accion, descripcion, tipo=ValueError):
    try:
        accion()
    except tipo:
        comprobar(True, descripcion)
    else:
        raise AssertionError(descripcion)


def datos_aislados(prueba):
    anterior = datos.RUTA_DATOS
    with TemporaryDirectory() as carpeta:
        datos.RUTA_DATOS = Path(carpeta) / "datos.json"
        try:
            prueba()
        finally:
            datos.RUTA_DATOS = anterior


def formulario_libro(**cambios):
    base = {
        "isbn": "0306406152", "titulo": "Ciencia de pruebas", "autor": "Autora Pruebas",
        "categoria": "Tecnología", "anio": "2001", "ejemplares": "2",
        "descripcion": "Validaciones automáticas",
    }
    base.update(cambios)
    return base


def probar_validaciones_formulario():
    comprobar(biblioteca._isbn("0-306-40615-2") == "0306406152", "ISBN-10 con guiones aceptado")
    comprobar(biblioteca._isbn("978-0-451-52493-5") == "9780451524935", "ISBN-13 con guiones aceptado")
    comprobar(biblioteca._isbn("080442957X") == "080442957X", "ISBN-10 con dígito X aceptado")
    for isbn in ("0306406153", "9780451524934", "1234567890", "abcd", "١٢٣٤٥٦٧٨٩٠", "030640615X"):
        debe_fallar(lambda v=isbn: biblioteca._isbn(v), f"ISBN incorrecto rechazado: {isbn}")
    debe_fallar(lambda: biblioteca.crear_libro(formulario_libro(titulo="   ")), "Rechaza título vacío")
    debe_fallar(lambda: biblioteca.crear_libro(formulario_libro(autor="  ")), "Rechaza autor vacío")
    debe_fallar(lambda: biblioteca.crear_libro(formulario_libro(categoria=" ")), "Rechaza categoría vacía")
    debe_fallar(lambda: biblioteca.crear_libro(formulario_libro(anio="1800.5")), "Rechaza año decimal")
    debe_fallar(lambda: biblioteca.crear_libro(formulario_libro(anio="abc")), "Rechaza año sin números")
    debe_fallar(lambda: biblioteca.crear_libro(formulario_libro(anio="9999")), "Rechaza publicación imposible")
    debe_fallar(lambda: biblioteca.crear_libro(formulario_libro(ejemplares="-1")), "Rechaza ejemplares negativos")
    debe_fallar(lambda: biblioteca.crear_libro(formulario_libro(ejemplares="1.5")), "Rechaza ejemplares decimales")
    debe_fallar(lambda: biblioteca.crear_libro(formulario_libro(descripcion="x" * 801)), "Rechaza descripción excesiva")
    debe_fallar(lambda: biblioteca.crear_libro(formulario_libro(titulo="x" * 121)), "Rechaza título excesivo")
    debe_fallar(lambda: biblioteca.crear_usuario({"nombre": "", "correo": "a@b.com"}), "Rechaza lector sin nombre")
    for correo in ("incorrecto", "a@b", "a @b.com", "a@@b.com", "a@b..com", "x@.com"):
        debe_fallar(lambda c=correo: biblioteca.crear_usuario({"nombre": "X", "correo": c}), f"Rechaza correo {correo}")
    comprobar(len(datos.leer()["libros"]) == 10, "Entradas inválidas no agregan libros")
    comprobar(len(datos.leer()["usuarios"]) == 3, "Entradas inválidas no agregan usuarios")


def probar_usuarios():
    nuevo = biblioteca.crear_usuario({"nombre": "  Juan    Pérez  ", "correo": "  JUAN@EJEMPLO.COM  "})
    comprobar(biblioteca.obtener_usuario(nuevo)["nombre"] == "Juan Pérez", "Normaliza espacios del nombre")
    comprobar(biblioteca.obtener_usuario(nuevo)["correo"] == "juan@ejemplo.com", "Normaliza correo")
    debe_fallar(lambda: biblioteca.crear_usuario({"nombre": "Duplicado", "correo": "JUAN@EJEMPLO.COM"}), "No duplica correos")
    biblioteca.editar_usuario(nuevo, {"nombre": "Juan Editado", "correo": "juan2@ejemplo.com"})
    comprobar(biblioteca.obtener_usuario(nuevo)["nombre"] == "Juan Editado", "Edita usuario correctamente")
    debe_fallar(lambda: biblioteca.editar_usuario(nuevo, {"nombre": "Juan", "correo": "ana@ejemplo.com"}), "Edición bloquea correo ocupado")
    comprobar(biblioteca.obtener_usuario(nuevo)["correo"] == "juan2@ejemplo.com", "Edición errónea conserva datos anteriores")
    biblioteca.eliminar_usuario(nuevo)
    debe_fallar(lambda: biblioteca.obtener_usuario(nuevo), "Elimina usuarios sin historial")
    debe_fallar(lambda: biblioteca.eliminar_usuario("USU001"), "Protege usuario con historial de préstamos")
    debe_fallar(lambda: biblioteca.eliminar_usuario("USU002"), "Protege usuario con historial de reservas")


def probar_existencias_y_reservas():
    libro = biblioteca.obtener_libro("LIB004")
    debe_fallar(lambda: biblioteca.editar_libro("LIB004", {
        "isbn": libro["isbn"], "titulo": libro["titulo"], "autor": libro["autor"],
        "categoria": libro["categoria"], "anio": str(libro["anio"]),
        "ejemplares": "0", "descripcion": libro["descripcion"],
    }), "No reduce ejemplares por debajo de préstamo activo")
    comprobar(biblioteca.obtener_libro("LIB004")["ejemplares"] == 1, "Cambio de existencias fallido no se guarda")
    reserva_nueva = biblioteca.crear_reserva("USU003", "LIB004")
    comprobar(any(r["id"] == reserva_nueva and r["estado"] == "pendiente" for r in biblioteca.listar_reservas()), "Registra segunda reserva en cola")
    biblioteca.editar_libro("LIB004", {
        "isbn": libro["isbn"], "titulo": libro["titulo"], "autor": libro["autor"],
        "categoria": libro["categoria"], "anio": str(libro["anio"]),
        "ejemplares": "3", "descripcion": libro["descripcion"],
    })
    estados = {r["id"]: r["estado"] for r in biblioteca.listar_reservas()}
    comprobar(estados["RES001"] == "lista" and estados[reserva_nueva] == "lista", "Aumentar copias reparte a reservas por antigüedad")
    comprobar(biblioteca.obtener_libro("LIB004")["disponibles"] == 0, "No ofrece copias apartadas")
    debe_fallar(lambda: biblioteca.crear_prestamo("USU001", "LIB004"), "No permite duplicar préstamo existente")
    biblioteca.cancelar_reserva("RES001")
    comprobar(biblioteca.obtener_libro("LIB004")["disponibles"] == 1, "Cancelar una reserva lista libera un ejemplar")
    prestamo = biblioteca.crear_prestamo("USU002", "LIB004")
    comprobar(biblioteca.obtener_libro("LIB004")["disponibles"] == 0, "Prestar copia liberada descuenta existencias")
    biblioteca.devolver_prestamo(prestamo)
    debe_fallar(lambda: biblioteca.devolver_prestamo(prestamo), "No permite devolver dos veces")
    comprobar(biblioteca.obtener_libro("LIB004")["disponibles"] == 1, "Devolución restaura existencias")
    comprobar(biblioteca.tablero()["disponibles"] == sum(l["disponibles"] for l in biblioteca.listar_libros()[0]), "Total del panel coincide con catálogo")


def probar_limite_de_prestamos():
    ids = [biblioteca.crear_prestamo("USU003", codigo) for codigo in ("LIB001", "LIB002", "LIB003")]
    comprobar(len(ids) == 3, "Permite tres préstamos activos al mismo lector")
    debe_fallar(lambda: biblioteca.crear_prestamo("USU003", "LIB005"), "Bloquea cuarto préstamo activo")
    comprobar(len([p for p in biblioteca.listar_prestamos() if p["usuario_id"] == "USU003"]) == 3,
             "Cuarto préstamo rechazado no aparece en el historial")
    biblioteca.devolver_prestamo(ids[0])
    comprobar(bool(biblioteca.crear_prestamo("USU003", "LIB005")), "Permite nuevo préstamo tras liberar cupo")
    debe_fallar(lambda: biblioteca.crear_reserva("USU003", "LIB005"), "No permite reservar un libro que ya se tiene prestado")
    comprobar(datos.validar_datos(datos.leer()), "Ciclo del límite de préstamos conserva integridad")


def probar_integridad_json():
    base = datos.leer()
    comprobar(datos.validar_datos(base) is True, "JSON de ejemplo íntegro")
    alteraciones = []
    alteraciones.append(("raíz no es objeto", []))
    alteraciones.append(("lista de usuarios ausente", {k: v for k, v in base.items() if k != "usuarios"}))
    mod = deepcopy(base); mod["libros"].append(deepcopy(mod["libros"][0])); alteraciones.append(("IDs duplicados", mod))
    mod = deepcopy(base); mod["libros"][1]["isbn"] = mod["libros"][0]["isbn"]; alteraciones.append(("ISBN duplicados", mod))
    mod = deepcopy(base); mod["usuarios"][1]["correo"] = mod["usuarios"][0]["correo"]; alteraciones.append(("Correos duplicados", mod))
    mod = deepcopy(base); mod["prestamos"][0]["usuario_id"] = "NOEXISTE"; alteraciones.append(("Préstamo huérfano", mod))
    mod = deepcopy(base); mod["reservas"][0]["libro_id"] = "NOEXISTE"; alteraciones.append(("Reserva huérfana", mod))
    mod = deepcopy(base); mod["reservas"][0]["estado"] = "imposible"; alteraciones.append(("Estado de reserva desconocido", mod))
    mod = deepcopy(base); mod["reservas"][0]["estado"] = []; alteraciones.append(("Estado reserva no textual", mod))
    mod = deepcopy(base); mod["prestamos"][0]["vence_en"] = "fecha"; alteraciones.append(("Fecha inválida", mod))
    mod = deepcopy(base); mod["libros"][3]["ejemplares"] = 0; alteraciones.append(("Más préstamos que ejemplares", mod))
    mod = deepcopy(base); mod["prestamos"].append(deepcopy(mod["prestamos"][0])); mod["prestamos"][1]["id"] = "OTRO"; alteraciones.append(("Dos préstamos activos iguales", mod))
    mod = deepcopy(base); mod["reservas"].append(deepcopy(mod["reservas"][0])); mod["reservas"][1]["id"] = "OTRA"; alteraciones.append(("Reservas duplicadas", mod))
    mod = deepcopy(base); mod["prestamos"][0]["prestado_en"] = "2099-01-01"; alteraciones.append(("Fecha de préstamo posterior a vencimiento", mod))
    for nombre, corrupto in alteraciones:
        debe_fallar(lambda v=corrupto: datos.validar_datos(v), f"Detecta: {nombre}")
    contenido_original = datos.RUTA_DATOS.read_bytes()
    debe_fallar(lambda: datos.cambiar(lambda b: b["libros"].clear()), "Transacción inconsistente se bloquea")
    comprobar(datos.RUTA_DATOS.read_bytes() == contenido_original, "Transacción fallida no modifica JSON")
    datos.RUTA_DATOS.write_text("{NO ES JSON", encoding="utf-8")
    debe_fallar(datos.leer, "Detecta archivo JSON malformado")
    comprobar(datos.RUTA_DATOS.read_text(encoding="utf-8") == "{NO ES JSON", "No sobreescribe archivos corruptos")


def probar_concurrencia():
    def agregar(i):
        return biblioteca.crear_usuario({"nombre": f"Lector {i}", "correo": f"lector{i}@ejemplo.org"})
    with ThreadPoolExecutor(max_workers=8) as pool:
        ids = list(pool.map(agregar, range(24)))
    comprobar(len(set(ids)) == 24, "24 operaciones concurrentes generan IDs únicos")
    comprobar(len(datos.leer()["usuarios"]) == 27, "No se pierden altas concurrentes dentro del proceso")
    comprobar(datos.validar_datos(datos.leer()), "JSON concurrente mantiene integridad")
    comprobar(not list(datos.RUTA_DATOS.parent.glob("biblioteca_*.tmp")), "No quedan archivos temporales")


def ejecutar_pruebas():
    datos_aislados(probar_validaciones_formulario)
    datos_aislados(probar_usuarios)
    datos_aislados(probar_existencias_y_reservas)
    datos_aislados(probar_limite_de_prestamos)
    datos_aislados(probar_integridad_json)
    datos_aislados(probar_concurrencia)
    print(f"\nRESULTADO: {VERIFICACIONES} verificaciones ampliadas correctas.")


if __name__ == "__main__":
    ejecutar_pruebas()
