from flask import (Blueprint, jsonify, redirect, render_template, request,
                   url_for)

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
						user="Vendedor")

@clients_bp.route("/clientes/search")
def clients_search():
	columns, rows, _, _, _ = get_clients()

	return render_template("clients/_clients_table_rows.html",
							columns=columns,
							rows=rows)

@clients_bp.route("/novo_cliente", methods=["POST"])
def new_client():
	try:
		name = validate_name(request.form["name"])
		phone = validate_phone(request.form["phone"])
	except ValueError as e:
		return str(e), 400

	if client_exists(name, phone):
		return "Cliente já cadastrado", 400

	run_update("""
	INSERT INTO IGOR_CG_CLIENTES
	(nome_razao, telefone)
	VALUES (?, ?)
	""", (name, phone))

	return redirect(request.referrer or url_for("clients_bp.clients"))

@clients_bp.route("/clientes/<int:id>/data")
def client_data(id):
	columns, rows = run_select("""
	SELECT
	id_cliente, nome_razao, telefone
	FROM IGOR_CG_CLIENTES WHERE id_cliente = ? AND isDeleted = 0""", (id,)
	)
	if not rows:
		return jsonify({"error": "Client not found"}), 404
	row = rows[0]
	return jsonify(dict(zip(columns, row)))

@clients_bp.route("/clientes/update", methods=["POST"])
def update_client():
	try:
		id = request.form["id"]
		if not validate_id(Table.Clients, "id_cliente", id):
			raise ValueError("Cliente inválido")
		name = validate_name(request.form["name"])
		phone = validate_phone(request.form["phone"])
	except ValueError as e:
		return str(e), 400

	if client_exists(name, phone, id):
		return "Cliente já cadastrado", 400

	run_update("""
	UPDATE IGOR_CG_CLIENTES
	SET
	nome_razao = ?,
	telefone = ?
	WHERE id_cliente = ?
	""", (name, phone, id))

	return redirect(url_for("clients_bp.clients"))

@clients_bp.route("/clientes/<int:id>/delete", methods=["POST"])
def delete_client(id):
	try:
		if not validate_id(Table.Clients, "id_cliente", id):
			raise ValueError("Cliente inválido")
		if client_has_open_orders(id):
			raise ValueError("Esse cliente possui pedido em aberto")
	except ValueError as e:
		return str(e), 400
	
	run_update("""
	UPDATE IGOR_CG_CLIENTES
	SET
	isDeleted = 1
	WHERE id_cliente = ?
	""", (id,))

	return "", 204