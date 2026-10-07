import json

from flask import (Blueprint, jsonify, redirect, render_template, request,
                   url_for)

from db import format_currency, format_date, run_select, run_transaction
from enums.order_status import orderStatus
from enums.table_names import Table
from services.order_service import (get_basket_composition, get_orders,
                                    get_today, update_order_stock)
from services.routes_service import (getAvailableAddresses,
                                     getAvailableBaskets, getAvailableClients,
                                     getAvailableStatus)
from services.status_transitions import get_allowed_status
from services.validate_service import (OPEN_ORDER_STATUS,
                                       validate_address_belonging,
                                       validate_date, validate_delivery,
                                       validate_id, validate_isDelivery_check,
                                       validate_order_items,
                                       validate_order_stock, validate_price,
                                       validate_status,
                                       validate_status_transition)

orders_bp = Blueprint("orders_bp", __name__)

@orders_bp.route("/pedidos")
def orders():
	columns, rows, page, total_pages, search = get_orders()

	available_clients = getAvailableClients()
	available_baskets = getAvailableBaskets()
	statuses = getAvailableStatus()
	available_addresses = getAvailableAddresses()

	return render_template("orders/orders.html",
						columns=columns,
						rows=rows,
						page=page,
						total_pages=total_pages,
						search=search,
						user="Vendedor",
						available_clients=available_clients,
						available_baskets=available_baskets,
						statuses=statuses,
						available_addresses=available_addresses,
						today=get_today())

@orders_bp.route('/pedidos/basket_comp/<int:id>')
def basket_composition(id):
	return jsonify(get_basket_composition(id))

@orders_bp.route("/pedidos/search")
def orders_search():
	columns, rows, _, _, _ = get_orders()

	return render_template("orders/_orders_table_rows.html",
							columns=columns,
							rows=rows)

@orders_bp.route("/novo_pedido", methods=["POST"])
def new_order():
	try:
		items_payload = json.loads(request.form["items"])
	except (KeyError, json.JSONDecodeError):
		return "Itens do pedido inválidos"

	try:
		delivery_details = json.loads(request.form["deliveryDetails"])
	except (KeyError, json.JSONDecodeError):
		return "Detalhes de entrega inválidos", 400

	try:
		client = request.form["client"]
		if not validate_id(Table.Clients, "id_cliente", client):
			return "Cliente inválido", 400
		date = validate_date(request.form["date"])
		deliveryDate = validate_date(request.form["deliveryDate"], date, False)
		orderPrice = validate_price(request.form["orderPrice"])	
		status = validate_status(orderStatus.PENDING.name)
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
				
		obs = request.form.get('obs', '')
		items = json.dumps(items_payload)

		with run_transaction() as cursor:
			validate_order_stock(cursor, items_payload)

			if is_delivery and address_id is None:
				cursor.execute("""
				INSERT INTO IGOR_CG_ENDERECOS_CLIENTES
				(id_cliente, endereco)
				OUTPUT INSERTED.id_endereco
				VALUES (?, ?)
				""", (client, address_txt))

				address_id = cursor.fetchone()[0]

			
			cursor.execute("""
			INSERT INTO IGOR_CG_PEDIDOS
			(id_cliente, data_pedido, data_entrega,
			status_pedido, valor_pedido, observacao,
			itens_pedido, isDelivery, id_endereco, taxa_entrega)
			OUTPUT INSERTED.id_pedido
			VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
			""", (client, date, deliveryDate, status, orderPrice, obs, items, is_delivery, address_id, delivery_fee))

			order_id = cursor.fetchone()[0]
		
			for item in items_payload:
				cursor.execute("""
				INSERT INTO IGOR_CG_CESTAS_PEDIDO
				(id_produto, id_pedido, quantidade)
				VALUES (?, ?, ?)
				""", (item['basket_id'], order_id, item['quantity']))
		
	except ValueError as e:
		return str(e), 400

	return redirect(request.referrer or url_for("orders_bp.orders"))

