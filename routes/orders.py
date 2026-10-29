import json

from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, session, url_for)

from db import run_select, run_transaction
from enums.delivery_status import deliveryStatus
from enums.order_status import OPEN_ORDER_STATUS, orderStatus
from enums.table_names import Table
from services.errors import StaleDataError
from services.order_service import (as_date, get_basket_composition,
                                    get_orders, get_today,
                                    save_delivery_address, update_order_stock)
from services.routes_service import (getAvailableAddresses,
                                     getAvailableBaskets, getAvailableClients,
                                     getAvailableOrderStatus)
from services.status_transitions import get_allowed_status
from services.validate_service import (validate_address_belonging,
                                       validate_date, validate_delivery,
                                       validate_id, validate_isDelivery_check,
                                       validate_opt_text, validate_order_items,
                                       validate_order_status,
                                       validate_order_stock, validate_price,
                                       validate_status_transition)

orders_bp = Blueprint("orders_bp", __name__)
order_mode = "ORDER"

@orders_bp.route("/pedidos")
def orders():
	columns, rows, page, total_pages, search = get_orders()

	available_clients = getAvailableClients()
	available_baskets = getAvailableBaskets()
	statuses = getAvailableOrderStatus()
	available_addresses = getAvailableAddresses()

	return render_template("orders/orders.html",
						columns=columns,
						rows=rows,
						page=page,
						total_pages=total_pages,
						search=search,
						user=session.get("username"),
						available_clients=available_clients,
						available_baskets=available_baskets,
						order_statuses=statuses,
						available_addresses=available_addresses,
						today=get_today())

@orders_bp.route('/basket_composition/<int:id>')
def basket_composition(id):
	return jsonify(get_basket_composition(id))

@orders_bp.route("/search_order")
def orders_search():
	columns, rows, _, _, search = get_orders()

	return render_template("orders/_orders_table_rows.html",
							columns=columns,
							rows=rows,
							search=search)

@orders_bp.route("/new_order", methods=["POST"])
def new_order():
	try:
		items_payload = json.loads(request.form["items"])
	except (KeyError, json.JSONDecodeError):
		return "Itens do pedido inválidos", 400

	try:
		delivery_details = json.loads(request.form["deliveryDetails"])
	except (KeyError, json.JSONDecodeError):
		return "Detalhes de entrega inválidos", 400

	try:
		client = request.form["client"]
		if not validate_id(Table.Clients, "client_id", client):
			return "Cliente inválido", 400
		date = validate_date(request.form["date"])
		deliveryDate = validate_date(request.form["deliveryDate"], date, False)
		orderPrice = validate_price(request.form["orderPrice"])	
		status = validate_order_status(orderStatus.PENDING.name)
		items_payload = validate_order_items(items_payload)
		is_delivery = request.form.get("isDelivery")
		is_delivery = validate_isDelivery_check(is_delivery, delivery_details)
		
		address_id = None
		delivery_fee = 0.00

		if is_delivery:
			delivery_details = validate_delivery(delivery_details)

			address_id = delivery_details.get("address_id")
			address_txt = delivery_details.get("address_txt")
			delivery_fee = delivery_details.get("delivery_fee")

			if address_id is not None:
				validate_address_belonging(client, address_id)
				
		obs = validate_opt_text(request.form.get('obs', ''), "Observação", 255)
		items = json.dumps(items_payload)

		with run_transaction() as cursor:
			validate_order_stock(cursor, items_payload)

			if is_delivery:
				address_id = save_delivery_address(cursor, client, address_id, address_txt)
			
			cursor.execute("""
			INSERT INTO CELEBRAR_ORDERS
			(client_id, order_date, delivery_date,
			order_status, order_subtotal, obs,
			order_items, isDelivery, address_id, delivery_fee)
			OUTPUT INSERTED.order_id
			VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
			""", (client, date, deliveryDate, status, orderPrice, obs, items, is_delivery, address_id, delivery_fee))

			order_id = cursor.fetchone()[0]
		
			for item in items_payload:
				cursor.execute("""
				INSERT INTO CELEBRAR_ORDER_ITEMS
				(basket_id, order_id, amount)
				VALUES (?, ?, ?)
				""", (item['basket_id'], order_id, item['quantity']))
		
	except KeyError:
		return "Dados do pedido inválidos", 400
	except ValueError as e:
		return str(e), 400

	return redirect(request.referrer or url_for("orders_bp.orders"))

