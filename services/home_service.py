from datetime import date

from db import format_currency, run_select, run_transaction
from enums.financial_status import financialStatus
from enums.movement_types import financialMovementTypes
from enums.order_status import orderStatus
from services.order_service import get_available_stock


def getMissingItems():
	with run_transaction() as cursor:
		available_stock = get_available_stock(cursor)

		cursor.execute("""
		SELECT
		id_insumo, estoque_minimo
		FROM IGOR_CG_ESTOQUE
		WHERE isDeleted = 0
		""")

		rows = cursor.fetchall()
	
	return sum(1 for item_id, min_stock in rows if available_stock.get(item_id, 0) <= min_stock)

def getCloseOrders():
	_, rows = run_select(f"""
	SELECT COUNT(*)
	FROM IGOR_CG_PEDIDOS p
	JOIN IGOR_CG_CLIENTES c
	ON p.id_cliente = c.id_cliente
	WHERE p.isDeleted = 0
	AND p.data_entrega BETWEEN CAST(GETDATE() AS DATE)
		AND DATEADD(DAY, 5, CAST(GETDATE() AS DATE))
	AND p.status_pedido NOT IN ('DELIVERED', 'CANCELLED')
	""",)

	return rows[0][0]

def getLateOrders():
	_, rows = run_select(f"""
	SELECT COUNT(*)
	FROM IGOR_CG_PEDIDOS p
	JOIN IGOR_CG_CLIENTES c
	ON p.id_cliente = c.id_cliente
	WHERE p.isDeleted = 0
	AND p.data_entrega < CAST(GETDATE() AS DATE)
	AND p.status_pedido NOT IN ('DELIVERED', 'CANCELLED')
	""",)

	return rows[0][0]

def getNoDeliveryOrders():
	status = orderStatus.READY.name

	_, rows = run_select(f"""
	SELECT COUNT(*)
	FROM IGOR_CG_PEDIDOS
	WHERE isDeleted = 0
	AND isDelivery = 1
	AND id_entrega is NULL
	AND status_pedido = ?
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
	SELECT tipo,
		SUM(CASE WHEN status_pagamento = ? THEN valor ELSE 0 END) AS pending,
		SUM(CASE WHEN status_pagamento = ?
			AND data_pagamento >= ?
			AND data_pagamento < ?
			THEN valor ELSE 0 END) AS paid_month
	FROM IGOR_CG_LANCAMENTOS_FIN
	WHERE isDeleted = 0
	GROUP BY tipo
	""", (PENDING, PAID, start, end))

	totals = {tipo: ((pending or 0), (monthly or 0)) for tipo, pending, monthly in rows}

	pending_income, month_income = totals.get(IN, (0, 0))
	pending_expense, month_expense = totals.get(OUT, (0, 0))
	
	balance["PENDING_INCOME"] = format_currency(pending_income)
	balance["PENDING_EXPENSE"] = format_currency(pending_expense)
	balance["MONTH_INCOME"] = format_currency(month_income)
	balance["MONTH_EXPENSE"] = format_currency(month_expense)
	balance["MONTH_TOTAL"] = format_currency(month_income-month_expense)

	return balance

