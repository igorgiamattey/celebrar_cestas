import json
from datetime import date

from flask import request

from db import format_currency, format_date_year, run_select
from enums.movement_types import movementTypes
from enums.order_status import orderStatus

def get_basket_composition(id):
	_, rows = run_select(f"""
	SELECT
	ce.id_insumo, e.nome_insumo, e.unidade_medida,
	ce.quantidade_utilizada, ce.id_grupo, g.nome_grupo
	FROM IGOR_CG_CESTA_ESTOQUE ce
	LEFT JOIN IGOR_CG_ESTOQUE e
		ON e.id_insumo = ce.id_insumo
		AND e.isDeleted = 0
	LEFT JOIN IGOR_CG_GRUPOS_ITEM g
		ON g.id_grupo = ce.id_grupo
		AND g.isDeleted = 0
	WHERE ce.id_produto = ?
	AND ce.isDeleted = 0
	""", (id,))

	fixed_items, group_ids, groups_data = [], [], {}

	for id_insumo, nome_insumo, unidade, qtd, id_grupo, nome_grupo in rows:
		if id_grupo is not None:
			group_ids.append(id_grupo)
			groups_data[id_grupo] = {
				"group_id": id_grupo,
				"group_name": nome_grupo,
				"quantity": qtd,
				"options": []
			}
		else:
			fixed_items.append({
				"item_id": id_insumo,
				"item_name": nome_insumo,
				"unit": unidade,
				"quantity": qtd
			})

	if group_ids:
		placeholders = ','.join(['?'] * len(group_ids))
		_, members_rows = run_select(f"""
			SELECT
			mg.id_grupo, e.id_insumo, e.nome_insumo, mg.qtd_item_grupo, e.unidade_medida
			FROM IGOR_CG_MEMBROS_GRUPO mg
			JOIN IGOR_CG_ESTOQUE e
			ON e.id_insumo = mg.id_insumo
			WHERE mg.id_grupo IN ({placeholders}) AND mg.isDeleted = 0
		""", tuple(group_ids))

		for id_grupo, id_insumo, nome_insumo, qtd, unidade in members_rows:
			groups_data[id_grupo]["options"].append({
				"item_id": id_insumo,
				"item_name": nome_insumo,
				"item_quantity": qtd,
				"unit": unidade
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
		UPDATE IGOR_CG_ESTOQUE
		SET
		qtd_estoque = qtd_estoque + ?
		WHERE id_insumo = ?
		AND isDeleted = 0
		""", (qty, item_id))

	elif operation == "deduct":
		cursor.execute("""
			UPDATE IGOR_CG_ESTOQUE
			SET
			qtd_estoque = qtd_estoque - ?
			WHERE id_insumo = ?
			AND qtd_estoque - ? >= 0
			AND isDeleted = 0
			""", (qty, item_id, qty))
		
		if cursor.rowcount == 0:
			raise ValueError(f"Estoque insuficiente para o item {item_id}")

	else:
		raise ValueError("Invalid Operation")

	cursor.execute("""
	INSERT INTO IGOR_CG_MOVIMENTACOES_ESTOQUE
	(id_insumo, tipo_movimentacao, quantidade, observacao)
	VALUES (?, ?, ?, ?)
	""", (item_id, move_type, qty, obs))

def update_order_stock(cursor, items_payload, operation, order_id=None):
	move = {
		"deduct": movementTypes.SAIDA_PEDIDO,
		"increase": movementTypes.ENTRADA_PEDIDO
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
	id_pedido, itens_pedido
	FROM IGOR_CG_PEDIDOS
	WHERE status_pedido = ?
	AND isDeleted = 0
	"""
	params = [orderStatus.PENDING.name]

	if exclude_order_id is not None:
		query += " AND id_pedido <> ?"
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
	id_insumo, quantidade_utilizada, id_grupo
	FROM IGOR_CG_CESTA_ESTOQUE
	WHERE id_produto = ?
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
				qtd_item_grupo
				FROM IGOR_CG_MEMBROS_GRUPO
				WHERE id_grupo = ?
				AND id_insumo = ?
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
	id_insumo, qtd_estoque
	FROM IGOR_CG_ESTOQUE
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

	where_clause = "WHERE p.isDeleted = 0"
	params = []
	if search:
		where_clause += """
					AND (
					c.nome_razao LIKE ?
					OR EXISTS (
						SELECT 1
						FROM IGOR_CG_CESTAS_PEDIDO cp
						JOIN IGOR_CG_PRODUTOS pr
						ON pr.id_produto = cp.id_produto
						WHERE cp.id_pedido = p.id_pedido
						AND pr.nome_cesta LIKE ?
					)
					OR CONVERT(VARCHAR(10), p.data_entrega, 103) LIKE ?
					OR CASE p.status_pedido
						WHEN 'PENDING' THEN 'Pagamento pendente'
						WHEN 'CONFIRMED' THEN 'Confirmado'
						WHEN 'PREPARING' THEN 'Em preparação'
						WHEN 'READY' THEN 'Pronto'
						WHEN 'DELIVERED' THEN 'Entregue'
						WHEN 'CANCELLED' THEN 'Cancelado'
					END LIKE ?
			)"""
		search_param = f"%{search}%"
		params.extend([search_param, search_param, search_param, search_param])

	if open_only:
			where_clause += """
					 AND p.status_pedido IN ('PENDING', 'CONFIRMED', 'PREPARING', 'READY')
			"""

	_, count_rows = run_select(f"""
	SELECT COUNT(*)
	FROM IGOR_CG_PEDIDOS p
	JOIN IGOR_CG_CLIENTES c
	ON p.id_cliente = c.id_cliente
	{where_clause}
	""", tuple(params))

	total_items = count_rows[0][0]
	total_pages = max((total_items + per_page - 1)//per_page, 1)
	page = min(page, total_pages)

	offset = (page - 1) * per_page

	columns, rows = run_select(f"""
	SELECT
	p.id_pedido AS ID,
	c.nome_razao AS Cliente,
	COALESCE(items.summary, '') AS Itens,
	p.data_entrega AS Entrega,
	p.valor_total AS Valor,
	p.status_pedido AS Status,
	p.isDelivery AS [Retirada/Entrega]
	FROM IGOR_CG_PEDIDOS p
	JOIN IGOR_CG_CLIENTES c
	ON p.id_cliente = c.id_cliente
	OUTER APPLY (
		SELECT
		STUFF ((
			SELECT
			CHAR (10) + CAST(cp.quantidade AS VARCHAR) + ' ' + CHAR(215) + ' ' + pr.nome_cesta
			FROM IGOR_CG_CESTAS_PEDIDO cp
			JOIN IGOR_CG_PRODUTOS pr
			ON pr.id_produto = cp.id_produto
			WHERE cp.id_pedido = p.id_pedido
			FOR XML PATH(''), TYPE
		).value('.', 'NVARCHAR(MAX)'), 1, 1, '')
		AS summary
	) items
	{where_clause}
	ORDER BY p.data_entrega, p.id_pedido
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