@orders_bp.route("/order_data/<int:id>")
def order_data(id):
	columns, rows = run_select("""
	SELECT
	o.order_id, o.client_id, c.client_name,
	o.order_date, o.delivery_date, o.order_status,
	o.order_subtotal, o.obs, o.order_items, o.delivery_id,
	o.isDelivery, o.address_id, o.delivery_fee, o.order_total
	FROM CELEBRAR_ORDERS o
	JOIN CELEBRAR_CLIENTS c
	ON o.client_id = c.client_id
	WHERE o.order_id = ? AND o.isDeleted = 0
	""", (id,))

	if not rows:
		return jsonify({"error": "Item not found"}), 404

	row = rows[0]
	order = dict(zip(columns, row))

	if order["order_date"]:
		order["order_date"] = order["order_date"].strftime("%Y-%m-%d")
	if order["delivery_date"]:
		order["delivery_date"] = order["delivery_date"].strftime("%Y-%m-%d")

	order["order_items"] = json.loads(order["order_items"])

	baskets_ids = list({item["basket_id"] for item in order["order_items"]})

	if baskets_ids:
		placeholders = ",".join("?" * len(baskets_ids))
		_, basket_rows = run_select(f"""
		SELECT
		basket_id, basket_name, basket_price
		FROM CELEBRAR_BASKETS
		WHERE isDeleted = 0
		AND basket_id IN ({placeholders})
		""", tuple(baskets_ids))
	else:
		basket_rows = []

	basket_lookup = {
		b_row[0]: {
			"name": b_row[1],
			"price": float(b_row[2])
			if b_row[2] is not None else None
		}
		for b_row in basket_rows
	}

	for item in order["order_items"]:
		comp = get_basket_composition(item["basket_id"])
		meta = basket_lookup.get(item["basket_id"], {})

		item["basket_name"] = meta.get("name")
		item["basket_price"] = meta.get("price")
		item["groups"] = comp["groups"]

		choices_by_group = {c["group_id"]: c["item_id"] for c in item.get("choices", [])}

		for group in item["groups"]:
			flat_choices = choices_by_group.get(group["group_id"], [])

			group["selected"] = [
				flat_choices[i:i + int(group["quantity"])]
				for i in range(0, len(flat_choices), int(group["quantity"]))
			]


	allowed = get_allowed_status(order["order_status"], order_mode)
	if order["delivery_id"] is not None:
		allowed = allowed - {orderStatus.CANCELLED.name, orderStatus.DELIVERED.name}
	order["allowed_status"] = sorted(allowed)

	return jsonify(order)

