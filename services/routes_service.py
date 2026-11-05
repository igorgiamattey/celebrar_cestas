from db import format_date, run_select
from enums.delivery_status import DeliveryStatus
from enums.financial_status import FinancialStatus
from enums.movement_types import (CAT_BY_TYPE, FinancialMovementCategories,
                                  FinancialMovementTypes, StorageMovementTypes)
from enums.order_status import OrderStatus
from enums.unit_measurement import Unit


def get_available_groups():
	_, rows = run_select("""
	SELECT
	group_id,
	group_name
	FROM CELEBRAR_GROUPS
	WHERE isDeleted = 0
	ORDER BY group_name
	""")

	available_groups = [
		{
			"id": row[0],
			"title": row[1],
			"name": row[1]
		}
		for row in rows
	]

	return available_groups

def get_available_items():
	_, rows = run_select("""
	SELECT
	item_id,
	item_name,
	item_unit
	FROM CELEBRAR_STORAGE
	WHERE isDeleted = 0
	ORDER BY item_name
	""")

	available_items = [
		{
			"id": row[0],
			"name": row[1],
			"unit": row[2],
			"title": f"{row[1]} ({row[2].lower()})"
		}
		for row in rows
	]

	return available_items

def get_available_clients():
	_, rows = run_select("""
	SELECT
	client_id, client_name
	FROM CELEBRAR_CLIENTS
	WHERE isDeleted = 0
	ORDER BY client_name
	""")

	available_clients = [
		{
			"id": row[0],
			"name": row[1]
		}
		for row in rows
	]

	return available_clients

def get_available_couriers():
	_, rows = run_select("""
	SELECT
	courier_id, courier_name, courier_phone
	FROM CELEBRAR_COURIERS
	WHERE isDeleted = 0
	ORDER BY courier_name
	""")

	available_couriers = [
		{
			"id": row[0],
			"name": row[1],
			"phone": row[2]
		}
		for row in rows
	]

	return available_couriers

def get_available_baskets():
	_, rows = run_select("""
	SELECT
	basket_id, basket_name, basket_price
	FROM CELEBRAR_BASKETS
	WHERE isDeleted = 0
	ORDER BY basket_name
	""")

	available_baskets = [
		{
			"id": row[0],
			"name": row[1],
			"price": row[2]
		}
		for row in rows
	]

	return available_baskets

def get_available_status_order():
	statuses = [
		{
			"id": status.name,
			"title": status.value.replace("_", " ").title()
		}
		for status in OrderStatus
	]

	return statuses

def get_available_status_delivery():
	statuses = [
		{
			"id": status.name,
			"title": status.value.replace("_", " ").title()
		}
		for status in DeliveryStatus
	]

	return statuses

def get_available_units():
	units = [
		{
			"id": units.name,
			"title": units.value.replace("_", " ")
		}
		for units in Unit
	]

	return units

def get_available_storage_moves():
	moves = [
		{
			"id": move.name,
			"title": move.value.replace("_", " ")
		}
		for move in StorageMovementTypes
	]

	return moves

def get_available_addresses():
	_, rows = run_select("""
	SELECT
	address_id, client_id, address_txt
	FROM CELEBRAR_ADDRESSES
	WHERE isDeleted = 0
	ORDER BY address_txt, address_id
	""")

	available_addresses = [
		{
			"id": row[0],
			"client_id": row[1],
			"address_txt": row[2]
		}
		for row in rows
	]

	return available_addresses

def get_available_dates(delivery_id=None):
	status = OrderStatus.READY.name

	_, rows = run_select("""
	SELECT DISTINCT
	delivery_date
	FROM CELEBRAR_ORDERS
	WHERE isDeleted = 0
	AND isDelivery = 1
	AND (delivery_id IS NULL OR delivery_id = ?)
	AND delivery_date IS NOT NULL
	AND order_status = ?
	ORDER BY delivery_date
	""", (delivery_id, status))

	available_dates = [
		{
			"id": row[0].isoformat(),
			"date": format_date(row[0])
		}
		for row in rows
	]

	return available_dates

