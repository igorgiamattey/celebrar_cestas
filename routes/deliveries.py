import json
from datetime import date

from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, session, url_for)

from db import run_select, run_transaction
from enums.delivery_status import OPEN_DELIVERY_STATUS, deliveryStatus
from enums.order_status import orderStatus
from enums.table_names import Table
from services.deliveries_service import courier_exists, get_deliveries
from services.errors import StaleDataError
from services.routes_service import (getAvailableAddresses,
                                     getAvailableCouriers, getAvailableDates,
                                     getAvailableDeliveryStatus,
                                     getAvailableOrders)
from services.status_transitions import get_allowed_status
from services.validate_service import (courier_has_open_deliveries,
                                       validate_date_id,
                                       validate_delivery_orders,
                                       validate_delivery_status, validate_id,
                                       validate_name, validate_phone,
                                       validate_status_transition)

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
						user=session.get("username"),
						available_couriers=available_couriers,
						available_dates=available_dates,
						available_orders=available_orders,
						delivery_statuses=statuses,
						available_addresses=available_addresses)

@deliveries_bp.route("/search_delivery")
def deliveries_search():
	columns, rows, _, _, search = get_deliveries()

	return render_template("deliveries/_deliveries_table_rows.html",
							columns=columns,
							rows=rows,
							search=search)

@deliveries_bp.route("/new_delivery", methods=["POST"])
def new_delivery():
	try:
		orders = json.loads(request.form.get("items", ""))
	except json.JSONDecodeError:
		return "Pedidos da entrega inválidos", 400

	try:
		courier = request.form.get("courier", type=int) or None
		if courier is not None and not validate_id(Table.Couriers, "courier_id", courier):
			return "Entregador inválido", 400
		date_id = request.form["date"]
		if not validate_date_id(date_id):
			return "Data inválida", 400
		delivery_date = date.fromisoformat(date_id)
		status = deliveryStatus.PENDING.name
		orders = validate_delivery_orders(orders, delivery_date)
		
		with run_transaction() as cursor:			
			cursor.execute("""
			INSERT INTO CELEBRAR_DELIVERIES
			(courier_id, delivery_date, delivery_status)
			OUTPUT INSERTED.delivery_id
			VALUES (?, ?, ?)
			""", (courier, delivery_date, status))

			delivery_id = cursor.fetchone()[0]

			for order in orders:
				cursor.execute("""
				UPDATE CELEBRAR_ORDERS
				SET delivery_id = ?
				WHERE order_id = ?
				AND isDeleted = 0
				AND isDelivery = 1
				AND delivery_id IS NULL
				AND order_status = ?
				AND delivery_date = ?
				""", (delivery_id, order, orderStatus.READY.name, delivery_date))

				if cursor.rowcount != 1:
					raise StaleDataError("Um ou mais pedidos não estão mais disponíveis para entrega")
		
	except KeyError:
		return "Dados da entrega inválidos", 400
	except StaleDataError as e:
		return str(e), 409
	except ValueError as e:
		return str(e), 400

	return redirect(request.referrer or url_for("deliveries_bp.deliveries"))

@deliveries_bp.route("/delivery_data/<int:id>")
def delivery_data(id):
	columns, rows = run_select("""
	SELECT
	d.delivery_id, d.courier_id, c.courier_name,
	d.delivery_date, d.delivery_status
	FROM CELEBRAR_DELIVERIES d
	LEFT JOIN CELEBRAR_COURIERS c
	ON d.courier_id = c.courier_id
	WHERE d.delivery_id = ? AND d.isDeleted = 0
	""", (id,))

	if not rows:
		return jsonify({"error": "Delivery not found"}), 404

	row = rows[0]
	delivery = dict(zip(columns, row))

	if delivery["delivery_date"]:
		delivery["delivery_date"] = delivery["delivery_date"].strftime("%Y-%m-%d")

	_, order_rows = run_select("""
	SELECT
	o.order_id, c.client_name, a.address_txt
	FROM CELEBRAR_ORDERS o
	LEFT JOIN CELEBRAR_CLIENTS c
	ON o.client_id = c.client_id
	LEFT JOIN CELEBRAR_ADDRESSES a
	ON o.address_id = a.address_id
	WHERE o.delivery_id = ?
	AND o.isDeleted = 0
	ORDER BY o.order_id
	""", (id,))

	delivery["orders"] = [
		{"id": o_row[0], "title": f"Pedido #{o_row[0]} | {o_row[1] or '---'} | {o_row[2] or '---'}"}
		for o_row in order_rows
	]
	
	delivery["allowed_status"] = sorted(get_allowed_status(delivery["delivery_status"], delivery_mode))

	delivery["available_orders"] = getAvailableOrders(id)
	delivery["available_dates"] = getAvailableDates(id)

	return jsonify(delivery)

