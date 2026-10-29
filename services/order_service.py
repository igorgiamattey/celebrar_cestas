import json
from datetime import date, datetime

from flask import request

from db import format_currency, format_date_year, run_select
from enums.movement_types import storageMovementTypes
from enums.order_status import OPEN_ORDER_STATUS, orderStatus


def get_basket_composition(id):
	_, rows = run_select(f"""
	SELECT
	bi.item_id, s.item_name, s.item_unit,
	bi.item_amount, bi.group_id, g.group_name
	FROM CELEBRAR_BASKET_ITEMS bi
	LEFT JOIN CELEBRAR_STORAGE s
		ON s.item_id = bi.item_id
		AND s.isDeleted = 0
	LEFT JOIN CELEBRAR_GROUPS g
		ON g.group_id = bi.group_id
		AND g.isDeleted = 0
	WHERE bi.basket_id = ?
	AND bi.isDeleted = 0
	""", (id,))

	fixed_items, group_ids, groups_data = [], [], {}

	for item_id, item_name, item_unit, item_qty, group_id, group_name in rows:
		if group_id is not None:
			group_ids.append(group_id)
			groups_data[group_id] = {
				"group_id": group_id,
				"group_name": group_name,
				"quantity": item_qty,
				"options": []
			}
		else:
			fixed_items.append({
				"item_id": item_id,
				"item_name": item_name,
				"unit": item_unit,
				"quantity": item_qty
			})

	if group_ids:
		placeholders = ','.join(['?'] * len(group_ids))
		_, members_rows = run_select(f"""
			SELECT
			m.group_id, s.item_id, s.item_name, m.group_item_qty, s.item_unit
			FROM CELEBRAR_GROUP_MEMBERS m
			JOIN CELEBRAR_STORAGE s
			ON s.item_id = m.item_id
			WHERE m.group_id IN ({placeholders}) AND m.isDeleted = 0
		""", tuple(group_ids))

		for group_id, item_id, item_name, item_qty, item_unit in members_rows:
			groups_data[group_id]["options"].append({
				"item_id": item_id,
				"item_name": item_name,
				"item_quantity": item_qty,
				"unit": item_unit
			})

	return {
		"basket_id": id,
		"fixed_items": fixed_items,
		"groups": list(groups_data.values())
	}

def update_stock(cursor, item_id, qty, order_id, operation, move_type, obs=""):
	if order_id: obs += f"\nPedido #{order_id}"
	
	if operation == "increase":
		cursor.execute("""
		UPDATE CELEBRAR_STORAGE
		SET
		item_qty = item_qty + ?
		WHERE item_id = ?
		AND isDeleted = 0
		""", (qty, item_id))

	elif operation == "deduct":
		cursor.execute("""
			UPDATE CELEBRAR_STORAGE
			SET
			item_qty = item_qty - ?
			WHERE item_id = ?
			AND item_qty - ? >= 0
			AND isDeleted = 0
			""", (qty, item_id, qty))
		
		if cursor.rowcount == 0:
			raise ValueError(f"Estoque insuficiente para o item {item_id}")

	else:
		raise ValueError("Invalid Operation")

	cursor.execute("""
	INSERT INTO CELEBRAR_STORAGE_MOVES
	(item_id, move_type, amount, obs)
	VALUES (?, ?, ?, ?)
	""", (item_id, move_type, qty, obs))

def update_order_stock(cursor, items_payload, operation, order_id=None):
	move = {
		"deduct": storageMovementTypes.DECREASE_ORDER,
		"increase": storageMovementTypes.INCREASE_ORDER
	}.get(operation)

	if move is None:
		raise ValueError("Invalid Operation")

	needed = {}
	for item in items_payload:
		for item_id, qty in get_stock_requirements(cursor, item).items():
			needed[item_id] = needed.get(item_id, 0) + qty

	for item_id, qty in needed.items():
		update_stock(cursor, item_id, qty, order_id, operation, move_type=move.name)

def get_today():
	return date.today().isoformat()

def get_pending_orders(cursor, exclude_order_id=None):
	query = """
	SELECT
	order_id, order_items
	FROM CELEBRAR_ORDERS
	WHERE order_status = ?
	AND isDeleted = 0
	"""
	params = [orderStatus.PENDING.name]

	if exclude_order_id is not None:
		query += " AND order_id <> ?"
		params.append(exclude_order_id)

	cursor.execute(query, params)
	return cursor.fetchall()

def get_stock_requirements(cursor, item):
	basket_id = item['basket_id']
	basket_qty = item['quantity']

	choices_by_group = {
		c['group_id']: c['item_id']
		for c in item.get('choices', [])
	}

	requirements = {}

	cursor.execute("""
	SELECT
	item_id, item_amount, group_id
	FROM CELEBRAR_BASKET_ITEMS
	WHERE basket_id = ?
	AND isDeleted = 0
	""", (basket_id,))

	recipe_rows = cursor.fetchall()

	for item_id, used_qty, group_id in recipe_rows:
		if group_id is None:
			required_qty = used_qty * basket_qty
			requirements[item_id] = (requirements.get(item_id, 0) + required_qty)

		else:
			chosen_ids = choices_by_group.get(group_id, [])
			if not chosen_ids:
				raise ValueError(
					f"Nenhuma escolha feita para o grupo "
					f"{group_id} (cesta {basket_id})"
				)

			for chosen_item in chosen_ids:
				cursor.execute("""
				SELECT
				group_item_qty
				FROM CELEBRAR_GROUP_MEMBERS
				WHERE group_id = ?
				AND item_id = ?
				AND isDeleted = 0
				""", (group_id, chosen_item))

				row = cursor.fetchone()

				if not row:
					raise ValueError(
						f"Item {chosen_item} não pertence "
						f"ao grupo {group_id}"
					)

				item_qty = row[0]
				requirements[chosen_item] = (
					requirements.get(chosen_item, 0) + item_qty
				)

	return requirements			

