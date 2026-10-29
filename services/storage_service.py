from flask import request

from db import format_currency, run_select, run_transaction
from enums.table_names import Table
from services.order_service import get_available_stock
from services.routes_service import countRows


def item_exists(name, exclude_id=None):
	query = """
	SELECT 1
	FROM CELEBRAR_STORAGE
	WHERE item_name = ?
	AND isDeleted = 0
	"""

	params = [name]

	if exclude_id is not None:
		query += " AND item_id <> ?"
		params.append(exclude_id)

	_, rows = run_select(query, tuple(params))

	return bool(rows)

def group_exists(name, exclude_id=None):
	query = """
	SELECT 1
	FROM CELEBRAR_GROUPS
	WHERE group_name = ?
	AND isDeleted = 0
	"""

	params = [name]

	if exclude_id is not None:
		query += " AND group_id <> ?"
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
		where_clause += " AND item_name LIKE ?"
		params.append(f"%{search}%")

	count = countRows(Table.Items, where_clause, tuple(params))
	total_pages = max((count + per_page - 1)//per_page, 1)
	page = min(page, total_pages)
	offset = (page - 1) * per_page

	with run_transaction() as cursor:
		available_stock = get_available_stock(cursor)

	columns, rows = run_select(f"""
	SELECT
	item_id AS ID,
	item_name AS Nome,
	item_unit AS Unidade,
	item_qty AS Estoque,
	item_cost AS Custo
	FROM CELEBRAR_STORAGE
	{where_clause}
	ORDER BY item_name
	OFFSET ? ROWS
	FETCH NEXT ? ROWS ONLY
	""", (*params, offset, per_page))

	columns = [
		columns[0], columns[1], columns[2], columns[3], "Reservado", "Disponível", columns[4]
	]


	rows = [
		(
			row[0],
			row[1].title(),
			row[2].lower(),
			f"{row[3]} {row[2].lower()}",
			f"{row[3] - available_stock.get(row[0], row[3])} {row[2].lower()}",
			f"{available_stock.get(row[0], row[3])} {row[2].lower()}",
			format_currency(row[4]))
		for row in rows
	]

	return columns, rows, page, total_pages, search