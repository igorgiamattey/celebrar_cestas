from db import format_date, run_select
from enums.delivery_status import deliveryStatus
from enums.financial_status import financialStatus
from enums.movement_types import (financialMovementCategories,
                                  financialMovementTypes, CAT_BY_TYPE)
from enums.order_status import orderStatus
from enums.unit_measurement import Unit


def getAvailableGroups():
	_, rows = run_select("""
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
	_, rows = run_select("""
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
	_, rows = run_select("""
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
	_, rows = run_select("""
	SELECT
	id_entregador, nome_entregador, telefone
	FROM IGOR_CG_ENTREGADORES
	WHERE isDeleted = 0
	ORDER BY nome_entregador
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
	_, rows = run_select("""
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

def getAvailableDates(delivery_id=None):
	status = orderStatus.READY.name

	_, rows = run_select("""
	SELECT DISTINCT
	data_entrega
	FROM IGOR_CG_PEDIDOS
	WHERE isDeleted = 0
	AND isDelivery = 1
	AND (id_entrega IS NULL OR id_entrega = ?)
	AND data_entrega IS NOT NULL
	AND status_pedido = ?
	ORDER BY data_entrega
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
	AND (p.id_entrega IS NULL OR p.id_entrega = ?)
	AND p.status_pedido = ?
	AND a.isDeleted = 0
	ORDER BY p.data_entrega, p.id_pedido;
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
	p.id_pedido,
	c.nome_razao,
	p.data_entrega,
	p.valor_total,
	p.status_pedido
	FROM IGOR_CG_PEDIDOS p
	JOIN IGOR_CG_CLIENTES c
	ON p.id_cliente = c.id_cliente
	LEFT JOIN IGOR_CG_ENDERECOS_CLIENTES a
	ON p.id_endereco = a.id_endereco
	WHERE p.isDeleted = 0
	AND p.status_pedido <> ?
	AND NOT EXISTS (
		SELECT 1
		FROM IGOR_CG_LANCAMENTOS_FIN f
		WHERE f.id_pedido = p.id_pedido
		AND f.status_pagamento IN (?, ?))
	ORDER BY p.id_pedido;
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

def countRows(table, where_clause="", params=()):
	_, rows = run_select(f"""
	SELECT COUNT(*)
	FROM {table.value}
	{where_clause}
	""", params)

	return rows[0][0]