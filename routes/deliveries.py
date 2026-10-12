import json
from datetime import date

from flask import (Blueprint, jsonify, redirect, render_template, request,
                   url_for)

from db import run_select, run_transaction
from enums.delivery_status import OPEN_DELIVERY_STATUS, deliveryStatus
from enums.order_status import orderStatus
from enums.table_names import Table
from services.deliveries_service import get_deliveries
from services.routes_service import (getAvailableAddresses,
                                     getAvailableCouriers, getAvailableDates,
                                     getAvailableDeliveryStatus,
                                     getAvailableOrders)
from services.status_transitions import get_allowed_status
from services.validate_service import (validate_date_id,
                                       validate_delivery_orders, validate_id)

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

# @deliveries_bp.route("/entregas/update", methods=["POST"])
# def update_order():
# 	try:
# 		id = request.form["id"]
# 		if not validate_id(Table.Orders, "id_pedido", id):
# 			raise ValueError("Pedido inválido")
# 		status = validate_order_status(request.form["status"])
# 	except KeyError:
# 		return "Dados do pedido inválidos", 400
# 	except ValueError as e:
# 		return str(e), 400

# 	_, data_rows = run_select("""
# 	SELECT
# 	id_cliente, data_pedido, data_entrega, status_pedido,
# 	valor_pedido, observacao, itens_pedido
# 	FROM IGOR_CG_PEDIDOS
# 	WHERE id_pedido = ?
# 	AND isDeleted = 0
# 	""", (id,))

# 	if not data_rows:
# 		return "Pedido não encontrado.", 404

# 	current_client = data_rows[0][0]
# 	current_date = data_rows[0][1]
# 	current_status = data_rows[0][3]
# 	current_orderPrice = data_rows[0][4]
# 	current_obs = data_rows[0][5]
# 	current_items = data_rows[0][6]

# 	if current_status not in OPEN_ORDER_STATUS:
# 		return "Um pedido encerrado não pode ser alterado.", 400

# 	try:
# 		validate_status_transition(current_status, status)

# 		if current_status == orderStatus.PENDING.name:
# 			client = request.form["client"]
# 			if not validate_id(Table.Clients, "id_cliente", client):
# 				raise ValueError("Cliente inválido")
# 			date = validate_date(request.form["date"])
# 			orderPrice = validate_price(request.form["orderPrice"])
# 			items_payload = validate_order_items(json.loads(request.form["items"]))
# 			obs = request.form.get('obs', '')
# 			items = json.dumps(items_payload)
# 		else:
# 			client = current_client
# 			date = current_date
# 			orderPrice = current_orderPrice
# 			obs = current_obs
# 			items = current_items
# 			items_payload = json.loads(current_items)
		
# 		deliveryDate = validate_date(request.form["deliveryDate"], date, False)

# 		delivery_details = json.loads(request.form["deliveryDetails"])
# 		is_delivery = validate_isDelivery_check(request.form.get("isDelivery"), delivery_details)

# 		address_id = None
# 		address_txt = None
# 		delivery_fee = 0.00

# 		if is_delivery:
# 			delivery_details = validate_delivery(delivery_details)
# 			address_id = delivery_details.get("address_id")
# 			address_txt = delivery_details.get("address_txt")
# 			delivery_fee = delivery_details.get("delivery_fee")

# 			if address_id is not None:
# 				validate_address_belonging(client, address_id)

# 	except (KeyError, TypeError):
# 		return "Dados do pedido inválidos", 400
# 	except ValueError as e:
# 		return str(e), 400
	
# 	try:
# 		with run_transaction() as cursor:
# 			if is_delivery and address_id is None:
# 				cursor.execute("""
# 				INSERT INTO IGOR_CG_ENDERECOS_CLIENTES
# 				(id_cliente, endereco)
# 				OUTPUT INSERTED.id_endereco
# 				VALUES (?, ?)
# 				""", (client, address_txt))

# 				address_id = cursor.fetchone()[0]

# 			cursor.execute("""
# 			UPDATE IGOR_CG_PEDIDOS
# 			SET
# 			id_cliente = ?,
# 			data_pedido = ?,
# 			data_entrega = ?,
# 			status_pedido = ?,
# 			valor_pedido = ?,
# 			observacao = ?,
# 			itens_pedido = ?,
# 			isDelivery = ?,
# 			id_endereco = ?,
# 			taxa_entrega = ?
# 			WHERE id_pedido = ?
# 			AND status_pedido = ?
# 			AND isDeleted = 0
# 			""", (client, date, deliveryDate, status, orderPrice, obs, items, is_delivery, address_id, delivery_fee, id, current_status))

# 			if cursor.rowcount != 1:
# 				raise ValueError("O pedido já foi alterado. Recarregue a página.")
			
# 			changed = items_payload != json.loads(current_items)

# 			if current_status == "PENDING":
# 				if status == "CONFIRMED" or (status == "PENDING" and changed):
# 					validate_order_stock(cursor, items_payload, exclude_order_id=id)

# 				if status == "CONFIRMED":
# 					update_order_stock(cursor, items_payload, "deduct", id)

# 			if status == "CANCELLED" and current_status not in {"PENDING", "CANCELLED"}:
# 				update_order_stock(cursor, items_payload, "increase", id)
			
# 			cursor.execute("""
# 			DELETE FROM IGOR_CG_CESTAS_PEDIDO
# 			WHERE id_pedido = ?
# 			""", (id,))

# 			for item in items_payload:
# 				cursor.execute("""
# 				INSERT INTO IGOR_CG_CESTAS_PEDIDO
# 				(id_produto, id_pedido, quantidade)
# 				VALUES (?, ?, ?)
# 				""", (item['basket_id'], id, item['quantity']))

# 	except ValueError as e:
# 		return str(e), 400

# 	return redirect(url_for("deliveries_bp.orders"))