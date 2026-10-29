from flask import request

from db import format_currency, format_date_year, run_select
from enums.financial_status import financialStatus
from enums.movement_types import (financialMovementCategories,
                                  financialMovementTypes)
from enums.order_status import orderStatus


def get_financial():
	page = request.args.get("page", 1, type=int)
	page = max(page, 1)
	search = request.args.get("search", "", type=str)
	month_filter = request.args.get("month", type=int)
	per_page = 1000

	where_clause = "WHERE isDeleted = 0"
	params = []
	if search:
		conditions = []
		
		matching_status = [s.name for s in financialStatus if search.lower() in s.value.lower()]
		matching_types = [t.name for t in financialMovementTypes if search.lower() in t.value.lower()]
		matching_categories = [c.name for c in financialMovementCategories if search.lower() in c.value.lower()]
		if matching_status:
			conditions.append(f"payment_status IN ({','.join('?' * len(matching_status))})")
			params.extend(matching_status)
		if matching_types:
			conditions.append(f"payment_type IN ({','.join('?' * len(matching_types))})")
			params.extend(matching_types)
		if matching_categories:
			conditions.append(f"payment_category IN ({','.join('?' * len(matching_categories))})")
			params.extend(matching_categories)

		where_clause += " AND (" + " OR ".join(conditions) + ")"

	if month_filter:
		year = month_filter//100
		month = month_filter%100
		where_clause += f" AND YEAR(payment_date) = ? AND MONTH(payment_date) = ?"
		params.extend([year, month])

	_, count_rows = run_select(f"""
	SELECT COUNT(*)
	FROM CELEBRAR_FINANCIAL_PAYMENTS
	{where_clause}
	""", tuple(params))

	total_items = count_rows[0][0]
	total_pages = max((total_items + per_page - 1)//per_page, 1)
	page = min(page, total_pages)

	offset = (page - 1) * per_page

	columns, rows = run_select(f"""
	SELECT
	payment_id AS ID,
	payment_type AS Tipo,
	payment_date AS Data,
	payment_value AS Valor,
	payment_status AS Status,
	payment_category AS Categoria
	FROM CELEBRAR_FINANCIAL_PAYMENTS
	{where_clause}
	ORDER BY payment_id DESC
	OFFSET ? ROWS
	FETCH NEXT ? ROWS ONLY
	""", (*params, offset, per_page))

	rows = [
		(
			row[0],
			financialMovementTypes[row[1]].value,
			format_date_year(row[2]),
			(format_currency(row[3])),
			financialStatus[row[4]].value,
			financialMovementCategories[row[5]].value
		)
		for row in rows
	]

	return columns, rows, page, total_pages, search

def get_order_total(order_id):
	_, rows = run_select("""
	SELECT order_total
	FROM CELEBRAR_ORDERS
	WHERE order_id = ?
	AND isDeleted = 0
	AND order_status <> ?
	""", (order_id, orderStatus.CANCELLED.name))

	if not rows:
		raise ValueError("Pedido inválido")

	return rows[0][0]

def get_balance():
	balance = {}
	IN = financialMovementTypes.INCOME.name
	OUT = financialMovementTypes.EXPENSE.name
	CAT = financialMovementCategories

	_, rows = run_select("""
	SELECT
	payment_type, payment_category, SUM(payment_value)
	FROM CELEBRAR_FINANCIAL_PAYMENTS
	WHERE payment_status = ?
	AND isDeleted = 0
	GROUP BY payment_type, payment_category
	""", (financialStatus.PAID.name,))

	totals = {(fin_type, fin_cat): total for fin_type, fin_cat, total in rows}

	income = sum((value for (fin_type, _), value in totals.items() if fin_type == IN))
	expense = sum((value for (fin_type, _), value in totals.items() if fin_type == OUT))
	
	balance["INCOME"] = format_currency(income)
	balance["EXPENSE"] = format_currency(expense)
	balance["TOTAL"] = format_currency(income - expense)

	balance["ORDERS"] = format_currency(totals.get((IN,  CAT.ORDER_PAYMENT.name), 0))
	balance["MARKET"] = format_currency(totals.get((OUT,  CAT.MARKET.name), 0))
	balance["OTHER_IN"] = format_currency(totals.get((IN,  CAT.OTHER.name), 0))
	balance["OTHER_OUT"] = format_currency(totals.get((OUT, CAT.OTHER.name), 0))
	balance["REFUND_IN"] = format_currency(totals.get((IN, CAT.REFUND.name), 0))
	balance["REFUND_OUT"] = format_currency(totals.get((OUT, CAT.REFUND.name), 0))

	return balance

def get_monthly_statement():
	monthName = {
		1: "Jan", 2: "Fev", 3: "Mar",
		4: "Abr", 5: "Mai", 6: "Jun",
		7: "Jul", 8: "Ago", 9: "Set",
		10: "Out", 11: "Nov", 12: "Dez"
	}

	IN = financialMovementTypes.INCOME.name
	OUT = financialMovementTypes.EXPENSE.name
	
	_, rows = run_select("""
	SELECT
	YEAR(payment_date) AS Ano,
	MONTH(payment_date) AS [Mês],
	SUM(CASE WHEN payment_type = ? THEN payment_value ELSE 0 END) AS Entrada,
	SUM(CASE WHEN payment_type = ? THEN payment_value ELSE 0 END) AS [Saída]
	FROM CELEBRAR_FINANCIAL_PAYMENTS
	WHERE isDeleted = 0
	AND payment_date IS NOT NULL
	GROUP BY YEAR(payment_date), MONTH(payment_date)
	ORDER BY Ano, [Mês]
	""", (IN, OUT))

	rows = [
		(
			f"{monthName[row[1]]}/{row[0]}",
			format_currency(row[2]),
			format_currency(row[3]),
			format_currency(row[2] - row[3])
		)
		for row in rows
	]

	return rows