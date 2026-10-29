from db import format_date, run_select
from enums.delivery_status import deliveryStatus
from enums.financial_status import financialStatus
from enums.movement_types import (CAT_BY_TYPE, financialMovementCategories,
                                  financialMovementTypes)
from enums.order_status import orderStatus
from enums.unit_measurement import Unit


def getAvailableGroups():
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

def getAvailableItems():
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

def getAvailableClients():
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

def getAvailableCouriers():
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

def getAvailableBaskets():
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

def getAvailableOrderStatus():
	statuses = [
		{
			"id": status.name,
			"title": status.value.replace("_", " ").title()
		}
		for status in orderStatus
	]

	return statuses

def getAvailableDeliveryStatus():
	statuses = [
		{
			"id": status.name,
			"title": status.value.replace("_", " ").title()
		}
		for status in deliveryStatus
	]

	return statuses

def getAvailableUnits():
	units = [
		{
			"id": units.name,
			"title": units.value.replace("_", " ")
		}
		for units in Unit
	]

	return units

def getAvailableAddresses():
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

def getAvailableDates(delivery_id=None):
	status = orderStatus.READY.name

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

def getAvailableOrders(delivery_id=None):
	status = orderStatus.READY.name

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

def getAvailableOrdersFinancial():
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
		AND f.payment_status IN (?, ?))
	ORDER BY o.order_id;
	""", (orderStatus.CANCELLED.name, financialStatus.PENDING.name, financialStatus.PAID.name))

	available_orders = [
		{
			"id": row[0],
			"title": " | ".join([
				f"Pedido #{row[0]}",
				row[1] or '---',
				format_date(row[2]),
				orderStatus[row[4]].value,
			]),
			"price": str(row[3]) if row[3] is not None else ""
		}
		for row in rows
	]

	return available_orders

def getAvailableFinancialStatus():
	statuses = [
		{
			"id": status.name,
			"title": status.value.replace("_", " ").title()
		}
		for status in financialStatus
	]

	return statuses

def getAvailableFinancialTypes():
	types = [
		{
			"id": type.name,
			"title": type.value.replace("_", " ").title()
		}
		for type in financialMovementTypes
	]

	return types

def getAvailableFinancialCategoriesByType():
	categories = {
		fin_type: [{"id": c.name, "title": c.value.replace("_", " ").title()} for c in cats if c != financialMovementCategories.REFUND]
		for fin_type, cats in CAT_BY_TYPE.items()
	}

	return categories

def getAvailableMonths():
	monthName = {
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
			"title": f"{monthName[row[1]]}/{row[0]}"
		}
		for row in rows
	]

	return months

def countRows(table, where_clause="", params=()):
	_, rows = run_select(f"""
	SELECT COUNT(*)
	FROM {table.value}
	{where_clause}
	""", params)

	return rows[0][0]