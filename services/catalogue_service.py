from flask import request

from db import format_currency, run_select
from enums.table_names import Table
from services.routes_service import countRows

def basket_exists(name, exclude_id=None):
	query = """
	SELECT 1
	FROM IGOR_CG_PRODUTOS
	WHERE nome_cesta = ?
	AND isDeleted = 0
	"""

	params = [name]

	if exclude_id is not None:
		query += " AND id_produto <> ?"
		params.append(exclude_id)

	_, rows = run_select(query, tuple(params))

	return bool(rows)

def get_catalogue():
	page = request.args.get("page", 1, type=int)
	page = max(1, page)
	search = request.args.get("search", "", type=str)
	per_page = 1000

	where_clause = "WHERE isDeleted = 0"
	params = []
	if search:
		where_clause += " AND nome_cesta LIKE ?"
		params.append(f"%{search}%")

	count = countRows(Table.Baskets, where_clause, tuple(params))
	total_pages = max((count + per_page - 1)//per_page, 1)
	page = min(page, total_pages)
	offset = (page - 1) * per_page
	
	columns, rows = run_select(f"""
	SELECT
	id_produto AS ID,
	nome_cesta AS Nome,
	preco_venda AS [Preço]
	FROM IGOR_CG_PRODUTOS
	{where_clause}
	ORDER BY nome_cesta
	OFFSET ? ROWS
	FETCH NEXT ? ROWS ONLY
	""", (*params, offset, per_page))

	rows = [
		(row[0], row[1].title(), format_currency(row[2]))
		for row in rows
	]

	return columns, rows, page, total_pages, search