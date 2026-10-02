from flask import Blueprint, render_template
from db import get_connection

dispatch_bp = Blueprint("dispatch_bp", __name__)

@dispatch_bp.route("/logistica")
def dispatch():
	conn = get_connection()
	cursor = conn.cursor()
	cursor.execute("SELECT TOP 50 * FROM IGOR_CG_CLIENTES")
	columns = [col[0] for col in cursor.description]
	rows = cursor.fetchall()
	conn.close()

	return render_template("clients.html", columns=columns, rows=rows)