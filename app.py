"""Interfaz web Flask: todas las operaciones y reglas se ejecutan en Python.

Ejecutar: python app.py | Abrir: http://127.0.0.1:5000
"""

import hmac
import json
import os
import secrets

from flask import (
    Flask, Response, abort, flash, redirect, render_template,
    request, session, url_for,
)
from core import biblioteca, datos, calendario

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024


def token_csrf():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(32)
    return session["_csrf"]


@app.after_request
def cabeceras_seguridad(respuesta):
    """La aplicación solo está destinada a la red local de desarrollo."""
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["X-Frame-Options"] = "DENY"
    respuesta.headers["Referrer-Policy"] = "no-referrer"
    respuesta.headers["Cache-Control"] = "no-store"
    respuesta.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'none'; style-src 'self'; "
        "img-src 'self' data:; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
    )
    return respuesta


@app.context_processor
def utilidades_plantilla():
    return {"token_csrf": token_csrf}


@app.before_request
def proteger_formularios():
    if request.method == "POST":
        recibido = request.form.get("_csrf", "")
        guardado = session.get("_csrf", "")
        if not recibido or not guardado or not hmac.compare_digest(recibido, guardado):
            abort(400, description="Formulario caducado o inválido. Recarga la página.")


def intentar(operacion, destino_exito, destino_error, mensaje):
    """Centraliza respuestas de formularios sin programar clases."""
    try:
        resultado = operacion()
        flash(mensaje, "ok")
        return redirect(destino_exito(resultado) if callable(destino_exito) else destino_exito)
    except ValueError as error:
        flash(str(error), "error")
        return redirect(destino_error)


@app.get("/")
def inicio():
    return render_template("inicio.html", tablero=biblioteca.tablero(), titulo="Panel general")


@app.get("/libros")
def libros():
    consulta = request.args.get("q", "").strip()[:150]
    categoria = request.args.get("categoria", "").strip()[:120]
    listado, categorias = biblioteca.listar_libros(consulta, categoria)
    return render_template(
        "libros.html", titulo="Catálogo de libros", libros=listado,
        categorias=categorias, consulta=consulta, categoria=categoria,
    )


@app.get("/libros/<libro_id>")
def libro_detalle(libro_id):
    try:
        libro = biblioteca.obtener_libro(libro_id)
    except ValueError:
        abort(404)
    return render_template("libro_detalle.html", titulo=libro["titulo"], libro=libro)


@app.route("/libros/nuevo", methods=["GET", "POST"])
def libro_nuevo():
    if request.method == "POST":
        return intentar(
            lambda: biblioteca.crear_libro(request.form),
            lambda libro_id: url_for("libro_detalle", libro_id=libro_id),
            url_for("libro_nuevo"), "Libro añadido al catálogo.",
        )
    return render_template("libro_form.html", titulo="Nuevo libro", libro=None, max_anio=calendario.anio_actual() + 1)


@app.route("/libros/<libro_id>/editar", methods=["GET", "POST"])
def libro_editar(libro_id):
    try:
        libro = biblioteca.obtener_libro(libro_id)
    except ValueError:
        abort(404)
    if request.method == "POST":
        return intentar(
            lambda: biblioteca.editar_libro(libro_id, request.form),
            url_for("libro_detalle", libro_id=libro_id),
            url_for("libro_editar", libro_id=libro_id), "Libro actualizado.",
        )
    return render_template("libro_form.html", titulo="Editar libro", libro=libro, max_anio=calendario.anio_actual() + 1)


@app.post("/libros/<libro_id>/eliminar")
def libro_eliminar(libro_id):
    return intentar(
        lambda: biblioteca.eliminar_libro(libro_id),
        url_for("libros"), url_for("libro_detalle", libro_id=libro_id),
        "Libro eliminado.",
    )


@app.get("/usuarios")
def usuarios():
    return render_template("usuarios.html", titulo="Usuarios", usuarios=biblioteca.listar_usuarios())


@app.route("/usuarios/nuevo", methods=["GET", "POST"])
def usuario_nuevo():
    if request.method == "POST":
        return intentar(
            lambda: biblioteca.crear_usuario(request.form),
            url_for("usuarios"), url_for("usuario_nuevo"),
            "Usuario registrado correctamente.",
        )
    return render_template("usuario_form.html", titulo="Registrar usuario", usuario=None)


@app.route("/usuarios/<usuario_id>/editar", methods=["GET", "POST"])
def usuario_editar(usuario_id):
    try:
        usuario = biblioteca.obtener_usuario(usuario_id)
    except ValueError:
        abort(404)
    if request.method == "POST":
        return intentar(
            lambda: biblioteca.editar_usuario(usuario_id, request.form),
            url_for("usuarios"), url_for("usuario_editar", usuario_id=usuario_id),
            "Usuario actualizado.",
        )
    return render_template("usuario_form.html", titulo="Editar usuario", usuario=usuario)


