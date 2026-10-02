import json

from flask import (Blueprint, jsonify, redirect, render_template, request,
                   url_for)

from db import run_select, run_transaction
from enums.table_names import Table
from services.catalogue_service import basket_exists, get_catalogue
from services.routes_service import getAvailableGroups, getAvailableItems
from services.validate_service import (basket_has_open_orders,
                                       validate_basket_items, validate_id,
                                       validate_name, validate_price)

catalogue_bp = Blueprint("catalogue_bp", __name__)

@catalogue_bp.route("/catalogo")
def catalogue():
	columns, rows, page, total_pages, search = get_catalogue()

	available_items = getAvailableItems()
	available_groups = getAvailableGroups()

	return render_template("catalogue/catalogue.html",
						columns=columns,
						rows=rows,
						page=page,
						total_pages=total_pages,
						search=search,
						user="Vendedor",
						available_items = available_items,
						available_groups = available_groups)

@catalogue_bp.route("/catalogo/search")
def catalogue_search():
	columns, rows, _, _, _ = get_catalogue()

	return render_template("catalogue/_catalogue_table_rows.html",
							columns=columns,
							rows=rows)

@catalogue_bp.route("/nova_cesta", methods=["POST"])
def new_basket():
	try:
		items = json.loads(request.form["items"])
	except (KeyError, json.JSONDecodeError):
		return "Itens da cesta inválidos", 400
	
	try:
		name = validate_name(request.form["name"])
		price = validate_price(request.form["price"])
		items = validate_basket_items(items)
	except ValueError as e:
		return str(e), 400

	if basket_exists(name):
		return "Já existe uma cesta com esse nome", 400

	with run_transaction() as cursor:
		cursor.execute("""
		INSERT INTO IGOR_CG_PRODUTOS
		(nome_cesta, preco_venda)
		OUTPUT INSERTED.id_produto
		VALUES (?, ?)
		""", (name, price))

		basket_id = cursor.fetchone()[0]

		for item in items:
			item_cat = item["category"]
			if item_cat == "items":
				cursor.execute("""
				INSERT INTO IGOR_CG_CESTA_ESTOQUE
				(id_produto, id_insumo, quantidade_utilizada)
				VALUES (?, ?, ?)
				""", (basket_id, item["item_id"], item["quantity"]))

			elif item_cat == "groups":
				cursor.execute("""
				INSERT INTO IGOR_CG_CESTA_ESTOQUE
				(id_produto, id_grupo, quantidade_utilizada)
				VALUES (?, ?, ?)
				""", (basket_id, item["item_id"], item["quantity"]))

	return redirect(request.referrer or url_for("catalogue_bp.catalogue"))

@catalogue_bp.route("/catalogo/<int:id>/data")
def basket_data(id):
	columns, rows = run_select("""
	SELECT
	id_produto, nome_cesta, preco_venda
	FROM IGOR_CG_PRODUTOS
	WHERE id_produto = ?
	AND isDeleted = 0
	""", (id,))

	if not rows:
		return jsonify({"error": "Basket not found"}), 404
	row = rows[0]

	basket = dict(zip(columns, row))

	_, items_rows = run_select("""
		SELECT
		c_e.id_insumo,
		e.nome_insumo,
		e.unidade_medida,
		c_e.quantidade_utilizada,
		c_e.id_grupo,
		g.nome_grupo
		FROM IGOR_CG_CESTA_ESTOQUE c_e
		LEFT JOIN IGOR_CG_ESTOQUE e
		ON c_e.id_insumo = e.id_insumo
		LEFT JOIN IGOR_CG_GRUPOS_ITEM g
		ON c_e.id_grupo = g.id_grupo
		WHERE c_e.id_produto = ?
		ORDER BY COALESCE(e.nome_insumo, g.nome_grupo)
	""", (id,))

	basket["items"] = [
		{
			"item_id": item[0] if item[0] is not None else item[4],
			"item_name": item[1] if item[1] is not None else item[5],
			"unit": item[2] if item[0] is not None else "un",
			"quantity": float(item[3]),
			"category": "items" if item[0] is not None else "groups"
		}
		for item in items_rows
	]
	
	return jsonify(basket)

@catalogue_bp.route("/catalogo/update", methods=["POST"])
def update_basket():
	try:
		items = json.loads(request.form["items"])
	except (KeyError, json.JSONDecodeError):
		return "Itens inválidos", 400

	try:
		id = request.form["id"]
		if not validate_id(Table.Baskets, "id_produto", id):
			raise ValueError("Cesta inválida")
		name = validate_name(request.form["name"])
		price = validate_price(request.form["price"])
		items = validate_basket_items(items)
		if basket_has_open_orders(id):
			raise ValueError("Essa cesta está sendo utilizada por um pedido em aberto")
	except ValueError as e:
		return str(e), 400

	if basket_exists(name, id):
		return "Já existe uma cesta com esse nome", 400
	
	with run_transaction() as cursor:
		cursor.execute("""
		UPDATE IGOR_CG_PRODUTOS
		SET
		nome_cesta = ?,
		preco_venda = ?
		WHERE id_produto = ?
		""", (name, price, id))

		cursor.execute("""
		DELETE FROM IGOR_CG_CESTA_ESTOQUE
		WHERE id_produto = ?
		""", (id,))

		for item in items:
			item_cat = item["category"]
			if item_cat == "items":
				cursor.execute("""
				INSERT INTO IGOR_CG_CESTA_ESTOQUE
				(id_produto, id_insumo, quantidade_utilizada)
				VALUES (?, ?, ?)
				""", (id, item["item_id"], item["quantity"]))

			elif item_cat == "groups":
				cursor.execute("""
				INSERT INTO IGOR_CG_CESTA_ESTOQUE
				(id_produto, id_grupo, quantidade_utilizada)
				VALUES (?, ?, ?)
				""", (id, item["item_id"], item["quantity"]))

	return redirect(url_for("catalogue_bp.catalogue"))

@catalogue_bp.route("/catalogo/<int:id>/delete", methods=["POST"])
def delete_basket(id):
	try:
		if not validate_id(Table.Baskets, "id_produto", id):
			raise ValueError("Cesta inválida")
		if basket_has_open_orders(id):
			raise ValueError("Essa cesta está sendo utilizada por um pedido em aberto")
	except ValueError as e:
		return str(e), 400
	
	with run_transaction() as cursor:
		cursor.execute("""
		UPDATE IGOR_CG_PRODUTOS
		SET
		isDeleted = 1
		WHERE id_produto = ?
		""", (id,))

		cursor.execute("""
		UPDATE IGOR_CG_CESTA_ESTOQUE
		SET isDeleted = 1
		WHERE id_produto = ?
		""", (id,))

	return "", 204