from db import run_select

def getMissingItems():
	_, rows = run_select(f"""
	SELECT
	COUNT(*)
	FROM IGOR_CG_ESTOQUE
	WHERE isDeleted = 0 AND qtd_estoque <= estoque_minimo
	""")

	return rows[0][0]

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