@orders_bp.route("/pedidos/<int:id>/data")
def order_data(id):
	columns, rows = run_select("""
	SELECT
	p.id_pedido, p.id_cliente, c.nome_razao,
	p.data_pedido, p.data_entrega, p.status_pedido,
	p.valor_pedido, p.observacao, p.itens_pedido,
	p.isDelivery, p.id_endereco, p.taxa_entrega, p.valor_total
	FROM IGOR_CG_PEDIDOS p
	JOIN IGOR_CG_CLIENTES c
	ON p.id_cliente = c.id_cliente
	WHERE p.id_pedido = ? AND p.isDeleted = 0
	""", (id,))

	if not rows:
		return jsonify({"error": "Item not found"}), 404

	row = rows[0]
	order = dict(zip(columns, row))

	if order["data_pedido"]:
		order["data_pedido"] = order["data_pedido"].strftime("%Y-%m-%d")
	if order["data_entrega"]:
			order["data_entrega"] = order["data_entrega"].strftime("%Y-%m-%d")

	order["itens_pedido"] = json.loads(order["itens_pedido"])

	_, basket_rows = run_select("""
	SELECT
	id_produto, nome_cesta, preco_venda
	FROM IGOR_CG_PRODUTOS
	WHERE isDeleted = 0
	""")

	basket_lookup = {
		row[0]: {
			"name": row[1],
			"price": row[2]
		}
		for row in basket_rows
	}

	for item in order["itens_pedido"]:
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


	order["allowed_status"] = list(get_allowed_status(order["status_pedido"]))
	return jsonify(order)

@orders_bp.route("/pedidos/update", methods=["POST"])
def update_order():
	try:
		id = request.form["id"]
		if not validate_id(Table.Orders, "id_pedido", id):
			raise ValueError("Pedido inválido")
		status = validate_status(request.form["status"])
	except (KeyError, ValueError) as e:
			if isinstance(e, KeyError):
				return "Dados do pedido inválidos", 400
			return str(e), 400

	_, data_rows = run_select("""
	SELECT
	id_cliente, data_pedido, data_entrega, status_pedido,
	valor_pedido, observacao, itens_pedido,
	isDelivery, endereco, taxa_entrega
	FROM IGOR_CG_PEDIDOS
	WHERE id_pedido = ?
	AND isDeleted = 0
	""", (id,))

	if not data_rows:
		return "Pedido não encontrado.", 404

	current_client = data_rows[0][0]
	current_date = data_rows[0][1]
	current_deliveryDate = data_rows[0][2]
	current_status = data_rows[0][3]
	current_orderPrice = data_rows[0][4]
	current_obs = data_rows[0][5]
	current_items = data_rows[0][6]
	current_is_delivery = data_rows[0][7]
	current_address = data_rows[0][8]
	current_fee = data_rows[0][9]

	try:
		validate_status_transition(current_status, status)
		deliveryDate = current_deliveryDate
		if current_status in OPEN_ORDER_STATUS:
			deliveryDate = validate_date(request.form["deliveryDate"], current_date, False)
	except ValueError as e:
		return str(e), 400
	
	if current_status == orderStatus.PENDING.name:
		try:
			client = request.form["client"]
			if not validate_id(Table.Clients, "id_cliente", client):
				raise ValueError("Cliente inválido")
			date = validate_date(request.form["date"])
			orderPrice = validate_price(request.form["orderPrice"])
			items_payload = json.loads(request.form["items"])
			items_payload = validate_order_items(items_payload)
			is_delivery, address, fee = validate_delivery(request.form)
		except (KeyError, json.JSONDecodeError):
			return "Itens do pedido inválidos 2", 400
		except ValueError as e:
			return str(e), 400

		obs = request.form.get('obs', '')
		items = json.dumps(items_payload)
	

	else:
		client = current_client
		date = current_date
		orderPrice = current_orderPrice
		obs = current_obs
		items = current_items
		is_delivery = current_is_delivery
		address = current_address
		fee = current_fee

		try:
			items_payload = json.loads(current_items)
		except (TypeError, json.JSONDecodeError):
			return "Itens do pedido inválidos 3", 400

	try:
		with run_transaction() as cursor:
			cursor.execute("""
			UPDATE IGOR_CG_PEDIDOS
			SET
			id_cliente = ?,
			data_pedido = ?,
			data_entrega = ?,
			status_pedido = ?,
			valor_pedido = ?,
			observacao = ?,
			itens_pedido = ?,
			isDelivery = ?,
			endereco = ?,
			taxa_entrega = ?
			WHERE id_pedido = ?
			""", (client, date, deliveryDate, status, orderPrice, obs, items, is_delivery, address, fee, id))

			cursor.execute("""
			DELETE FROM IGOR_CG_CESTAS_PEDIDO
			WHERE id_pedido = ?
			""", (id,))

			for item in items_payload:
				cursor.execute("""
				INSERT INTO IGOR_CG_CESTAS_PEDIDO
				(id_produto, id_pedido, quantidade)
				VALUES (?, ?, ?)
				""", (item['basket_id'], id, item['quantity']))

			if status == "CONFIRMED" and current_status == "PENDING":
					update_order_stock(cursor, items_payload, "deduct", id)

			if status == "CANCELLED" and current_status not in {"PENDING", "CANCELLED"}:
					update_order_stock(cursor, items_payload, "increase", id)

	except ValueError as e:
		return str(e), 400

	return redirect(url_for("orders_bp.orders"))