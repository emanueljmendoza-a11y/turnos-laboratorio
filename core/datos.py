"""Persistencia JSON local, transacciones atómicas y validación de integridad.

Se utiliza únicamente la biblioteca estándar. La validación se ejecuta al leer
los datos y justo antes de escribirlos, para evitar guardar estados incoherentes.
"""

from core import calendario
from core.estructuras import a_minusculas
from pathlib import Path
import json
import os
import tempfile
import threading

RUTA_DATOS = Path(__file__).resolve().parent.parent / "data" / "biblioteca.json"
BLOQUEO = threading.RLock()
COLECCIONES = ("libros", "usuarios", "prestamos", "reservas")
ESTADOS_RESERVA = {"pendiente", "lista", "cumplida", "cancelada"}


def ejemplo_inicial():
    """Registros de demostración creados únicamente en el primer inicio."""
    hoy = calendario.fecha_hoy()
    libros_base = [
        ("LIB001", "9788420412146", "Don Quijote de la Mancha", "Miguel de Cervantes", "Clásicos", 1605, 3),
        ("LIB002", "9780307474728", "Cien años de soledad", "Gabriel García Márquez", "Novela", 1967, 2),
        ("LIB003", "9780307389732", "El amor en los tiempos del cólera", "Gabriel García Márquez", "Novela", 1985, 2),
        ("LIB004", "9780451524935", "1984", "George Orwell", "Ciencia ficción", 1949, 1),
        ("LIB005", "9780451526342", "Rebelión en la granja", "George Orwell", "Clásicos", 1945, 2),
        ("LIB006", "9780156012195", "El principito", "Antoine de Saint-Exupéry", "Infantil", 1943, 4),
        ("LIB007", "9781400034710", "Crónica de una muerte anunciada", "Gabriel García Márquez", "Novela", 1981, 2),
        ("LIB008", "9781451673319", "Fahrenheit 451", "Ray Bradbury", "Ciencia ficción", 1953, 2),
        ("LIB009", "9780553213102", "Orgullo y prejuicio", "Jane Austen", "Clásicos", 1813, 2),
        ("LIB010", "9780553213690", "La metamorfosis", "Franz Kafka", "Clásicos", 1915, 1),
    ]
    libros = [{
        "id": id_, "isbn": isbn, "titulo": titulo, "autor": autor,
        "categoria": categoria, "anio": anio, "ejemplares": ejemplares,
        "descripcion": "Ejemplar de demostración para el sistema académico de biblioteca.",
    } for id_, isbn, titulo, autor, categoria, anio, ejemplares in libros_base]

    return {
        "libros": libros,
        "usuarios": [
            {"id": "USU001", "nombre": "Ana López", "correo": "ana@ejemplo.com"},
            {"id": "USU002", "nombre": "Carlos Pérez", "correo": "carlos@ejemplo.com"},
            {"id": "USU003", "nombre": "Lucía Martínez", "correo": "lucia@ejemplo.com"},
        ],
        "prestamos": [{
            "id": "PRE001", "libro_id": "LIB004", "usuario_id": "USU001",
            "prestado_en": calendario.sumar_dias(hoy, -20),
            "vence_en": calendario.sumar_dias(hoy, -6), "devuelto_en": None,
        }],
        "reservas": [{
            "id": "RES001", "libro_id": "LIB004", "usuario_id": "USU002",
            "creada_en": calendario.sumar_dias(hoy, -2) + calendario.fecha_hora_actual()[10:19],
            "estado": "pendiente",
        }],
    }


def _texto(registro, clave, contexto, puede_ser_vacio=False):
    valor = registro.get(clave)
    if not isinstance(valor, str) or (not valor.strip() and not puede_ser_vacio):
        raise ValueError(f"JSON inválido: {contexto}, campo «{clave}» incorrecto.")
    return valor


def _fecha(valor, contexto, permitir_nulo=False, con_hora=False):
    if permitir_nulo and valor is None:
        return None
    if not isinstance(valor, str):
        raise ValueError(f"JSON inválido: fecha de {contexto} incorrecta.")
    try:
        if con_hora:
            return calendario.validar_fecha_hora(valor)
        calendario.fecha_a_dias(valor)
        return valor
    except ValueError:
        raise ValueError(f"JSON inválido: fecha de {contexto} incorrecta.") from None



