from flask import (Blueprint, json, jsonify, redirect, render_template,
                   request, url_for)

from db import (format_date, run_select, run_transaction,
                run_update)
from enums.movement_types import movementTypes
from enums.table_names import Table
from services.order_service import update_stock
from services.routes_service import getAvailableUnits
from services.storage_service import group_exists, item_exists, get_storage
from services.validate_service import (group_has_open_orders,
                                       item_has_open_orders,
                                       validate_group_items, validate_id,
                                       validate_move, validate_name,
                                       validate_price, validate_qty,
                                       validate_unit)

storage_bp = Blueprint("storage_bp", __name__)

@storage_bp.route("/estoque")
def storage():
	columns, rows, page, total_pages, search = get_storage()

	_, groups_rows = run_select("""
	SELECT id_grupo, nome_grupo
	FROM IGOR_CG_GRUPOS_ITEM
	WHERE isDeleted = 0
	ORDER BY nome_grupo
	""")

	_, items_row = run_select(f"""
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
			"title": row[1],
			"unit": row[2]
		}
		for row in items_row
	]

	available_movements = [
		movementTypes.ENTRADA,
		movementTypes.SAIDA
	]

	return render_template("storage/storage.html",
						columns=columns,
						rows=rows,
						page=page,
						total_pages=total_pages,
						search=search,
						user="Vendedor",
						existing_groups=groups_rows,
						available_items=available_items,
						available_movements=available_movements,
						units=getAvailableUnits())

@storage_bp.route("/estoque/search")
def storage_search():
	columns, rows, _, _, _ = get_storage()
	
	return render_template("storage/_storage_table_rows.html",
							columns=columns,
							rows=rows)

@storage_bp.route("/novo_item", methods=["POST"])
def new_item():

	try:
		name = validate_name(request.form["name"])
		unit = validate_unit(request.form["unit"])
		amount = validate_qty(request.form["amount"], True)
		minimal = validate_qty(request.form["minimal"])
		cost = validate_price(request.form["cost"])
	except ValueError as e:
		return str(e), 400

	if item_exists(name):
		return "Já existe um item com esse nome", 400

	run_update("""
	INSERT INTO IGOR_CG_ESTOQUE
	(nome_insumo, unidade_medida, qtd_estoque, estoque_minimo, custo_unitario)
	VALUES (?, ?, ?, ?, ?)
	""", (name, unit, amount, minimal, cost))

	return redirect(request.referrer or url_for("storage_bp.storage"))

@storage_bp.route("/estoque/<int:id>/data")
def item_data(id):
	columns, rows = run_select("""
	SELECT
	id_insumo, nome_insumo,
	unidade_medida, qtd_estoque,
	estoque_minimo, custo_unitario
	FROM IGOR_CG_ESTOQUE
	WHERE id_insumo = ?
	AND isDeleted = 0
	""", (id,))
	if not rows:
		return jsonify({"error": "Item not found"}), 404
	row = rows[0]
	return jsonify(dict(zip(columns, row)))

@storage_bp.route("/estoque/falta")
def storage_miss():
	_, rows = run_select(f"""
	SELECT
	nome_insumo AS Nome,
	unidade_medida AS Unidade,
	qtd_estoque AS Quantidade
	FROM IGOR_CG_ESTOQUE
	WHERE isDeleted = 0 AND qtd_estoque <= estoque_minimo
	""")

	lines = [
		f"{row[0]}: {row[2]} {row[1].lower()}" for row in rows
	]

	text = "\n".join(lines)

	return jsonify({"missing_items": text})

@storage_bp.route("/estoque/<int:id>/movimentacoes")
def storage_moves(id):
	_, moves_row = run_select(f"""
	SELECT TOP 10
	tipo_movimentacao, quantidade, data_movimentacao, observacao
	FROM IGOR_CG_MOVIMENTACOES_ESTOQUE
	WHERE id_insumo = ?
	AND isDeleted = 0
	ORDER BY data_movimentacao DESC, id_movimentacao DESC
	""", (id,))

	movements = [
		{
		"type": row[0],
		"type_value": movementTypes[row[0]].value,
		"quantity": row[1],
		"date": format_date(row[2]),
		"observation": row[3]
		}
		for row in moves_row
	]

	return jsonify(movements)

@storage_bp.route("/estoque/<int:id>/nova_movimentacao", methods=["POST"])
def save_move(id):
	data = request.get_json()

	if not isinstance(data, dict):
		return jsonify({"error": "Dados inválidos"}), 400

	try:
		movement_type = validate_move(data["type"])
		quantity = validate_qty(data["quantity"])
		
		obs = data.get("obs", "")

		with run_transaction() as cursor:
			if movement_type == movementTypes.SAIDA.name:
				update_stock(cursor, id, quantity, None, "deduct", movement_type, obs)

			elif movement_type == movementTypes.ENTRADA.name:
				update_stock(cursor, id, quantity, None, "increase", movement_type, obs)

			else:
				raise ValueError("Tipo de movimentação inválido")

		return jsonify({"success": True})
				

	except ValueError as e:
		return jsonify({"error": str(e)}), 400

@storage_bp.route("/estoque/update", methods=["POST"])
def update_item():
	try:
		id = request.form["id"]
		if not validate_id(Table.Items, "id_insumo", id):
			raise ValueError("Item inválido")
		name = validate_name(request.form["name"])
		unit = validate_unit(request.form["unit"])
		minimal = validate_qty(request.form["minimal"])
		cost = validate_price(request.form["cost"])
	except ValueError as e:
		return str(e), 400

	if item_exists(name, id):
		return "Já existe um item com esse nome", 400

	run_update("""
	UPDATE IGOR_CG_ESTOQUE
	SET
	nome_insumo = ?,
	unidade_medida = ?,
	estoque_minimo = ?,
	custo_unitario = ?
	WHERE id_insumo = ?
	""", (name, unit, minimal, cost, id))

	return redirect(url_for("storage_bp.storage"))

@storage_bp.route("/estoque/<int:id>/delete", methods=["POST"])
def delete_item(id):
	try:
		if not validate_id(Table.Items, "id_insumo", id):
			raise ValueError("Item inválido")
		if item_has_open_orders(id):
			raise ValueError("Esse item faz parte de um pedido em aberto")
	except ValueError as e:
		return str(e), 400
	
	run_update("""
	UPDATE IGOR_CG_ESTOQUE
	SET
	isDeleted = 1
	WHERE id_insumo = ?
	""", (id,))

	return "", 204

@storage_bp.route("/estoque/grupos/<int:id>/data")
def group_data(id):
	_, rows = run_select("""
	SELECT nome_grupo
	FROM IGOR_CG_GRUPOS_ITEM
	WHERE id_grupo = ?
	AND isDeleted = 0
	""", (id,))

	if not rows:
		return jsonify({"error": "Group not found"}), 404

	group_name = rows[0][0]

	_, items_rows = run_select("""
	SELECT e.id_insumo, e.nome_insumo, m.qtd_item_grupo, e.unidade_medida
	FROM IGOR_CG_MEMBROS_GRUPO m
	JOIN IGOR_CG_ESTOQUE e
	ON m.id_insumo = e.id_insumo
	WHERE m.id_grupo = ?
	AND m.isDeleted = 0
	AND e.isDeleted = 0
	""", (id,))

	items = [
		{"item_id": row[0], "item_name": row[1], "item_qty": row[2], "unit": row[3]}
		for row in items_rows
	]

	return jsonify({"group_name": group_name, "items": items})

@storage_bp.route("/estoque/grupos/save", methods=["POST"])
def save_group():
	try:
		items = json.loads(request.form["items"])
	except (KeyError, json.JSONDecodeError):
		return "Itens inválidos", 400

	
	try:
		group_id = request.form.get("group_id")
		if group_id:
			if not validate_id(Table.Groups, "id_grupo", group_id):
				raise ValueError("Grupo inválido")

			if group_has_open_orders(group_id):
				return (
					"Não é possível alterar este grupo "
					"porque ele está sendo utilizado por um pedido em aberto.",
					400
				)
				
		group_name = validate_name(request.form["group_name"])
		items = validate_group_items(items)
	except ValueError as e:
		return str(e), 400

	if group_exists(group_name, group_id):
		return "Já existe um grupo com esse nome", 400

	with run_transaction() as cursor:
		if group_id:
			cursor.execute("""
			UPDATE IGOR_CG_GRUPOS_ITEM
			SET
			nome_grupo = ?
			WHERE id_grupo = ?
			""", (group_name,group_id))

			cursor.execute("""
			DELETE FROM IGOR_CG_MEMBROS_GRUPO
			WHERE id_grupo = ?
			""", (group_id,))

		else:
			cursor.execute("""
			INSERT INTO IGOR_CG_GRUPOS_ITEM
			(nome_grupo)
			VALUES (?)
			""", (group_name,))

			cursor.execute("""
			SELECT SCOPE_IDENTITY()
			""")
			group_id = int(cursor.fetchone()[0])

		for item_id, item_qty in items:
			cursor.execute("""
			INSERT INTO IGOR_CG_MEMBROS_GRUPO
			(id_grupo, id_insumo, qtd_item_grupo)
			VALUES (?, ?, ?)
			""", (group_id, item_id, item_qty))

	return redirect(url_for("storage_bp.storage"))

@storage_bp.route("/estoque/grupos/<int:id>/delete", methods=["POST"])
def delete_group(id):
	try:
		if not validate_id(Table.Groups, "id_grupo", id):
			raise ValueError("Item inválido")
		if group_has_open_orders(id):
			raise ValueError("Esse grupo faz parte de um pedido em aberto")
	except ValueError as e:
		return str(e), 400
	
	with run_transaction() as cursor:
		cursor.execute("""
		UPDATE IGOR_CG_MEMBROS_GRUPO
		SET
		isDeleted = 1
		WHERE id_grupo = ?
		""", (id,))

		cursor.execute("""
		UPDATE IGOR_CG_GRUPOS_ITEM
		SET
		isDeleted = 1
		WHERE id_grupo = ?
		""", (id,))

	return "", 204