@app.post("/usuarios/<usuario_id>/eliminar")
def usuario_eliminar(usuario_id):
    return intentar(
        lambda: biblioteca.eliminar_usuario(usuario_id),
        url_for("usuarios"), url_for("usuario_editar", usuario_id=usuario_id),
        "Usuario eliminado.",
    )


@app.get("/datos/exportar")
def exportar_datos():
    """Descarga una copia JSON para respaldo manual, sin cambiar el original."""
    contenido = json.dumps(datos.leer(), ensure_ascii=False, indent=2) + "\n"
    return Response(
        contenido,
        content_type="application/json; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="biblioteca_respaldo.json"'},
    )


@app.get("/prestamos")
def prestamos():
    estado = request.args.get("estado", "activos")
    if estado not in ("activos", "devueltos", "todos"):
        estado = "activos"
    return render_template(
        "prestamos.html", titulo="Préstamos", prestamos=biblioteca.listar_prestamos(estado), estado=estado,
    )


@app.route("/prestamos/nuevo", methods=["GET", "POST"])
def prestamo_nuevo():
    if request.method == "POST":
        return intentar(
            lambda: biblioteca.crear_prestamo(
                request.form.get("usuario_id", ""), request.form.get("libro_id", "")
            ),
            url_for("prestamos"), url_for("prestamo_nuevo", libro_id=request.form.get("libro_id", "")),
            "Préstamo registrado; vence en 14 días.",
        )
    libros_lista, _ = biblioteca.listar_libros()
    return render_template(
        "prestamo_form.html", titulo="Nuevo préstamo",
        libros=libros_lista, usuarios=biblioteca.listar_usuarios(),
        seleccionado=request.args.get("libro_id", ""),
        seleccionado_usuario=request.args.get("usuario_id", ""),
    )


@app.post("/prestamos/<prestamo_id>/devolver")
def prestamo_devolver(prestamo_id):
    return intentar(
        lambda: biblioteca.devolver_prestamo(prestamo_id),
        url_for("prestamos"), url_for("prestamos"),
        "Devolución registrada. Las reservas pendientes se actualizaron.",
    )


@app.get("/reservas")
def reservas():
    estado = request.args.get("estado", "todas")
    if estado not in ("todas", "pendiente", "lista", "cumplida", "cancelada"):
        estado = "todas"
    return render_template(
        "reservas.html", titulo="Reservas", reservas=biblioteca.listar_reservas(estado), estado=estado,
    )


@app.route("/reservas/nueva", methods=["GET", "POST"])
def reserva_nueva():
    if request.method == "POST":
        return intentar(
            lambda: biblioteca.crear_reserva(
                request.form.get("usuario_id", ""), request.form.get("libro_id", "")
            ),
            url_for("reservas"), url_for("reserva_nueva", libro_id=request.form.get("libro_id", "")),
            "Reserva creada y añadida a la cola de prioridad.",
        )
    libros_lista, _ = biblioteca.listar_libros()
    return render_template(
        "reserva_form.html", titulo="Nueva reserva",
        libros=libros_lista, usuarios=biblioteca.listar_usuarios(),
        seleccionado=request.args.get("libro_id", ""),
    )


@app.post("/reservas/<reserva_id>/cancelar")
def reserva_cancelar(reserva_id):
    return intentar(
        lambda: biblioteca.cancelar_reserva(reserva_id),
        url_for("reservas"), url_for("reservas"), "Reserva cancelada.",
    )


@app.get("/algoritmos")
def algoritmos():
    return render_template("algoritmos.html", titulo="Estructuras y Big O", datos=biblioteca.analisis_estructuras())


@app.errorhandler(404)
def no_encontrado(error):
    return render_template("error.html", titulo="No encontrado", mensaje="La página solicitada no existe."), 404


@app.errorhandler(400)
def solicitud_invalida(error):
    return render_template("error.html", titulo="Solicitud inválida", mensaje=str(error.description)), 400


@app.errorhandler(413)
def contenido_excesivo(error):
    return render_template("error.html", titulo="Formulario demasiado grande", mensaje="El formulario supera el tamaño permitido."), 413


@app.errorhandler(ValueError)
def datos_invalidos(error):
    app.logger.error("Error de validación no recuperable: %s", error)
    return render_template("error.html", titulo="Error en los datos", mensaje=str(error)), 500


if __name__ == "__main__":
    datos.inicializar()
    app.run(host="127.0.0.1", port=5000, debug=False)
