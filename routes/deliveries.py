import json
from datetime import date

from flask import (Blueprint, jsonify, redirect, render_template, request,
                   url_for)

from db import run_select, run_transaction
from enums.delivery_status import OPEN_DELIVERY_STATUS, deliveryStatus
from enums.order_status import orderStatus
from enums.table_names import Table
from services.deliveries_service import get_deliveries, courier_exists
from services.routes_service import (getAvailableAddresses,
                                     getAvailableCouriers, getAvailableDates,
                                     getAvailableDeliveryStatus,
                                     getAvailableOrders)
from services.status_transitions import get_allowed_status
from services.validate_service import (validate_date_id,
                                       validate_delivery_orders,
                                       validate_delivery_status, validate_id,
                                       validate_name, validate_phone,
                                       validate_status_transition, courier_has_open_deliveries)

deliveries_bp = Blueprint("deliveries_bp", __name__)
delivery_mode = "DELIVERY"

@deliveries_bp.route("/entregas")
def deliveries():
	columns, rows, page, total_pages, search = get_deliveries()

	available_couriers = getAvailableCouriers()
	available_dates = getAvailableDates()
	available_orders = getAvailableOrders()
	statuses = getAvailableDeliveryStatus()
	available_addresses = getAvailableAddresses()

	return render_template("deliveries/deliveries.html",
						columns=columns,
						rows=rows,
						page=page,
						total_pages=total_pages,
						search=search,
						user="Vendedor",
						available_couriers=available_couriers,
						available_dates=available_dates,
						available_orders=available_orders,
						statuses=statuses,
						available_addresses=available_addresses)

@deliveries_bp.route("/entregas/search")
def deliveries_search():
	columns, rows, _, _, _ = get_deliveries()

	return render_template("deliveries/_deliveries_table_rows.html",
							columns=columns,
							rows=rows)

@deliveries_bp.route("/nova_entrega", methods=["POST"])
def new_delivery():
	try:
		orders = json.loads(request.form.get("items", ""))
	except json.JSONDecodeError:
		return "Pedidos da entrega inválidos", 400

	try:
		courier = request.form.get("courier", type=int) or None
		if courier is not None and not validate_id(Table.Couriers, "id_entregador", courier):
			return "Entregador inválido", 400
		date_id = request.form["date"]
		if not validate_date_id(date_id):
			return "Data inválida", 400
		delivery_date = date.fromisoformat(date_id)
		status = deliveryStatus.PENDING.name
		orders = validate_delivery_orders(orders, delivery_date)
		
		with run_transaction() as cursor:			
			cursor.execute("""
			INSERT INTO IGOR_CG_ENTREGAS
			(id_entregador, data_entrega, status_entrega)
			OUTPUT INSERTED.id_entrega
			VALUES (?, ?, ?)
			""", (courier, delivery_date, status))

			delivery_id = cursor.fetchone()[0]

			for order in orders:
				cursor.execute("""
				UPDATE IGOR_CG_PEDIDOS
				SET id_entrega = ?
				WHERE id_pedido = ?
				AND isDeleted = 0
				AND isDelivery = 1
				AND id_entrega IS NULL
				AND status_pedido = ?
				AND data_entrega = ?
				""", (delivery_id, order, orderStatus.READY.name, delivery_date))

				if cursor.rowcount != 1:
					raise ValueError("Um ou mais pedidos não estão mais disponíveis para entrega")
		
	except KeyError:
		return "Dados da entrega inválidos", 400
	except ValueError as e:
		return str(e), 400

	return redirect(request.referrer or url_for("deliveries_bp.deliveries"))