@orders_bp.route("/update_order", methods=["POST"])
def update_order():
	try:
		id = request.form["id"]
		if not validate_id(Table.Orders, "order_id", id):
			raise ValueError("Pedido inválido")
		status = validate_order_status(request.form["status"])
	except KeyError:
		return "Dados do pedido inválidos", 400
	except ValueError as e:
		return str(e), 400

	_, data_rows = run_select("""
	SELECT
	client_id, order_date, delivery_date, order_status,
	order_subtotal, obs, order_items, delivery_id
	FROM CELEBRAR_ORDERS
	WHERE order_id = ?
	AND isDeleted = 0
	""", (id,))

	if not data_rows:
		return "Pedido não encontrado.", 404

	current_client = data_rows[0][0]
	current_date = data_rows[0][1]
	current_delivery_date = data_rows[0][2]
	current_status = data_rows[0][3]
	current_orderPrice = data_rows[0][4]
	current_obs = data_rows[0][5]
	current_items = data_rows[0][6]
	current_delivery_id = data_rows[0][7]

	if current_status not in OPEN_ORDER_STATUS:
		return "Um pedido encerrado não pode ser alterado.", 400

	try:
		validate_status_transition(current_status, status, order_mode)

		if current_status == orderStatus.PENDING.name:
			client = request.form["client"]
			if not validate_id(Table.Clients, "client_id", client):
				raise ValueError("Cliente inválido")
			date = validate_date(request.form["date"])
			orderPrice = validate_price(request.form["orderPrice"])
			items_payload = validate_order_items(json.loads(request.form["items"]))
			obs = validate_opt_text(request.form.get('obs', ''), "Observação", 255)
			items = json.dumps(items_payload)
		else:
			client = current_client
			date = current_date
			orderPrice = current_orderPrice
			obs = current_obs
			items = current_items
			items_payload = json.loads(current_items)
		
		deliveryDate = validate_date(request.form["deliveryDate"], date, False)

		delivery_details = json.loads(request.form["deliveryDetails"])
		is_delivery = validate_isDelivery_check(request.form.get("isDelivery"), delivery_details)

		if current_delivery_id is not None and status in (orderStatus.CANCELLED.name, orderStatus.DELIVERED.name):
			raise ValueError(f"Remova o pedido da entrega {current_delivery_id} antes de alterar o status.")

		date_change = as_date(deliveryDate) != as_date(current_delivery_date)
		release = not is_delivery or date_change

		address_id = None
		address_txt = None
		delivery_fee = 0.00

		if is_delivery:
			delivery_details = validate_delivery(delivery_details)
			address_id = delivery_details.get("address_id")
			address_txt = delivery_details.get("address_txt")
			delivery_fee = delivery_details.get("delivery_fee")

			if address_id is not None:
				validate_address_belonging(client, address_id)

	except (KeyError, TypeError):
		return "Dados do pedido inválidos", 400
	except ValueError as e:
		return str(e), 400
	
	notices = []
	
	try:
		with run_transaction() as cursor:
			if is_delivery:
				address_id = save_delivery_address(cursor, client, address_id, address_txt)

			cursor.execute("""
			UPDATE CELEBRAR_ORDERS
			SET
			client_id = ?,
			order_date = ?,
			delivery_date = ?,
			order_status = ?,
			order_subtotal = ?,
			obs = ?,
			order_items = ?,
			isDelivery = ?,
			address_id = ?,
			delivery_fee = ?
			WHERE order_id = ?
			AND order_status = ?
			AND isDeleted = 0
			""", (client, date, deliveryDate, status, orderPrice, obs, items, is_delivery, address_id, delivery_fee, id, current_status))

			if cursor.rowcount != 1:
				raise StaleDataError("O pedido já foi alterado. Recarregue a página.")

			if release:
				cursor.execute("""
				SELECT
				delivery_id
				FROM CELEBRAR_ORDERS
				WHERE order_id = ?
				AND delivery_id IS NOT NULL
				AND isDeleted = 0
				""", (id,))

				row = cursor.fetchone()

				if row is not None:
					released_delivery_id = row[0]

					cursor.execute("""
					UPDATE CELEBRAR_ORDERS
					SET delivery_id = NULL
					WHERE order_id = ?
					AND delivery_id = ?
					AND isDeleted = 0
					""", (id,released_delivery_id))

					notices.append(f"Pedido removido da entrega #{released_delivery_id}.")

					cursor.execute("""
					SELECT COUNT(*)
					FROM CELEBRAR_ORDERS
					WHERE delivery_id = ?
					AND isDeleted = 0
					""", (released_delivery_id,))

					delivery_orders = cursor.fetchone()[0]

					if delivery_orders == 0:
						cursor.execute("""
						UPDATE CELEBRAR_DELIVERIES
						SET delivery_status = ?
						WHERE delivery_id = ?
						AND isDeleted = 0
						""", (deliveryStatus.CANCELLED.name, released_delivery_id))

						notices.append(f"Entrega #{released_delivery_id} cancelada por ficar sem pedidos.")
			
			changed = items_payload != json.loads(current_items)

			if current_status == "PENDING":
				if status == "CONFIRMED" or (status == "PENDING" and changed):
					validate_order_stock(cursor, items_payload, exclude_order_id=id)

				if status == "CONFIRMED":
					update_order_stock(cursor, items_payload, "deduct", id)
					notices.append("Estoque atualizado: itens do pedido descontados.")

			if status == "CANCELLED" and current_status not in {"PENDING", "CANCELLED"}:
				update_order_stock(cursor, items_payload, "increase", id)
				notices.append("Estoque atualizado: itens do pedido devolvidos.")
			
			cursor.execute("""
			DELETE FROM CELEBRAR_ORDER_ITEMS
			WHERE order_id = ?
			""", (id,))

			for item in items_payload:
				cursor.execute("""
				INSERT INTO CELEBRAR_ORDER_ITEMS
				(basket_id, order_id, amount)
				VALUES (?, ?, ?)
				""", (item['basket_id'], id, item['quantity']))

	except StaleDataError as e:
		return str(e), 409
	except ValueError as e:
		return str(e), 400

	flash(f"Pedido #{id} atualizado com sucesso!", "success")
	for notice in notices:
		flash(notice, "info")

	return "", 204