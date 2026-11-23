"""Renderiza todas las plantillas con Jinja2, sin necesitar Flask ni servidor.

Jinja2 es una dependencia transitiva de Flask. Las rutas HTTP se prueban
independientemente en tests/test_flask.py cuando Flask esté instalado.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import biblioteca, datos
try:
    from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
except ImportError:
    print("Jinja2 no instalado. Instala requirements.txt antes de esta prueba.")
    sys.exit(2)

RAIZ = Path(__file__).resolve().parent.parent


def ejecutar_pruebas():
    anterior = datos.RUTA_DATOS
    with TemporaryDirectory() as carpeta:
        datos.RUTA_DATOS = Path(carpeta) / "biblioteca.json"
        try:
            listado, categorias = biblioteca.listar_libros()
            usuario = biblioteca.obtener_usuario("USU001")
            env = Environment(
                loader=FileSystemLoader(RAIZ / "templates"),
                autoescape=select_autoescape(["html"]), undefined=StrictUndefined,
            )
            env.globals.update({
                "url_for": lambda endpoint, **params: "/" + endpoint,
                "token_csrf": lambda: "token-prueba",
                "get_flashed_messages": lambda with_categories: [],
                "request": SimpleNamespace(endpoint="inicio"),
            })
            contextos = {
                "base.html": {"titulo": "Base"},
                "inicio.html": {"titulo": "Inicio", "tablero": biblioteca.tablero()},
                "libros.html": {"titulo": "Libros", "libros": listado, "categorias": categorias,
                                "consulta": "", "categoria": ""},
                "libro_detalle.html": {"titulo": "1984", "libro": biblioteca.obtener_libro("LIB004")},
                "libro_form.html": {"titulo": "Nuevo libro", "libro": None, "max_anio": time.localtime().tm_year + 1},
                "usuarios.html": {"titulo": "Usuarios", "usuarios": biblioteca.listar_usuarios()},
                "usuario_form.html": {"titulo": "Nuevo usuario", "usuario": None},
                "prestamos.html": {"titulo": "Préstamos", "prestamos": biblioteca.listar_prestamos(), "estado": "activos"},
                "prestamo_form.html": {"titulo": "Prestar", "libros": listado, "usuarios": biblioteca.listar_usuarios(),
                                       "seleccionado": "LIB004", "seleccionado_usuario": "USU002"},
                "reservas.html": {"titulo": "Reservas", "reservas": biblioteca.listar_reservas(), "estado": "todas"},
                "reserva_form.html": {"titulo": "Reservar", "libros": listado, "usuarios": biblioteca.listar_usuarios(),
                                      "seleccionado": "LIB004"},
                "algoritmos.html": {"titulo": "Algoritmos", "datos": biblioteca.analisis_estructuras()},
                "error.html": {"titulo": "Error", "mensaje": "Página no encontrada."},
            }
            contador = 0
            for nombre, contexto in contextos.items():
                salida = env.get_template(nombre).render(**contexto)
                assert "<!DOCTYPE html>" in salida, nombre
                assert "BiblioEstructuras" in salida, nombre
                if '<form method="post"' in salida or 'method="post"' in salida:
                    assert 'name="_csrf" value="token-prueba"' in salida, nombre
                contador += 1
                print(f"[OK] {nombre}: compilada, renderizada y con contexto completo")
            for nombre, contexto in (
                ("libro_form.html", {"titulo": "Editar", "libro": biblioteca.obtener_libro("LIB004"),
                                      "max_anio": time.localtime().tm_year + 1}),
                ("usuario_form.html", {"titulo": "Editar", "usuario": usuario}),
                ("reservas.html", {"titulo": "Reservas", "reservas": [
                    {**r, "estado": "lista"} for r in biblioteca.listar_reservas()
                ], "estado": "lista"}),
            ):
                salida = env.get_template(nombre).render(**contexto)
                assert "<!DOCTYPE html>" in salida, nombre
                contador += 1
                print(f"[OK] {nombre}: modo alternativo válido")
            print(f"\nRESULTADO: {contador} renderizados correctos.")
        finally:
            datos.RUTA_DATOS = anterior


if __name__ == "__main__":
    ejecutar_pruebas()
