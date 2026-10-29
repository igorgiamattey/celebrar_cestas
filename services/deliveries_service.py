from flask import request

from db import format_date_year, run_select
from enums.delivery_status import deliveryStatus, OPEN_DELIVERY_STATUS


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
				where_clause += " AND d.delivery_id = ?"
				params.append(int(id_part))
		else:	
			search_param = f"%{search}%"
			conditions = [
				"c.courier_name LIKE ?",
				"CONVERT(VARCHAR(10), d.delivery_date, 103) LIKE ?",
			]
			params.extend([search_param, search_param])

			matching_status = [s.name for s in deliveryStatus if search.lower() in s.value.lower()]
			if matching_status:
				conditions.append(f"d.delivery_status IN ({','.join('?' * len(matching_status))})")
				params.extend(matching_status)

			where_clause += " AND (" + " OR ".join(conditions) + ")"

	if open_only:
		open_status = OPEN_DELIVERY_STATUS
		where_clause += f" AND d.delivery_status IN ({','.join('?' * len(open_status))})"
		params.extend(open_status)

	_, count_rows = run_select(f"""
	SELECT COUNT(*)
	FROM CELEBRAR_DELIVERIES d
	LEFT JOIN CELEBRAR_COURIERS c
	ON d.courier_id = c.courier_id
	{where_clause}
	""", tuple(params))

	total_items = count_rows[0][0]
	total_pages = max((total_items + per_page - 1)//per_page, 1)
	page = min(page, total_pages)

	offset = (page - 1) * per_page

	columns, rows = run_select(f"""
	SELECT
	d.delivery_id AS ID,
	d.delivery_date AS [Data de Entrega],
	c.courier_name AS Entregador,
	COUNT(o.order_id) AS [Num. Pedidos],
	d.delivery_status AS Status
	FROM CELEBRAR_DELIVERIES d
	LEFT JOIN CELEBRAR_COURIERS c
		ON d.courier_id = c.courier_id
	LEFT JOIN CELEBRAR_ORDERS o
		ON o.delivery_id = d.delivery_id
		AND o.isDeleted = 0
	{where_clause}
	GROUP BY
		d.delivery_id,
		d.delivery_date,
		c.courier_name,
		d.delivery_status
	ORDER BY d.delivery_date, d.delivery_id
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
	FROM CELEBRAR_COURIERS
	WHERE courier_name = ?
	AND courier_phone = ?
	AND isDeleted = 0
	"""

	params = [name, phone]

	if exclude_id is not None:
		query += " AND courier_id <> ?"
		params.append(exclude_id)

	_, rows = run_select(query, tuple(params))

	return bool(rows)