def validar_datos(base):
    """Comprueba tipos, unicidad, claves foráneas y ejemplares disponibles.

    O(L + U + P + R) promedio, mediante conjuntos y diccionarios auxiliares.
    No modifica el contenido recibido. Acepta ISBN antiguos por compatibilidad;
    los ISBN nuevos se comprueban con su dígito de control en biblioteca.py.
    """
    if not isinstance(base, dict):
        raise ValueError("JSON inválido: se requieren las listas libros, usuarios, préstamos y reservas.")
    for clave in COLECCIONES:
        if not isinstance(base.get(clave), list):
            raise ValueError("JSON inválido: se requieren las listas libros, usuarios, préstamos y reservas.")

    por_id = {}
    for coleccion in COLECCIONES:
        vistos = set()
        por_id[coleccion] = {}
        for registro in base[coleccion]:
            if not isinstance(registro, dict):
                raise ValueError(f"JSON inválido: registro de {coleccion} no es un objeto.")
            id_ = _texto(registro, "id", coleccion)
            if len(id_) > 80 or id_ in vistos:
                raise ValueError(f"JSON inválido: identificador duplicado o excesivo en {coleccion}.")
            vistos.add(id_)
            por_id[coleccion][id_] = registro

    isbn_vistos = set()
    for libro in base["libros"]:
        contexto = f"libro {libro['id']}"
        isbn = _texto(libro, "isbn", contexto)
        if isbn in isbn_vistos:
            raise ValueError("JSON inválido: existen ISBN duplicados.")
        isbn_vistos.add(isbn)
        for clave in ("titulo", "autor", "categoria"):
            _texto(libro, clave, contexto)
        _texto(libro, "descripcion", contexto, puede_ser_vacio=True)
        if (type(libro.get("anio")) is not int or not 1 <= libro["anio"] <= 2100
                or type(libro.get("ejemplares")) is not int or not 0 <= libro["ejemplares"] <= 10000):
            raise ValueError(f"JSON inválido: año o ejemplares incorrectos en {contexto}.")

    correos = set()
    for usuario in base["usuarios"]:
        contexto = f"usuario {usuario['id']}"
        _texto(usuario, "nombre", contexto)
        correo = a_minusculas(_texto(usuario, "correo", contexto))
        if correo in correos:
            raise ValueError("JSON inválido: hay correos repetidos.")
        correos.add(correo)

    ocupados = {id_: 0 for id_ in por_id["libros"]}
    activos_usuario_libro = set()
    for prestamo in base["prestamos"]:
        contexto = f"préstamo {prestamo['id']}"
        libro_id = _texto(prestamo, "libro_id", contexto)
        usuario_id = _texto(prestamo, "usuario_id", contexto)
        if libro_id not in ocupados or usuario_id not in por_id["usuarios"]:
            raise ValueError(f"JSON inválido: {contexto} referencia un libro o usuario inexistente.")
        inicio = _fecha(prestamo.get("prestado_en"), f"{contexto} (préstamo)")
        vencimiento = _fecha(prestamo.get("vence_en"), f"{contexto} (vencimiento)")
        devolucion = _fecha(prestamo.get("devuelto_en"), f"{contexto} (devolución)", permitir_nulo=True)
        if vencimiento < inicio or (devolucion is not None and devolucion < inicio):
            raise ValueError(f"JSON inválido: fechas incoherentes en {contexto}.")
        if devolucion is None:
            clave = (usuario_id, libro_id)
            if clave in activos_usuario_libro:
                raise ValueError("JSON inválido: un usuario tiene dos préstamos activos del mismo libro.")
            activos_usuario_libro.add(clave)
            ocupados[libro_id] += 1

    reservas_activas = set()
    for reserva in base["reservas"]:
        contexto = f"reserva {reserva['id']}"
        libro_id = _texto(reserva, "libro_id", contexto)
        usuario_id = _texto(reserva, "usuario_id", contexto)
        if libro_id not in ocupados or usuario_id not in por_id["usuarios"]:
            raise ValueError(f"JSON inválido: {contexto} referencia un libro o usuario inexistente.")
        _fecha(reserva.get("creada_en"), f"{contexto} (creación)", con_hora=True)
        estado = reserva.get("estado")
        if not isinstance(estado, str) or estado not in ESTADOS_RESERVA:
            raise ValueError(f"JSON inválido: estado incorrecto en {contexto}.")
        if estado in ("pendiente", "lista"):
            clave = (usuario_id, libro_id)
            if clave in reservas_activas or clave in activos_usuario_libro:
                raise ValueError("JSON inválido: reservas activas duplicadas o con préstamo simultáneo.")
            reservas_activas.add(clave)
        if estado == "lista":
            ocupados[libro_id] += 1

    for libro_id, cantidad in ocupados.items():
        if cantidad > por_id["libros"][libro_id]["ejemplares"]:
            raise ValueError(f"JSON inválido: hay más préstamos y reservas listas que ejemplares ({libro_id}).")
    return True


def guardar_sin_bloqueo(base):
    validar_datos(base)
    RUTA_DATOS.parent.mkdir(parents=True, exist_ok=True)
    temporal = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=RUTA_DATOS.parent,
            prefix="biblioteca_", suffix=".tmp", delete=False
        ) as archivo:
            temporal = archivo.name
            json.dump(base, archivo, ensure_ascii=False, indent=2, allow_nan=False)
            archivo.write("\n")
            archivo.flush()
            os.fsync(archivo.fileno())
        os.replace(temporal, RUTA_DATOS)
    finally:
        if temporal and os.path.exists(temporal):
            os.remove(temporal)


def inicializar():
    with BLOQUEO:
        if not RUTA_DATOS.exists():
            guardar_sin_bloqueo(ejemplo_inicial())


def cargar_sin_bloqueo():
    try:
        with RUTA_DATOS.open("r", encoding="utf-8") as archivo:
            base = json.load(archivo)
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ValueError("No se puede leer el JSON: formato o codificación incorrectos. No se modificó el archivo.") from error
    validar_datos(base)
    return base


def leer():
    with BLOQUEO:
        inicializar()
        return cargar_sin_bloqueo()


def cambiar(operacion):
    """Carga, aplica, valida y guarda una transacción bajo un mismo bloqueo."""
    with BLOQUEO:
        inicializar()
        base = cargar_sin_bloqueo()
        resultado = operacion(base)
        guardar_sin_bloqueo(base)
        return resultado