@deliveries_bp.route("/entregas/<int:id>/data")
def delivery_data(id):
	columns, rows = run_select("""
	SELECT
	d.id_entrega, d.id_entregador, c.nome_entregador,
	d.data_entrega, d.status_entrega
	FROM IGOR_CG_ENTREGAS d
	LEFT JOIN IGOR_CG_ENTREGADORES c
	ON d.id_entregador = c.id_entregador
	WHERE d.id_entrega = ? AND d.isDeleted = 0
	""", (id,))

	if not rows:
		return jsonify({"error": "Delivery not found"}), 404

	row = rows[0]
	delivery = dict(zip(columns, row))

	if delivery["status_entrega"] not in OPEN_DELIVERY_STATUS:
		return jsonify({"error": "Entrega encerrada"}), 403

	if delivery["data_entrega"]:
		delivery["data_entrega"] = delivery["data_entrega"].strftime("%Y-%m-%d")

	_, order_rows = run_select("""
	SELECT
	p.id_pedido, c.nome_razao, a.endereco
	FROM IGOR_CG_PEDIDOS p
	LEFT JOIN IGOR_CG_CLIENTES c
	ON p.id_cliente = c.id_cliente
	LEFT JOIN IGOR_CG_ENDERECOS_CLIENTES a
	ON p.id_endereco = a.id_endereco
	WHERE p.id_entrega = ?
	AND p.isDeleted = 0
	ORDER BY p.id_pedido
	""", (id,))

	delivery["orders"] = [
		{"id": o_row[0], "title": f"Pedido #{o_row[0]} | {o_row[1] or '---'} | {o_row[2] or '---'}"}
		for o_row in order_rows
	]
	
	delivery["allowed_status"] = sorted(get_allowed_status(delivery["status_entrega"], delivery_mode))

	delivery["available_orders"] = getAvailableOrders(id)
	delivery["available_dates"] = getAvailableDates(id)

	return jsonify(delivery)

@deliveries_bp.route("/entregas/update", methods=["POST"])
def update_delivery():
	try:
		id = request.form["id"]
		if not validate_id(Table.Deliveries, "id_entrega", id):
			raise ValueError("Entrega inválida")
		status = validate_delivery_status(request.form["status"])
		courier = None
		if request.form.get("courier"):
			courier = request.form.get("courier", type=int) or None
			if courier is None or not validate_id(Table.Couriers, "id_entregador", courier):
				return "Entregador inválido", 400

		if courier is None and status in (deliveryStatus.TRANSIT.name, deliveryStatus.DELIVERED.name):
			return "Informe o entregador antes de iniciar a entrega.", 400
	except KeyError:
		return "Dados da entrega inválidos", 400
	except ValueError as e:
		return str(e), 400

	_, data_rows = run_select("""
	SELECT
	data_entrega, status_entrega
	FROM IGOR_CG_ENTREGAS
	WHERE id_entrega = ?
	AND isDeleted = 0
	""", (id,))

	if not data_rows:
		return "Entrega não encontrada.", 404

	current_delivery_date = data_rows[0][0]
	current_status = data_rows[0][1]

	if current_status not in OPEN_DELIVERY_STATUS:
		return "Uma entrega encerrada não pode ser alterada.", 400

	try:
		validate_status_transition(current_status, status, delivery_mode)
		orders = []
		delivery_date = current_delivery_date

		if current_status == deliveryStatus.PENDING.name and status != deliveryStatus.CANCELLED.name:
			date_id = request.form["date"]
			if not validate_date_id(date_id, id):
				return "Data inválida", 400
			delivery_date = date.fromisoformat(date_id)
			
			try:
				orders = json.loads(request.form.get("items", ""))
			except json.JSONDecodeError:
				return "Pedidos da entrega inválidos", 400
			orders = validate_delivery_orders(orders, delivery_date, id)

	except (KeyError, TypeError):
		return "Dados da entrega inválidos", 400
	except ValueError as e:
		return str(e), 400

	try:
		with run_transaction() as cursor:
			cursor.execute("""
			UPDATE IGOR_CG_ENTREGAS
			SET
			id_entregador = ?,
			data_entrega = ?,
			status_entrega = ?
			WHERE id_entrega = ?
			AND isDeleted = 0
			AND status_entrega = ?
			""", (courier, delivery_date, status, id, current_status))

			if cursor.rowcount != 1:
				raise ValueError("A entrega já foi alterada. Recarregue a página.")

			if status == deliveryStatus.CANCELLED.name:
				cursor.execute(f"""
				UPDATE IGOR_CG_PEDIDOS
				SET id_entrega = NULL
				WHERE id_entrega = ?
				""", (id,))

			elif status == deliveryStatus.DELIVERED.name:
				cursor.execute(f"""
				UPDATE IGOR_CG_PEDIDOS
				SET status_pedido = ?
				WHERE id_entrega = ?
				AND isDeleted = 0
				AND status_pedido = ?
				""", (orderStatus.DELIVERED.name, id, orderStatus.READY.name))
				
			elif current_status == deliveryStatus.PENDING.name:
				placeholders = ", ".join("?" * len(orders))

				cursor.execute(f"""
				UPDATE IGOR_CG_PEDIDOS
				SET id_entrega = NULL
				WHERE id_entrega = ?
				AND id_pedido NOT IN ({placeholders})
				""", (id, *orders))

				for order in orders:
					cursor.execute("""
					UPDATE IGOR_CG_PEDIDOS
					SET id_entrega = ?
					WHERE id_pedido = ?
					AND isDeleted = 0
					AND isDelivery = 1
					AND status_pedido = ?
					AND data_entrega = ?
					AND (id_entrega is NULL OR id_entrega = ?)
					""", (id, order, orderStatus.READY.name, delivery_date, id))

					if cursor.rowcount != 1:
						raise ValueError("Um ou mais pedidos não estão mais disponíveis para entrega")

			

	except ValueError as e:
		return str(e), 400


	return redirect(request.referrer or url_for("deliveries_bp.deliveries"))

