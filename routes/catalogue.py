import json

from flask import (Blueprint, jsonify, redirect, render_template, request,
                   session, url_for)

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
						user=session.get("username"),
						available_items = available_items,
						available_groups = available_groups)

@catalogue_bp.route("/search_basket")
def catalogue_search():
	columns, rows, _, _, search = get_catalogue()

	return render_template("catalogue/_catalogue_table_rows.html",
							columns=columns,
							rows=rows,
							search=search)

@catalogue_bp.route("/new_basket", methods=["POST"])
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
		INSERT INTO CELEBRAR_BASKETS
		(basket_name, basket_price)
		OUTPUT INSERTED.basket_id
		VALUES (?, ?)
		""", (name, price))

		basket_id = cursor.fetchone()[0]

		for item in items:
			item_cat = item["category"]
			if item_cat == "items":
				cursor.execute("""
				INSERT INTO CELEBRAR_BASKET_ITEMS
				(basket_id, item_id, item_amount)
				VALUES (?, ?, ?)
				""", (basket_id, item["item_id"], item["quantity"]))

			elif item_cat == "groups":
				cursor.execute("""
				INSERT INTO CELEBRAR_BASKET_ITEMS
				(basket_id, group_id, item_amount)
				VALUES (?, ?, ?)
				""", (basket_id, item["item_id"], item["quantity"]))

	return redirect(request.referrer or url_for("catalogue_bp.catalogue"))

@catalogue_bp.route("/basket_data/<int:id>")
def basket_data(id):
	columns, rows = run_select("""
	SELECT
	basket_id, basket_name, basket_price
	FROM CELEBRAR_BASKETS
	WHERE basket_id = ?
	AND isDeleted = 0
	""", (id,))

	if not rows:
		return jsonify({"error": "Basket not found"}), 404
	row = rows[0]

	basket = dict(zip(columns, row))

	_, items_rows = run_select("""
		SELECT
		bi.item_id,
		s.item_name,
		s.item_unit,
		bi.item_amount,
		bi.group_id,
		g.group_name
		FROM CELEBRAR_BASKET_ITEMS bi
		LEFT JOIN CELEBRAR_STORAGE s
		ON bi.item_id = s.item_id
		LEFT JOIN CELEBRAR_GROUPS g
		ON bi.group_id = g.group_id
		WHERE bi.basket_id = ?
		ORDER BY COALESCE(s.item_name, g.group_name)
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

@catalogue_bp.route("/update_basket", methods=["POST"])
def update_basket():
	try:
		items = json.loads(request.form["items"])
	except (KeyError, json.JSONDecodeError):
		return "Itens inválidos", 400

	try:
		id = request.form["id"]
		if not validate_id(Table.Baskets, "basket_id", id):
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
		UPDATE CELEBRAR_BASKETS
		SET
		basket_name = ?,
		basket_price = ?
		WHERE basket_id = ?
		""", (name, price, id))

		cursor.execute("""
		DELETE FROM CELEBRAR_BASKET_ITEMS
		WHERE basket_id = ?
		""", (id,))

		for item in items:
			item_cat = item["category"]
			if item_cat == "items":
				cursor.execute("""
				INSERT INTO CELEBRAR_BASKET_ITEMS
				(basket_id, item_id, item_amount)
				VALUES (?, ?, ?)
				""", (id, item["item_id"], item["quantity"]))

			elif item_cat == "groups":
				cursor.execute("""
				INSERT INTO CELEBRAR_BASKET_ITEMS
				(basket_id, group_id, item_amount)
				VALUES (?, ?, ?)
				""", (id, item["item_id"], item["quantity"]))

	return redirect(url_for("catalogue_bp.catalogue"))

@catalogue_bp.route("/delete_basket/<int:id>", methods=["POST"])
def delete_basket(id):
	try:
		if not validate_id(Table.Baskets, "basket_id", id):
			raise ValueError("Cesta inválida")
		if basket_has_open_orders(id):
			raise ValueError("Essa cesta está sendo utilizada por um pedido em aberto")
	except ValueError as e:
		return str(e), 400
	
	with run_transaction() as cursor:
		cursor.execute("""
		UPDATE CELEBRAR_BASKETS
		SET
		isDeleted = 1
		WHERE basket_id = ?
		""", (id,))

		cursor.execute("""
		UPDATE CELEBRAR_BASKET_ITEMS
		SET isDeleted = 1
		WHERE basket_id = ?
		""", (id,))

	return "", 204