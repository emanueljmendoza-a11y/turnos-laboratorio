"""Pruebas HTTP reales con Flask test_client (requieren instalar Flask).

Desde la raíz: python tests/test_flask.py
Sin clases propias; usa un archivo JSON temporal y un navegador de pruebas.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from app import app
except ModuleNotFoundError as error:
    if error.name == "flask" or error.name == "werkzeug":
        print("NO EJECUTADO: falta Flask. Instala primero: python -m pip install -r requirements.txt")
        sys.exit(2)
    raise
from core import biblioteca, datos

COMPROBACIONES = 0


def comprobar(condicion, mensaje):
    global COMPROBACIONES
    if not condicion:
        raise AssertionError(mensaje)
    COMPROBACIONES += 1
    print(f"[OK {COMPROBACIONES:02d}] {mensaje}")


def csrf(cliente, url="/usuarios/nuevo"):
    respuesta = cliente.get(url)
    comprobar(respuesta.status_code == 200, f"Formulario {url} funciona")
    encontrado = re.search(rb'name="_csrf" value="([0-9a-f]{64})"', respuesta.data)
    assert encontrado is not None, f"Falta token CSRF en {url}"
    return encontrado.group(1).decode()


def ejecutar_pruebas():
    anterior = datos.RUTA_DATOS
    with TemporaryDirectory() as carpeta:
        datos.RUTA_DATOS = Path(carpeta) / "web.json"
        app.config.update(TESTING=True)
        try:
            cliente = app.test_client()
            for url in ("/", "/libros", "/libros/LIB004", "/usuarios", "/prestamos",
                        "/reservas", "/algoritmos", "/libros/nuevo", "/prestamos/nuevo",
                        "/reservas/nueva", "/usuarios/nuevo", "/usuarios/USU001/editar"):
                respuesta = cliente.get(url)
                comprobar(respuesta.status_code == 200, f"GET {url} → 200")
                comprobar(b"BiblioEstructuras" in respuesta.data, f"GET {url} renderiza plantilla")
            respuesta = cliente.get("/no-existe")
            comprobar(respuesta.status_code == 404, "Ruta inexistente → 404")
            respuesta = cliente.get("/libros/NOEXISTE")
            comprobar(respuesta.status_code == 404, "Libro inexistente → 404")
            respuesta = cliente.get("/usuarios/NOEXISTE/editar")
            comprobar(respuesta.status_code == 404, "Usuario inexistente → 404")
            respuesta = cliente.post("/usuarios/nuevo", data={"nombre": "Intruso", "correo": "a@b.com"})
            comprobar(respuesta.status_code == 400, "Sin CSRF → 400")
            comprobar(len(datos.leer()["usuarios"]) == 3, "CSRF impide cambios de datos")
            token = csrf(cliente)
            respuesta = cliente.post("/usuarios/nuevo", data={"_csrf": token, "nombre": "Josefa López", "correo": "josefa@ejemplo.com"})
            comprobar(respuesta.status_code == 302, "Alta de usuario redirige tras guardar")
            usuario = next(u for u in datos.leer()["usuarios"] if u["correo"] == "josefa@ejemplo.com")
            comprobar(usuario["nombre"] == "Josefa López", "Alta HTTP persiste usuario")
            respuesta = cliente.post(f"/usuarios/{usuario['id']}/editar", data={"_csrf": token, "nombre": "Josefa Editada", "correo": "josefa@ejemplo.com"})
            comprobar(respuesta.status_code == 302, "Edición HTTP de usuario")
            comprobar(biblioteca.obtener_usuario(usuario["id"])["nombre"] == "Josefa Editada", "Edición HTTP persiste cambios")
            respuesta = cliente.post(f"/usuarios/{usuario['id']}/eliminar", data={"_csrf": token})
            comprobar(respuesta.status_code == 302, "Eliminación HTTP redirige")
            comprobar(len(datos.leer()["usuarios"]) == 3, "Eliminación HTTP persiste")
            respuesta = cliente.post("/libros/nuevo", data={
                "_csrf": token, "isbn": "1234567890", "titulo": "ISBN inválido", "autor": "Test",
                "categoria": "Test", "anio": "2020", "ejemplares": "1", "descripcion": "",
            })
            comprobar(respuesta.status_code == 302, "Formulario incorrecto redirige con error")
            comprobar(len(datos.leer()["libros"]) == 10, "Libro con ISBN incorrecto no se guarda")
            respuesta = cliente.post("/prestamos/PRE001/devolver", data={"_csrf": token})
            comprobar(respuesta.status_code == 302, "Devolución HTTP procesada")
            reserva = next(r for r in datos.leer()["reservas"] if r["id"] == "RES001")
            comprobar(reserva["estado"] == "lista", "Devolución HTTP activa próxima reserva")
            respuesta = cliente.post("/prestamos/nuevo", data={"_csrf": token, "usuario_id": "USU002", "libro_id": "LIB004"})
            comprobar(respuesta.status_code == 302, "Recogida HTTP procesada")
            reserva = next(r for r in datos.leer()["reservas"] if r["id"] == "RES001")
            comprobar(reserva["estado"] == "cumplida", "Recogida HTTP completa reserva")
            respuesta = cliente.get("/datos/exportar")
            comprobar(respuesta.status_code == 200, "Exportación JSON disponible")
            comprobar("attachment" in respuesta.headers.get("Content-Disposition", ""), "Descarga marcada como archivo")
            comprobar(json.loads(respuesta.data)["libros"][0]["id"] == "LIB001", "Respaldo JSON íntegro")
            comprobar(respuesta.headers["X-Content-Type-Options"] == "nosniff", "Cabecera de seguridad nosniff")
            comprobar("script-src 'none'" in respuesta.headers["Content-Security-Policy"], "CSP bloquea scripts")
            respuesta = cliente.post("/usuarios/nuevo", data={"_csrf": token, "nombre": "x" * (70 * 1024)})
            comprobar(respuesta.status_code == 413, "Formularios enormes rechazados")
        finally:
            datos.RUTA_DATOS = anterior
    print(f"\nRESULTADO: {COMPROBACIONES} pruebas HTTP reales satisfactorias.")


if __name__ == "__main__":
    ejecutar_pruebas()
