"""Funciones auxiliares: validación de datos y formato de montos."""
import math
from datetime import datetime

LONGITUD_MAX_DESCRIPCION = 100


def validar_gasto(fecha, descripcion, monto):
    """Valida los datos de un gasto y devuelve la lista de errores (vacía si todo está bien)."""
    errores = []

    try:
        datetime.strptime(fecha or "", "%Y-%m-%d")
    except ValueError:
        errores.append("La fecha no es válida.")

    descripcion = (descripcion or "").strip()
    if not descripcion:
        errores.append("La descripción es obligatoria.")
    elif len(descripcion) > LONGITUD_MAX_DESCRIPCION:
        errores.append(f"La descripción no debe superar {LONGITUD_MAX_DESCRIPCION} caracteres.")

    try:
        valor = float(monto)
        if not math.isfinite(valor) or valor <= 0:
            errores.append("El monto debe ser un número mayor que cero.")
    except (TypeError, ValueError):
        errores.append("El monto debe ser un número mayor que cero.")

    return errores


def formatear_monto(monto):
    """Convierte un número en texto con formato de soles: 1234.5 -> 'S/ 1,234.50'."""
    return f"S/ {monto:,.2f}"
