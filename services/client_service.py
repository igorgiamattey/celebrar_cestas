from db import run_select
from flask import request
from services.routes_service import countRows
from enums.table_names import Table

def client_exists(name, phone, exclude_id=None):
	query = """
	SELECT 1
	FROM IGOR_CG_CLIENTES
	WHERE nome_razao = ?
	AND telefone = ?
	AND isDeleted = 0
	"""

	params = [name, phone]

	if exclude_id is not None:
		query += " AND id_cliente <> ?"
		params.append(exclude_id)

	_, rows = run_select(query, tuple(params))

	return bool(rows)

def get_clients():
	page = request.args.get("page", 1, type=int)
	page = max(1, page)
	search = request.args.get("search", "", type=str)
	per_page = 10

	where_clause = "WHERE isDeleted = 0"
	params = []
	if search:
		where_clause += " AND nome_razao LIKE ?"
		params.append(f"%{search}%")


	count = countRows(Table.Clients, where_clause, tuple(params))
	total_pages = max((count + per_page - 1)//per_page, 1)
	page = min(page, total_pages)
	offset = (page - 1) * per_page

	columns, rows = run_select(f"""
	SELECT
	id_cliente AS ID,
	nome_razao AS Nome,
	telefone AS Telefone
	FROM IGOR_CG_CLIENTES
	{where_clause}
	ORDER BY nome_razao
	OFFSET ? ROWS
	FETCH NEXT ? ROWS ONLY
	""", (*params, offset, per_page))

	rows = [
		(row[0], row[1].title(), row[2])
		for row in rows
	]

	return columns, rows, page, total_pages, search