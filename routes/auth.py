from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash

from db import run_select

auth_bp = Blueprint("auth_bp", __name__)

@auth_bp.route("/", methods=["GET", "POST"])
def login(): 
	if request.method == "GET":
		return render_template("login.html")

	try:	
		login_id = request.form.get("login_id", "")
		password = request.form.get("password", "")
	except ValueError as e:
		flash(str(e), "error")
		return redirect(url_for("auth_bp.login"))

	query = """
	SELECT id_usuario, nome_usuario, senha_hash
	FROM IGOR_CG_USUARIOS
	WHERE (LOWER(email) = ? OR LOWER(nome_usuario) = ?)
	AND isDeleted = 0
	"""

	_, rows = run_select(query, (login_id, login_id))

	if not rows or not check_password_hash(rows[0][2], password):
		flash("E-mail ou senha inválidos.", "error")
		return redirect(url_for("auth_bp.login"))

	user_id = rows[0][0]
	username = rows[0][1]

	session.clear()
	session["user_id"] = user_id
	session["username"] = username

	return redirect(url_for("home_bp.home"))

@auth_bp.route("/logout", methods=["POST"])
def logout():
	session.clear()
	return redirect(url_for("auth_bp.login"))