from flask import request

from db import run_select, format_currency
from enums.table_names import Table
from services.routes_service import countRows

def item_exists(name, exclude_id=None):
	query = """
	SELECT 1
	FROM IGOR_CG_ESTOQUE
	WHERE nome_insumo = ?
	AND isDeleted = 0
	"""

	params = [name]

	if exclude_id is not None:
		query += " AND id_insumo <> ?"
		params.append(exclude_id)

	_, rows = run_select(query, tuple(params))

	return bool(rows)

def group_exists(name, exclude_id=None):
	query = """
	SELECT 1
	FROM IGOR_CG_GRUPOS_ITEM
	WHERE nome_grupo = ?
	AND isDeleted = 0
	"""

	params = [name]

	if exclude_id is not None:
		query += " AND id_grupo <> ?"
		params.append(exclude_id)

	_, rows = run_select(query, tuple(params))

	return bool(rows)

def get_storage():
	page = request.args.get("page", 1, type=int)
	page = max(1, page)
	search = request.args.get("search", "", type=str)
	per_page = 1000

	where_clause = "WHERE isDeleted = 0"
	params = []
	if search:
		where_clause += " AND nome_insumo LIKE ?"
		params.append(f"%{search}%")

	count = countRows(Table.Items, where_clause, tuple(params))
	total_pages = max((count + per_page - 1)//per_page, 1)
	page = min(page, total_pages)
	offset = (page - 1) * per_page

	columns, rows = run_select(f"""
	SELECT
	id_insumo AS ID,
	nome_insumo AS Nome,
	unidade_medida AS Unidade,
	qtd_estoque AS Quantidade,
	custo_unitario AS Custo
	FROM IGOR_CG_ESTOQUE
	{where_clause}
	ORDER BY nome_insumo
	OFFSET ? ROWS
	FETCH NEXT ? ROWS ONLY
	""", (*params, offset, per_page))

	rows = [
		(row[0], row[1].title(), f"{row[3]} {row[2].lower()}", format_currency(row[4]))
		for row in rows
	]

	return columns, rows, page, total_pages, search