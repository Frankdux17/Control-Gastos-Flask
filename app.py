"""Control de Gastos: aplicación web con Flask y SQLite."""
import csv
import io
import logging
import os
import sqlite3
from datetime import date
from functools import wraps

from flask import (Flask, Response, flash, g, redirect, render_template,
                   request, session, url_for)

from utils import formatear_monto, validar_gasto

USUARIO = "admin"
CLAVE = "123"


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "clave-de-desarrollo"),
        DATABASE=os.path.join(app.root_path, "gastos.db"),
    )
    if config:
        app.config.update(config)

    logging.basicConfig(level=logging.INFO)
    app.jinja_env.filters["soles"] = formatear_monto

    # ---------- Base de datos ----------
    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def cerrar_db(error=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    with app.app_context():
        db = get_db()
        db.execute("""
            CREATE TABLE IF NOT EXISTS gastos (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha       TEXT    NOT NULL,
                descripcion TEXT    NOT NULL,
                monto       REAL    NOT NULL
            )
        """)
        db.commit()

    # ---------- Seguridad ----------
    def login_required(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            if "usuario" not in session:
                flash("Inicia sesión para continuar.", "aviso")
                return redirect(url_for("login"))
            return vista(*args, **kwargs)
        return envoltura

    # ---------- Rutas ----------
    @app.route("/")
    def inicio():
        if "usuario" in session:
            return redirect(url_for("gastos"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            usuario = request.form.get("usuario", "").strip()
            clave = request.form.get("clave", "")
            if usuario == USUARIO and clave == CLAVE:
                session.clear()
                session["usuario"] = usuario
                app.logger.info("Inicio de sesión correcto")
                return redirect(url_for("gastos"))
            app.logger.warning("Intento de acceso fallido")
            flash("Credenciales inválidas. Revisa el usuario y la clave.", "error")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("Sesión cerrada.", "ok")
        return redirect(url_for("login"))

    @app.route("/gastos", methods=["GET", "POST"])
    @login_required
    def gastos():
        db = get_db()
        if request.method == "POST":
            fecha = request.form.get("fecha", "")
            descripcion = request.form.get("descripcion", "").strip()
            monto = request.form.get("monto", "")
            errores = validar_gasto(fecha, descripcion, monto)
            if errores:
                for e in errores:
                    flash(e, "error")
            else:
                db.execute(
                    "INSERT INTO gastos (fecha, descripcion, monto) VALUES (?, ?, ?)",
                    (fecha, descripcion, round(float(monto), 2)),
                )
                db.commit()
                app.logger.info("Gasto registrado: %s", descripcion)
                flash("Gasto registrado.", "ok")
            return redirect(url_for("gastos"))

        lista = db.execute(
            "SELECT * FROM gastos ORDER BY fecha DESC, id DESC"
        ).fetchall()
        total = sum(g_["monto"] for g_ in lista)
        return render_template("gastos.html", gastos=lista, total=total,
                               hoy=date.today().isoformat())

    @app.route("/gastos/<int:gasto_id>/eliminar", methods=["POST"])
    @login_required
    def eliminar(gasto_id):
        db = get_db()
        cur = db.execute("DELETE FROM gastos WHERE id = ?", (gasto_id,))
        db.commit()
        if cur.rowcount:
            flash("Gasto eliminado.", "ok")
        else:
            flash("El gasto no existe.", "error")
        return redirect(url_for("gastos"))

    def consultar_reporte(desde, hasta):
        condiciones, parametros = [], []
        if desde:
            condiciones.append("fecha >= ?")
            parametros.append(desde)
        if hasta:
            condiciones.append("fecha <= ?")
            parametros.append(hasta)
        where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
        db = get_db()
        detalle = db.execute(
            f"SELECT * FROM gastos {where} ORDER BY fecha, id", parametros
        ).fetchall()
        por_mes = db.execute(
            f"""SELECT strftime('%Y-%m', fecha) AS mes, COUNT(*) AS cantidad,
                       SUM(monto) AS total
                FROM gastos {where} GROUP BY mes ORDER BY mes""",
            parametros,
        ).fetchall()
        return detalle, por_mes

    @app.route("/reporte")
    @login_required
    def reporte():
        desde = request.args.get("desde", "")
        hasta = request.args.get("hasta", "")
        detalle, por_mes = consultar_reporte(desde, hasta)
        total = sum(f["monto"] for f in detalle)
        promedio = total / len(detalle) if detalle else 0
        mayor = max(detalle, key=lambda f: f["monto"]) if detalle else None
        return render_template("reporte.html", detalle=detalle, por_mes=por_mes,
                               total=total, promedio=promedio, mayor=mayor,
                               desde=desde, hasta=hasta)

    @app.route("/reporte/csv")
    @login_required
    def reporte_csv():
        detalle, _ = consultar_reporte(request.args.get("desde", ""),
                                       request.args.get("hasta", ""))
        salida = io.StringIO()
        escritor = csv.writer(salida)
        escritor.writerow(["Fecha", "Descripción", "Monto"])
        for f in detalle:
            escritor.writerow([f["fecha"], f["descripcion"], f"{f['monto']:.2f}"])
        escritor.writerow(["", "TOTAL", f"{sum(f['monto'] for f in detalle):.2f}"])
        return Response(
            "\ufeff" + salida.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=reporte_gastos.csv"},
        )

    @app.errorhandler(404)
    def no_encontrado(error):
        return render_template("404.html"), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
