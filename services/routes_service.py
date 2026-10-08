from db import run_select
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

def getAvailableStatus():
	statuses = [
		{
			"id": status.name,
			"title": status.value.replace("_", " ").title()
		}
		for status in orderStatus
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

def countRows(table, where_clause="", params=()):
	_, rows = run_select(f"""
	SELECT COUNT(*)
	FROM {table.value}
	{where_clause}
	""", params)

	return rows[0][0]