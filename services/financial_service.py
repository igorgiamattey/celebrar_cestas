from flask import request

from db import format_currency, format_date_year, run_select
from enums.financial_status import financialStatus
from enums.order_status import orderStatus
from enums.movement_types import (financialMovementCategories,
                                  financialMovementTypes)


def get_financial():
	page = request.args.get("page", 1, type=int)
	page = max(page, 1)
	search = request.args.get("search", "", type=str)
	per_page = 1000

	where_clause = "WHERE isDeleted = 0"
	params = []
	if search:
		search_param = f"%{search}%"
		conditions = [
			"CONVERT(VARCHAR(10), data_pagamento, 103) LIKE ?",
		]
		params.extend([search_param])

		matching_status = [s.name for s in financialStatus if search.lower() in s.value.lower()]
		matching_types = [t.name for t in financialMovementTypes if search.lower() in t.value.lower()]
		matching_categories = [c.name for c in financialMovementCategories if search.lower() in c.value.lower()]
		if matching_status:
			conditions.append(f"status_pagamento IN ({','.join('?' * len(matching_status))})")
			params.extend(matching_status)
		if matching_types:
			conditions.append(f"tipo IN ({','.join('?' * len(matching_types))})")
			params.extend(matching_types)
		if matching_categories:
			conditions.append(f"categoria IN ({','.join('?' * len(matching_categories))})")
			params.extend(matching_categories)

		where_clause += " AND (" + " OR ".join(conditions) + ")"

	_, count_rows = run_select(f"""
	SELECT COUNT(*)
	FROM IGOR_CG_LANCAMENTOS_FIN
	{where_clause}
	""", tuple(params))

	total_items = count_rows[0][0]
	total_pages = max((total_items + per_page - 1)//per_page, 1)
	page = min(page, total_pages)

	offset = (page - 1) * per_page

	columns, rows = run_select(f"""
	SELECT
	id_lancamento AS ID,
	tipo AS Tipo,
	data_pagamento AS Data,
	valor AS Valor,
	status_pagamento AS Status,
	categoria AS Categoria
	FROM IGOR_CG_LANCAMENTOS_FIN
	{where_clause}
	ORDER BY id_lancamento DESC
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
	SELECT valor_total
	FROM IGOR_CG_PEDIDOS
	WHERE id_pedido = ?
	AND isDeleted = 0
	AND status_pedido <> ?
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
	SELECT tipo, categoria, SUM(valor)
	FROM IGOR_CG_LANCAMENTOS_FIN
	WHERE status_pagamento = ?
	AND isDeleted = 0
	GROUP BY tipo, categoria
	""", (financialStatus.PAID.name,))

	totals = {(tipo, cat): total for tipo, cat, total in rows}

	income = sum((value for (tipo, _), value in totals.items() if tipo == IN))
	expense = sum((value for (tipo, _), value in totals.items() if tipo == OUT))
	
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

