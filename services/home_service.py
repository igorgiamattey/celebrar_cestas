from db import run_select, run_transaction
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