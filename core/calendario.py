"""Operaciones de calendario gregoriano hechas con aritmética y funciones.

No usa datetime, date ni timedelta. Se consulta el reloj del sistema con
`time.localtime` (eso no calcula las fechas: solo obtiene el instante actual).
Las conversiones, validaciones, sumas y diferencias se hacen manualmente.
"""

import time


DIAS_MES = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def es_bisiesto(anio):
    return anio % 400 == 0 or (anio % 4 == 0 and anio % 100 != 0)


def dias_del_mes(anio, mes):
    if mes < 1 or mes > 12:
        raise ValueError("El mes debe estar entre 1 y 12.")
    if mes == 2 and es_bisiesto(anio):
        return 29
    return DIAS_MES[mes - 1]


def _solo_digitos(texto):
    for caracter in texto:
        if caracter < "0" or caracter > "9":
            return False
    return True


def _partes_fecha(fecha):
    if (not isinstance(fecha, str) or len(fecha) != 10 or
            fecha[4] != "-" or fecha[7] != "-" or
            not _solo_digitos(fecha[0:4] + fecha[5:7] + fecha[8:10])):
        raise ValueError("La fecha debe tener formato AAAA-MM-DD.")
    anio, mes, dia = int(fecha[0:4]), int(fecha[5:7]), int(fecha[8:10])
    if anio < 1 or anio > 9999 or mes < 1 or mes > 12:
        raise ValueError("La fecha contiene un año o mes inválido.")
    if dia < 1 or dia > dias_del_mes(anio, mes):
        raise ValueError("La fecha contiene un día inválido.")
    return anio, mes, dia


def _dias_antes_del_anio(anio):
    anterior = anio - 1
    return 365 * anterior + anterior // 4 - anterior // 100 + anterior // 400


def fecha_a_dias(fecha):
    """Convierte AAAA-MM-DD en número de día desde 0001-01-01 (día 1)."""
    anio, mes, dia = _partes_fecha(fecha)
    acumulado = _dias_antes_del_anio(anio) + dia
    for m in range(1, mes):
        acumulado += dias_del_mes(anio, m)
    return acumulado


def dias_a_fecha(numero):
    """Transforma el ordinal en AAAA-MM-DD; búsqueda binaria del año."""
    maximo = _dias_antes_del_anio(10000)
    if type(numero) is not int or numero < 1 or numero > maximo:
        raise ValueError("El día está fuera del calendario compatible (años 1-9999).")
    inicio, fin = 1, 9999
    while inicio <= fin:
        medio = (inicio + fin) // 2
        primer_dia = _dias_antes_del_anio(medio) + 1
        siguiente = _dias_antes_del_anio(medio + 1) + 1
        if numero < primer_dia:
            fin = medio - 1
        elif numero >= siguiente:
            inicio = medio + 1
        else:
            anio = medio
            break
    restante = numero - _dias_antes_del_anio(anio)
    mes = 1
    while restante > dias_del_mes(anio, mes):
        restante -= dias_del_mes(anio, mes)
        mes += 1
    return f"{anio:04d}-{mes:02d}-{restante:02d}"


def sumar_dias(fecha, cantidad):
    if type(cantidad) is not int:
        raise ValueError("La cantidad de días debe ser un entero.")
    return dias_a_fecha(fecha_a_dias(fecha) + cantidad)


def diferencia_dias(desde, hasta):
    """Positivo si `hasta` es posterior a `desde`."""
    return fecha_a_dias(hasta) - fecha_a_dias(desde)


def validar_fecha_hora(valor):
    """Valida ISO local: AAAA-MM-DDTHH:MM:SS[.ffffff]."""
    if (not isinstance(valor, str) or len(valor) < 19 or
            valor[10] != "T" or valor[13] != ":" or valor[16] != ":" or
            not _solo_digitos(valor[11:13] + valor[14:16] + valor[17:19])):
        raise ValueError("Fecha y hora inválidas.")
    fecha_a_dias(valor[:10])
    hora, minuto, segundo = int(valor[11:13]), int(valor[14:16]), int(valor[17:19])
    if hora > 23 or minuto > 59 or segundo > 59:
        raise ValueError("Hora fuera del rango permitido.")
    if len(valor) > 19:
        fraccion = valor[19:]
        if (len(fraccion) < 2 or len(fraccion) > 7 or
                fraccion[0] != "." or not _solo_digitos(fraccion[1:])):
            raise ValueError("Fracción de segundos inválida.")
    return valor


def fecha_hoy():
    actual = time.localtime()
    return f"{actual.tm_year:04d}-{actual.tm_mon:02d}-{actual.tm_mday:02d}"


def fecha_hora_actual():
    instante = time.time_ns()
    actual = time.localtime(instante // 1_000_000_000)
    micros = (instante % 1_000_000_000) // 1000
    return (f"{actual.tm_year:04d}-{actual.tm_mon:02d}-{actual.tm_mday:02d}T"
            f"{actual.tm_hour:02d}:{actual.tm_min:02d}:{actual.tm_sec:02d}.{micros:06d}")


def anio_actual():
    return time.localtime().tm_year
