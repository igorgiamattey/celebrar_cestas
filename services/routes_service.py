from db import run_select, format_date
from enums.delivery_status import deliveryStatus
from enums.order_status import orderStatus
from enums.unit_measurement import Unit


def getAvailableGroups():
	_, rows = run_select(f"""
	SELECT
	id_grupo,
	nome_grupo
	FROM IGOR_CG_GRUPOS_ITEM
	WHERE isDeleted = 0
	ORDER BY nome_grupo
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
	_, rows = run_select(f"""
	SELECT
	id_insumo,
	nome_insumo,
	unidade_medida
	FROM IGOR_CG_ESTOQUE
	WHERE isDeleted = 0
	ORDER BY nome_insumo
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
	_, rows = run_select(f"""
	SELECT
	id_cliente, nome_razao
	FROM IGOR_CG_CLIENTES
	WHERE isDeleted = 0
	ORDER BY nome_razao
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
	_, rows = run_select(f"""
	SELECT
	id_entregador, nome_entregador
	FROM IGOR_CG_ENTREGADORES
	WHERE isDeleted = 0
	ORDER BY nome_entregador
	""")

	available_couriers = [
		{
			"id": row[0],
			"name": row[1]
		}
		for row in rows
	]

	return available_couriers

def getAvailableBaskets():
	_, rows = run_select(f"""
	SELECT
	id_produto, nome_cesta, preco_venda
	FROM IGOR_CG_PRODUTOS
	WHERE isDeleted = 0
	ORDER BY nome_cesta
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
	_, rows = run_select(f"""
	SELECT
	id_endereco, id_cliente, endereco
	FROM IGOR_CG_ENDERECOS_CLIENTES
	WHERE isDeleted = 0
	ORDER BY endereco, id_endereco
	""")

	available_addresses = [
		{
			"id": row[0],
			"id_cliente": row[1],
			"endereco": row[2]
		}
		for row in rows
	]

	return available_addresses

def getAvailableDates():
	status = orderStatus.READY.name

	_, rows = run_select(f"""
	SELECT DISTINCT
	data_entrega
	FROM IGOR_CG_PEDIDOS
	WHERE isDeleted = 0
	AND isDelivery = 1
	AND id_entrega IS NULL
	AND data_entrega IS NOT NULL
	AND status_pedido = ?
	ORDER BY data_entrega
	""", (status,))

	available_dates = [
		{
			"id": row[0],
			"date": format_date(row[0])
		}
		for row in rows
	]

	return available_dates

def getAvailableOrders():
	status = orderStatus.READY.name

	_, rows = run_select(f"""
	SELECT
	p.id_pedido,
	c.nome_razao,
	a.endereco,
	p.data_entrega
	FROM IGOR_CG_PEDIDOS p
	JOIN IGOR_CG_CLIENTES c
	ON p.id_cliente = c.id_cliente
	JOIN IGOR_CG_ENDERECOS_CLIENTES a
	ON p.id_endereco = a.id_endereco
	WHERE p.isDeleted = 0
	AND p.isDelivery = 1
	AND p.id_entrega IS NULL
	AND p.status_pedido = ?
	AND a.isDeleted = 0
	ORDER BY p.data_entrega, p.id_pedido;
	""", (status,))

	available_orders = [
		{
			"id": row[0],
			"title": (f"Pedido #{row[0]} | {row[1]} | {row[2]}"),
			"date": row[3]
		}
		for row in rows
	]

	return available_orders

def countRows(table, where_clause="", params=()):
	_, rows = run_select(f"""
	SELECT COUNT(*)
	FROM {table.value}
	{where_clause}
	""", params)

	return rows[0][0]