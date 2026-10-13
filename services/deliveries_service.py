from flask import request

from db import format_date_year, run_select
from enums.delivery_status import deliveryStatus


def get_deliveries():
	page = request.args.get("page", 1, type=int)
	page = max(page, 1)
	search = request.args.get("search", "", type=str)
	open_only = request.args.get("openonly", "false").lower() == "true"
	per_page = 1000

	where_clause = "WHERE d.isDeleted = 0"
	params = []
	if search:
		if search.startswith("#"):
			id_part = search[1:].strip()
			if id_part.isdigit():
				where_clause += " AND d.id_entrega = ?"
				params.append(int(id_part))
		else:	
			search_param = f"%{search}%"
			conditions = [
				"c.nome_entregador LIKE ?",
				"CONVERT(VARCHAR(10), d.data_entrega, 103) LIKE ?",
			]
			params.extend([search_param, search_param])

			matching_status = [s.name for s in deliveryStatus if search.lower() in s.value.lower()]
			if matching_status:
				conditions.append(f"d.status_entrega IN ({','.join('?' * len(matching_status))})")
				params.extend(matching_status)

			where_clause += " AND (" + " OR ".join(conditions) + ")"

	if open_only:
		open_status = [deliveryStatus.PENDING.name, deliveryStatus.TRANSIT.name]
		where_clause += f" AND d.status_entrega IN ({','.join('?' * len(open_status))})"
		params.extend(open_status)

	_, count_rows = run_select(f"""
	SELECT COUNT(*)
	FROM IGOR_CG_ENTREGAS d
	LEFT JOIN IGOR_CG_ENTREGADORES c
	ON d.id_entregador = c.id_entregador
	{where_clause}
	""", tuple(params))

	total_items = count_rows[0][0]
	total_pages = max((total_items + per_page - 1)//per_page, 1)
	page = min(page, total_pages)

	offset = (page - 1) * per_page

	columns, rows = run_select(f"""
	SELECT
	d.id_entrega AS ID,
	d.data_entrega AS [Data de Entrega],
	c.nome_entregador AS Entregador,
	COUNT(o.id_pedido) AS [Num. Pedidos],
	d.status_entrega AS Status
	FROM IGOR_CG_ENTREGAS d
	LEFT JOIN IGOR_CG_ENTREGADORES c
		ON d.id_entregador = c.id_entregador
	LEFT JOIN IGOR_CG_PEDIDOS o
		ON o.id_entrega = d.id_entrega
		AND o.isDeleted = 0
	{where_clause}
	GROUP BY
		d.id_entrega,
		d.data_entrega,
		c.nome_entregador,
		d.status_entrega
	ORDER BY d.data_entrega, d.id_entrega
	OFFSET ? ROWS
	FETCH NEXT ? ROWS ONLY
	""", (*params, offset, per_page))

	rows = [
		(
			row[0],
			format_date_year(row[1]),
			row[2].title() if row[2] else "---",
			row[3],
			deliveryStatus[row[4]].value,
		)
		for row in rows
	]

	return columns, rows, page, total_pages, search

def courier_exists(name, phone, exclude_id=None):
	query = """
	SELECT 1
	FROM IGOR_CG_ENTREGADORES
	WHERE nome_entregador = ?
	AND telefone = ?
	AND isDeleted = 0
	"""

	params = [name, phone]

	if exclude_id is not None:
		query += " AND id_entregador <> ?"
		params.append(exclude_id)

	_, rows = run_select(query, tuple(params))

	return bool(rows)