def get_available_orders(delivery_id=None):
	status = OrderStatus.READY.name

	_, rows = run_select("""
	SELECT  
	o.order_id,
	c.client_name,
	a.address_txt,
	o.delivery_date
	FROM CELEBRAR_ORDERS o
	JOIN CELEBRAR_CLIENTS c
	ON o.client_id = c.client_id
	JOIN CELEBRAR_ADDRESSES a
	ON o.address_id = a.address_id
	WHERE o.isDeleted = 0
	AND o.isDelivery = 1
	AND (o.delivery_id IS NULL OR o.delivery_id = ?)
	AND o.order_status = ?
	AND a.isDeleted = 0
	ORDER BY o.delivery_date, o.order_id;
	""", (delivery_id, status))

	available_orders = [
		{
			"id": row[0],
			"title": (f"Pedido #{row[0]} | {row[1] or '---'} | {row[2] or '---'}"),
			"date": row[3].isoformat() if row[3] is not None else None
		}
		for row in rows
	]

	return available_orders

def get_available_orders_financial(payment_id=None):
	_, rows = run_select("""
	SELECT  
	o.order_id,
	c.client_name,
	o.delivery_date,
	o.order_total,
	o.order_status
	FROM CELEBRAR_ORDERS o
	JOIN CELEBRAR_CLIENTS c
	ON o.client_id = c.client_id
	LEFT JOIN CELEBRAR_ADDRESSES a
	ON o.address_id = a.address_id
	WHERE o.isDeleted = 0
	AND o.order_status <> ?
	AND NOT EXISTS (
		SELECT 1
		FROM CELEBRAR_FINANCIAL_PAYMENTS f
		WHERE f.order_id = o.order_id
		AND f.payment_id <> ?
		AND f.payment_status IN (?, ?))
	ORDER BY o.order_id;
	""", (OrderStatus.CANCELLED.name, payment_id, FinancialStatus.PENDING.name, FinancialStatus.PAID.name))

	available_orders = [
		{
			"id": row[0],
			"title": " | ".join([
				f"Pedido #{row[0]}",
				row[1] or '---',
				format_date(row[2]),
				OrderStatus[row[4]].value,
			]),
			"price": str(row[3]) if row[3] is not None else ""
		}
		for row in rows
	]

	return available_orders

def get_available_status_financial():
	statuses = [
		{
			"id": status.name,
			"title": status.value.replace("_", " ").title()
		}
		for status in FinancialStatus
	]

	return statuses

def get_available_financial_types():
	types = [
		{
			"id": type.name,
			"title": type.value.replace("_", " ").title()
		}
		for type in FinancialMovementTypes
	]

	return types

def get_available_financial_categories():
	categories = {
		fin_type: [{"id": c.name, "title": c.value.replace("_", " ").title()} for c in cats if c != FinancialMovementCategories.REFUND]
		for fin_type, cats in CAT_BY_TYPE.items()
	}

	return categories

def get_available_months():
	month_name = {
		1: "Janeiro", 2: "Fevereiro", 3: "Março",
		4: "Abril", 5: "Maio", 6: "Junho",
		7: "Julho", 8: "Agosto", 9: "Setembro",
		10: "Outubro", 11: "Novembro", 12: "Dezembro"
	}

	_, rows = run_select("""
	SELECT
	YEAR(payment_date) AS Ano,
	MONTH(payment_date) AS [Mês]
	FROM CELEBRAR_FINANCIAL_PAYMENTS
	WHERE isDeleted = 0
	AND payment_date IS NOT NULL
	GROUP BY YEAR(payment_date), MONTH(payment_date)
	ORDER BY Ano, [Mês]
	""")

	months = [
		{
			"id": row[0] * 100 + row[1],
			"title": f"{month_name[row[1]]}/{row[0]}"
		}
		for row in rows
	]

	return months

def count_rows(table, where_clause="", params=()):
	_, rows = run_select(f"""
	SELECT COUNT(*)
	FROM {table.value}
	{where_clause}
	""", params)

	return rows[0][0]