@deliveries_bp.route("/entregas/entregadores/save", methods=["POST"])
def save_courier():
	try:
		courier_id = request.form.get("courier_id")
		if courier_id:
			if not validate_id(Table.Couriers, "id_entregador", courier_id):
				raise ValueError("Entregador inválido")
		name = validate_name(request.form["courier_name"])
		phone = validate_phone(request.form["courier_phone"])
	except ValueError as e:
		return str(e), 400

	if courier_exists(name, phone, courier_id):
		return "Entregador já cadastrado", 400

	
	with run_transaction() as cursor:
		if courier_id:
			cursor.execute("""
			UPDATE IGOR_CG_ENTREGADORES
			SET
			nome_entregador = ?,
			telefone = ?
			WHERE id_entregador = ?
			""", (name, phone, courier_id))

		else:
			cursor.execute("""
			INSERT INTO IGOR_CG_ENTREGADORES
			(nome_entregador, telefone)
			VALUES (?, ?)
			""", (name, phone))

	return redirect(url_for("deliveries_bp.deliveries"))

@deliveries_bp.route("/entregas/entregadores/<int:id>/delete", methods=["POST"])
def delete_courier(id):
	try:
		if not validate_id(Table.Couriers, "id_entregador", id):
			raise ValueError("Entregador inválido")
		if courier_has_open_deliveries(id):
			raise ValueError("Esse entregador tem uma entrega em aberto")
	except ValueError as e:
		return str(e), 400
	
	with run_transaction() as cursor:
		cursor.execute("""
		UPDATE IGOR_CG_ENTREGADORES
		SET
		isDeleted = 1
		WHERE id_entregador = ?
		""", (id,))

	return "", 204

@deliveries_bp.route("/entregas/entregadores/<int:id>/data")
def group_data(id):
	_, rows = run_select("""
	SELECT nome_entregador, telefone
	FROM IGOR_CG_ENTREGADORES
	WHERE id_entregador = ?
	AND isDeleted = 0
	""", (id,))

	if not rows:
		return jsonify({"error": "Courier not found"}), 404

	courier_name = rows[0][0]
	courier_phone = rows[0][1]

	return jsonify({"name": courier_name, "phone": courier_phone})