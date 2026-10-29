from flask import (Blueprint, jsonify, redirect, render_template, request,
                   session, url_for)

from db import run_select, run_update
from enums.table_names import Table
from services.client_service import client_exists, get_clients
from services.validate_service import (client_has_open_orders, validate_id,
                                       validate_name, validate_phone)

clients_bp = Blueprint("clients_bp", __name__)

@clients_bp.route("/clientes")
def clients():
	columns, rows, page, total_pages, search = get_clients()
	
	return render_template("clients/clients.html",
						columns=columns,
						rows=rows,
						page=page,
						total_pages=total_pages,
						search=search,
						user=session.get("username"))

@clients_bp.route("/search_client")
def clients_search():
	columns, rows, _, _, search = get_clients()

	return render_template("clients/_clients_table_rows.html",
							columns=columns,
							rows=rows,
							search=search)

@clients_bp.route("/new_client", methods=["POST"])
def new_client():
	try:
		name = validate_name(request.form["name"])
		phone = validate_phone(request.form["phone"])
	except ValueError as e:
		return str(e), 400

	if client_exists(name, phone):
		return "Cliente já cadastrado", 400

	run_update("""
	INSERT INTO CELEBRAR_CLIENTS
	(client_name, client_phone)
	VALUES (?, ?)
	""", (name, phone))

	return redirect(request.referrer or url_for("clients_bp.clients"))

@clients_bp.route("/client_data/<int:id>")
def client_data(id):
	columns, rows = run_select("""
	SELECT
	client_id, client_name, client_phone
	FROM CELEBRAR_CLIENTS WHERE client_id = ? AND isDeleted = 0""", (id,)
	)
	if not rows:
		return jsonify({"error": "Client not found"}), 404
	row = rows[0]
	return jsonify(dict(zip(columns, row)))

@clients_bp.route("/update_client", methods=["POST"])
def update_client():
	try:
		id = request.form["id"]
		if not validate_id(Table.Clients, "client_id", id):
			raise ValueError("Cliente inválido")
		if client_has_open_orders(id):
			raise ValueError("Esse cliente possui pedido em aberto")
		name = validate_name(request.form["name"])
		phone = validate_phone(request.form["phone"])
	except ValueError as e:
		return str(e), 400

	if client_exists(name, phone, id):
		return "Cliente já cadastrado", 400

	run_update("""
	UPDATE CELEBRAR_CLIENTS
	SET
	client_name = ?,
	client_phone = ?
	WHERE client_id = ?
	""", (name, phone, id))

	return redirect(url_for("clients_bp.clients"))

@clients_bp.route("/delete_client/<int:id>", methods=["POST"])
def delete_client(id):
	try:
		if not validate_id(Table.Clients, "client_id", id):
			raise ValueError("Cliente inválido")
		if client_has_open_orders(id):
			raise ValueError("Esse cliente possui pedido em aberto")
	except ValueError as e:
		return str(e), 400
	
	run_update("""
	UPDATE CELEBRAR_CLIENTS
	SET
	isDeleted = 1
	WHERE client_id = ?
	""", (id,))

	return "", 204