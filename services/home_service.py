from datetime import date

from db import format_currency, run_select, run_transaction
from enums.financial_status import financialStatus
from enums.movement_types import financialMovementTypes
from enums.order_status import orderStatus, CLOSED_ORDER_STATUS
from services.order_service import get_available_stock


def getMissingItems():
	with run_transaction() as cursor:
		available_stock = get_available_stock(cursor)

		cursor.execute("""
		SELECT
		item_id, item_min
		FROM CELEBRAR_STORAGE
		WHERE isDeleted = 0
		""")

		rows = cursor.fetchall()
	
	return sum(1 for item_id, min_stock in rows if available_stock.get(item_id, 0) <= min_stock)

def getCloseOrders():
	placeholders = ",".join("?" * len(CLOSED_ORDER_STATUS))
	
	_, rows = run_select(f"""
	SELECT COUNT(*)
	FROM CELEBRAR_ORDERS o
	JOIN CELEBRAR_CLIENTS c
	ON o.client_id = c.client_id
	WHERE o.isDeleted = 0
	AND o.delivery_date BETWEEN CAST(GETDATE() AS DATE)
		AND DATEADD(DAY, 5, CAST(GETDATE() AS DATE))
	AND o.order_status NOT IN ({placeholders})
	""", CLOSED_ORDER_STATUS)

	return rows[0][0]

def getLateOrders():
	placeholders = ",".join("?" * len(CLOSED_ORDER_STATUS))

	_, rows = run_select(f"""
	SELECT COUNT(*)
	FROM CELEBRAR_ORDERS o
	JOIN CELEBRAR_CLIENTS c
	ON o.client_id = c.client_id
	WHERE o.isDeleted = 0
	AND o.delivery_date < CAST(GETDATE() AS DATE)
	AND o.order_status NOT IN ({placeholders})
	""", CLOSED_ORDER_STATUS)

	return rows[0][0]

def getNoDeliveryOrders():
	status = orderStatus.READY.name

	_, rows = run_select(f"""
	SELECT COUNT(*)
	FROM CELEBRAR_ORDERS
	WHERE isDeleted = 0
	AND isDelivery = 1
	AND delivery_id is NULL
	AND order_status = ?
	""", (status))

	return rows[0][0]

def getBalance():
	balance = {}
	IN = financialMovementTypes.INCOME.name
	OUT = financialMovementTypes.EXPENSE.name
	PAID = financialStatus.PAID.name
	PENDING = financialStatus.PENDING.name

	start = date.today().replace(day=1)
	end = (
		start.replace(year=start.year + 1, month=1) if start.month == 12
		else start.replace(month=start.month+1)
	)
	
	_, rows = run_select("""
	SELECT payment_type,
		SUM(CASE WHEN payment_status = ? THEN payment_value ELSE 0 END) AS pending,
		SUM(CASE WHEN payment_status = ?
			AND payment_date >= ?
			AND payment_date < ?
			THEN payment_value ELSE 0 END) AS paid_month
	FROM CELEBRAR_FINANCIAL_PAYMENTS
	WHERE isDeleted = 0
	GROUP BY payment_type
	""", (PENDING, PAID, start, end))

	totals = {fin_type: ((pending or 0), (monthly or 0)) for fin_type, pending, monthly in rows}

	pending_income, month_income = totals.get(IN, (0, 0))
	pending_expense, month_expense = totals.get(OUT, (0, 0))
	
	balance["PENDING_INCOME"] = format_currency(pending_income)
	balance["PENDING_EXPENSE"] = format_currency(pending_expense)
	balance["MONTH_INCOME"] = format_currency(month_income)
	balance["MONTH_EXPENSE"] = format_currency(month_expense)
	balance["MONTH_TOTAL"] = format_currency(month_income-month_expense)

	return balance