@deliveries_bp.route("/update_delivery", methods=["POST"])
def update_delivery():
	try:
		id = request.form["id"]
		if not validate_id(Table.Deliveries, "delivery_id", id):
			raise ValueError("Entrega inválida")
		status = validate_delivery_status(request.form["status"])
		courier = None
		if request.form.get("courier"):
			courier = request.form.get("courier", type=int) or None
			if courier is None or not validate_id(Table.Couriers, "courier_id", courier):
				return "Entregador inválido", 400

		if courier is None and status in (deliveryStatus.TRANSIT.name, deliveryStatus.DELIVERED.name):
			return "Informe o entregador antes de iniciar a entrega.", 400
	except KeyError:
		return "Dados da entrega inválidos", 400
	except ValueError as e:
		return str(e), 400

	_, data_rows = run_select("""
	SELECT
	delivery_date, delivery_status
	FROM CELEBRAR_DELIVERIES
	WHERE delivery_id = ?
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

	notices = []
	
	try:
		with run_transaction() as cursor:
			cursor.execute("""
			UPDATE CELEBRAR_DELIVERIES
			SET
			courier_id = ?,
			delivery_date = ?,
			delivery_status = ?
			WHERE delivery_id = ?
			AND isDeleted = 0
			AND delivery_status = ?
			""", (courier, delivery_date, status, id, current_status))

			if cursor.rowcount != 1:
				raise StaleDataError("A entrega já foi alterada. Recarregue a página.")

			if status == deliveryStatus.CANCELLED.name:
				cursor.execute(f"""
				UPDATE CELEBRAR_ORDERS
				SET delivery_id = NULL
				WHERE delivery_id = ?
				""", (id,))

				if cursor.rowcount > 0:
					notices.append(f"{cursor.rowcount} {'pedido removido' if cursor.rowcount == 1 else 'pedidos removidos'} da entrega")

			elif status == deliveryStatus.DELIVERED.name:
				cursor.execute(f"""
				UPDATE CELEBRAR_ORDERS
				SET order_status = ?
				WHERE delivery_id = ?
				AND isDeleted = 0
				AND order_status = ?
				""", (orderStatus.DELIVERED.name, id, orderStatus.READY.name))

				if cursor.rowcount > 0:
					notices.append(f"{cursor.rowcount} {'pedido marcado como entregue' if cursor.rowcount == 1 else 'pedidos marcados como entregues'}")
				
			elif current_status == deliveryStatus.PENDING.name:
				placeholders = ", ".join("?" * len(orders))

				cursor.execute(f"""
				UPDATE CELEBRAR_ORDERS
				SET delivery_id = NULL
				WHERE delivery_id = ?
				AND order_id NOT IN ({placeholders})
				""", (id, *orders))

				for order in orders:
					cursor.execute("""
					UPDATE CELEBRAR_ORDERS
					SET delivery_id = ?
					WHERE order_id = ?
					AND isDeleted = 0
					AND isDelivery = 1
					AND order_status = ?
					AND delivery_date = ?
					AND (delivery_id is NULL OR delivery_id = ?)
					""", (id, order, orderStatus.READY.name, delivery_date, id))

					if cursor.rowcount != 1:
						raise StaleDataError("Um ou mais pedidos não estão mais disponíveis para entrega")

	except StaleDataError as e:
		return str(e), 409
	except ValueError as e:
		return str(e), 400

	flash(f"Entrega #{id} atualizada com sucesso!", "success")
	for notice in notices:
		flash(notice, "info")

	return "", 204

@deliveries_bp.route("/save_courier", methods=["POST"])
def save_courier():
	try:
		courier_id = request.form.get("courier_id")
		if courier_id:
			if not validate_id(Table.Couriers, "courier_id", courier_id):
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
			UPDATE CELEBRAR_COURIERS
			SET
			courier_name = ?,
			courier_phone = ?
			WHERE courier_id = ?
			""", (name, phone, courier_id))

		else:
			cursor.execute("""
			INSERT INTO CELEBRAR_COURIERS
			(courier_name, courier_phone)
			VALUES (?, ?)
			""", (name, phone))

	return redirect(url_for("deliveries_bp.deliveries"))

@deliveries_bp.route("/delete_courier/<int:id>", methods=["POST"])
def delete_courier(id):
	try:
		if not validate_id(Table.Couriers, "courier_id", id):
			raise ValueError("Entregador inválido")
		if courier_has_open_deliveries(id):
			raise ValueError("Esse entregador tem uma entrega em aberto")
	except ValueError as e:
		return str(e), 400
	
	with run_transaction() as cursor:
		cursor.execute("""
		UPDATE CELEBRAR_COURIERS
		SET
		isDeleted = 1
		WHERE courier_id = ?
		""", (id,))

	return "", 204

@deliveries_bp.route("/courier_data/<int:id>")
def courier_data(id):
	_, rows = run_select("""
	SELECT courier_name, courier_phone
	FROM CELEBRAR_COURIERS
	WHERE courier_id = ?
	AND isDeleted = 0
	""", (id,))

	if not rows:
		return jsonify({"error": "Courier not found"}), 404

	courier_name = rows[0][0]
	courier_phone = rows[0][1]

	return jsonify({"name": courier_name, "phone": courier_phone})