def get_pending_stock_requirements(cursor, exclude_order_id=None):
	pending_orders = get_pending_orders(cursor, exclude_order_id)

	requirements = {}

	for _, items_json in pending_orders:
		items_payload = json.loads(items_json)

		for item in items_payload:
			item_requirements = get_stock_requirements(cursor, item)

			for item_id, quantity in item_requirements.items():
				requirements[item_id] = (
					requirements.get(item_id, 0) + quantity
				)

	return requirements

def get_available_stock(cursor, exclude_order_id=None):
	pending_requirements = get_pending_stock_requirements(cursor, exclude_order_id)

	cursor.execute("""
	SELECT
	item_id, item_qty
	FROM CELEBRAR_STORAGE
	WHERE isDeleted = 0
	""")

	stock_rows = cursor.fetchall()
	available_stock = {}

	for item_id, current_stock in stock_rows:
		pending_qty = pending_requirements.get(item_id, 0)
		available_stock[item_id] = current_stock - pending_qty

	return available_stock

def get_orders():
	page = request.args.get("page", 1, type=int)
	page = max(page, 1)
	search = request.args.get("search", "", type=str)
	open_only = request.args.get("openonly", "false").lower() == "true"
	per_page = 1000

	where_clause = "WHERE o.isDeleted = 0"
	params = []
	if search:
		if search.startswith("#"):
			id_part = search[1:].strip()
			if id_part.isdigit():
				where_clause += " AND o.order_id = ?"
				params.append(int(id_part))
		
		else:
			search_param = f"%{search}%"
			conditions = [
				"c.client_name LIKE ?",
				"""EXISTS (
					SELECT 1
					FROM CELEBRAR_ORDER_ITEMS oi
					JOIN CELEBRAR_BASKETS b
					ON b.basket_id = oi.basket_id
					WHERE oi.order_id = o.order_id
					AND b.basket_name LIKE ?
				)""",
				"CONVERT(VARCHAR(10), o.delivery_date, 103) LIKE ?"
			]
			params.extend([search_param, search_param, search_param])

			if search.isdigit():
				conditions.append("o.order_id = ?")
				params.append(int(search))

			matching_status = [s.name for s in orderStatus if search.lower() in s.value.lower()]
			if matching_status:
				conditions.append(f"o.order_status IN ({','.join('?' * len(matching_status))})")
				params.extend(matching_status)
			
			where_clause += " AND (" + " OR ".join(conditions) + ")"

	if open_only:
		open_status = OPEN_ORDER_STATUS
		where_clause += f" AND o.order_status IN ({','.join('?' * len(open_status))})"
		params.extend(open_status)

	_, count_rows = run_select(f"""
	SELECT COUNT(*)
	FROM CELEBRAR_ORDERS o
	JOIN CELEBRAR_CLIENTS c
	ON o.client_id = c.client_id
	{where_clause}
	""", tuple(params))

	total_items = count_rows[0][0]
	total_pages = max((total_items + per_page - 1)//per_page, 1)
	page = min(page, total_pages)

	offset = (page - 1) * per_page

	columns, rows = run_select(f"""
	SELECT
	o.order_id AS ID,
	c.client_name AS Cliente,
	COALESCE(items.summary, '') AS Itens,
	o.delivery_date AS Entrega,
	o.order_total AS Valor,
	o.order_status AS Status,
	o.isDelivery AS Tipo
	FROM CELEBRAR_ORDERS o
	JOIN CELEBRAR_CLIENTS c
	ON o.client_id = c.client_id
	OUTER APPLY (
		SELECT
		STUFF ((
			SELECT
			CHAR (10) + CAST(oi.amount AS VARCHAR) + ' ' + CHAR(215) + ' ' + b.basket_name
			FROM CELEBRAR_ORDER_ITEMS oi
			JOIN CELEBRAR_BASKETS b
			ON b.basket_id = oi.basket_id
			WHERE oi.order_id = o.order_id
			FOR XML PATH(''), TYPE
		).value('.', 'NVARCHAR(MAX)'), 1, 1, '')
		AS summary
	) items
	{where_clause}
	ORDER BY o.delivery_date, o.order_id
	OFFSET ? ROWS
	FETCH NEXT ? ROWS ONLY
	""", (*params, offset, per_page))

	rows = [
		(
			row[0],
			row[1].title(),
			row[2],
			format_date_year(row[3]),
			format_currency(row[4]),
			orderStatus[row[5]].value,
			row[6]
		)
		for row in rows
	]

	return columns, rows, page, total_pages, search

def as_date(value):
	if value is None:
		return None
	if isinstance(value, datetime):
		return value.date()
	if isinstance(value, str):
		return date.fromisoformat(value)
	return value

def save_delivery_address(cursor, client_id, address_id, address_txt):
	address_txt = address_txt.strip() if address_txt else ""

	if not address_txt:
		raise ValueError("Informe um endereço válido")

	if address_id is None:
		cursor.execute("""
		INSERT INTO CELEBRAR_ADDRESSES
		(client_id, address_txt)
		OUTPUT INSERTED.address_id
		VALUES (?, ?)
		""", (client_id, address_txt))

		return cursor.fetchone()[0]

	cursor.execute("""
	UPDATE CELEBRAR_ADDRESSES
	SET address_txt = ?
	WHERE address_id = ?
	AND client_id = ?
	""", (address_txt, address_id, client_id))

	if cursor.rowcount != 1:
		raise ValueError("Endereço inválido para o cliente selecionado.")

	return address_id