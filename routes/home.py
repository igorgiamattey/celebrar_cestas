from datetime import date, timedelta

from flask import Blueprint, jsonify, render_template, request, session

from db import format_date, run_select
from enums.order_status import orderStatus
from services.home_service import (getBalance, getCloseOrders, getLateOrders,
                                   getMissingItems, getNoDeliveryOrders)
from services.routes_service import (getAvailableAddresses,
                                     getAvailableBaskets, getAvailableClients,
                                     getAvailableCouriers, getAvailableDates,
                                     getAvailableDeliveryStatus,
                                     getAvailableGroups, getAvailableItems,
                                     getAvailableOrders,
                                     getAvailableOrderStatus)

home_bp = Blueprint("home_bp", __name__)

@home_bp.route("/home")
def home(): 
	page = request.args.get("page", 1, type=int)
	page = max(page, 1)
	per_page = 3
	
	where_clause = """
		WHERE o.isDeleted = 0
		AND o.order_status NOT IN ('DELIVERED', 'CANCELLED')
	"""

	_, count_rows = run_select(f"""
	SELECT COUNT(*)
	FROM CELEBRAR_ORDERS o
	JOIN CELEBRAR_CLIENTS c
	ON o.client_id = c.client_id
	{where_clause}
	""",)

	total_items = count_rows[0][0]
	total_pages = max((total_items + per_page - 1)//per_page, 1)
	page = min(page, total_pages)
	offset = (page - 1) * per_page

	order_columns, order_rows = run_select(f"""
	SELECT
	o.order_id AS ID,
	c.client_name AS Cliente,
	COALESCE(items.summary, '') AS Itens,
	o.delivery_date AS Entrega,
	o.order_total AS Valor,
	o.order_status AS Status
	FROM CELEBRAR_ORDERS o
	JOIN CELEBRAR_CLIENTS c
	ON o.client_id = c.client_id
	OUTER APPLY (
		SELECT
		STUFF ((
			SELECT
			CHAR (10) + CAST(oi.amount AS VARCHAR) + ' ' + CHAR(215) + ' ' + b.basket_name
			FROM CELEBRAR_ORDER_ITEMS oi
			JOIN CELEBRAR_BASKETS b
			ON b.basket_id = oi.basket_id
			WHERE oi.order_id = o.order_id
			FOR XML PATH(''), TYPE
		).value('.', 'NVARCHAR(MAX)'), 1, 1, '')
		AS summary
	) items
	{where_clause}
	ORDER BY o.delivery_date, o.order_id
	OFFSET ? ROWS
	FETCH NEXT ? ROWS ONLY
	""", (offset, per_page))

	order_columns = [
		order_columns[3],
		order_columns[2],
		order_columns[5]
	]

	today = date.today()
	limit_date = today + timedelta(days=5)

	order_rows = [
		{
			"id": row[0],
			"delivery": format_date(row[3]),
			"items": row[2],
			"status": orderStatus[row[5]].value,
			"warning": row[3] is not None and today <= row[3] <= limit_date and orderStatus[row[5]].name not in ("DELIVERED", "CANCELLED"),
			"late": row[3] is not None and today > row[3] and orderStatus[row[5]].name not in ("DELIVERED", "CANCELLED")
		}
		for row in order_rows
	]

	finances = getBalance()

	available_items = getAvailableItems()
	available_groups = getAvailableGroups()
	available_clients = getAvailableClients()
	available_baskets = getAvailableBaskets()
	order_statuses = getAvailableOrderStatus()

	missing_items = getMissingItems()
	close_orders = getCloseOrders()
	late_orders = getLateOrders()
	no_delivery_orders = getNoDeliveryOrders()
	available_addresses = getAvailableAddresses()
	available_couriers = getAvailableCouriers()

	available_dates = getAvailableDates()
	available_orders = getAvailableOrders()
	delivery_statuses = getAvailableDeliveryStatus()

	return render_template("home/home.html",
						order_rows=order_rows,
						order_columns=order_columns,
						page=page,
						total_pages=total_pages,
						finances=finances,
						user=session.get("username"),
						available_items=available_items,
						available_groups=available_groups,
						available_clients=available_clients,
						available_baskets=available_baskets,
						no_delivery_orders=no_delivery_orders,
						available_addresses=available_addresses,
						available_couriers=available_couriers,
						available_dates=available_dates,
						available_orders=available_orders,
						order_statuses=order_statuses,
						delivery_statuses=delivery_statuses,
						missing_items=missing_items,
						close_orders=close_orders,
						late_orders=late_orders)

@home_bp.route("/home_order_items/<int:id>")
def order_items(id):
	_, rows = run_select(f"""
	SELECT
	oi.amount, b.basket_name
	FROM CELEBRAR_ORDER_ITEMS oi
	JOIN CELEBRAR_BASKETS b
	ON b.basket_id = oi.basket_id
	WHERE oi.order_id = ?
	AND b.isDeleted = 0
	ORDER BY b.basket_name
	""", (id,))

	items = [
		{
			"quantity": row[0],
			"name": row[1]
		}
		for row in rows
	]

	return jsonify({"items": items})