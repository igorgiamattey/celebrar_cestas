from datetime import datetime
from decimal import Decimal

import phonenumbers

from db import parse_price, run_select
from enums.movement_types import movementTypes
from enums.order_status import orderStatus
from enums.table_names import Table
from enums.unit_measurement import Unit
from services.order_service import (get_available_stock,
                                    get_basket_composition,
                                    get_stock_requirements)
from services.status_transitions import is_valid_transition


def validate_qty(qty, allow_zero=False):
	try:
		qty = float(qty)
	except (TypeError, ValueError):
		raise ValueError("Quantidade Inválida")

	if qty < 0:
		raise ValueError("A quantidade não pode ser negativa")
	
	if qty == 0 and not allow_zero:
		raise ValueError("A quantidade deve ser maior que zero")

	return qty

def validate_int_qty(qty, allow_zero=False):
	qty = validate_qty(qty, allow_zero)

	if not qty.is_integer():
		raise ValueError("A quantidade deve ser um número inteiro")

	return int(qty)

def validate_price(price, allow_free=False):
	try:
		price = parse_price(price)
	except ValueError:
		raise ValueError("Preço inválido")

	if allow_free:
		if price < 0:
			raise ValueError("O preço não pode ser negativo")
	else:
		if price <= 0:
			raise ValueError("O preço deve ser maior que zero")
		

	return price

def validate_id(table, column, value):
	_, rows = run_select(f"""
	SELECT 1
	FROM {table.value}
	WHERE {column} = ?
	AND isDeleted = 0
	""", (value,))

	return bool(rows)

def validate_date(value, min_date=None, required=True):
	if value is None or value == "":
		if required:
			raise ValueError("Data do pedido é obrigatória")
		return None

	try:
		parsed_date = datetime.strptime(value, "%Y-%m-%d").date()
	except (TypeError, ValueError):
		if required: raise ValueError(f"Data do pedido inválida")
		else: raise ValueError(f"Data de entrega inválida")

	if min_date is not None and parsed_date < min_date:
		raise ValueError("Data de entrega não pode ser anterior à data do pedido")

	return parsed_date

def validate_status(status):
	try:
		return orderStatus[status].name
	except KeyError:
		raise ValueError("Status inválido")

def validate_move(move):
	try:
		return movementTypes[move].name
	except KeyError:
		raise ValueError("Tipo de Movimentação inválida")

def validate_unit(unit):
	try:
		return Unit[unit].name
	except KeyError:
		raise ValueError("Unidade inválida")

def validate_name(name):
	if not isinstance(name, str):
		raise ValueError("Nome inválido")

	name = name.strip()

	if not name:
		raise ValueError("Nome inválido")

	if len(name) > 100:
		raise ValueError("Nome muito longo")

	return name

def validate_phone(phone):
	if not isinstance(phone, str):
		raise ValueError("Telefone inválido")

	phone = phone.strip()

	try:
		number = phonenumbers.parse(phone, "BR")
	except phonenumbers.NumberParseException:
		raise ValueError("Telefone inválido.")

	if not phonenumbers.is_valid_number(number):
		raise ValueError("Telefone inválido.")

	phone = phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
	
	return phone

def validate_status_transition(current, new):
	if not is_valid_transition(current, new):
		raise ValueError(
			f"Não é possível alterar o status de "
			f"{current} para {new}"
		)
	return new

def validate_delivery(form):
	if form.get("isDelivery") not in ("1", "true", "on"):
		return False, None, Decimal("0.00")

	address = form.get("address", "").strip()
	if not address:
		raise ValueError("Endereço obrigatório para entregas")
	if len(address) > 200:
		raise ValueError("Endereço muito longo (máx. 200 caracteres)")

	fee_raw = form.get("deliveryFee", "").strip()
	fee = validate_price(fee_raw, allow_free=True) if fee_raw else Decimal("0.00")
	return True, address, fee

# ---------------------------

def validate_basket_choices(basket_id, quantity, choices):
	composition = get_basket_composition(basket_id)
	groups_by_id = {g["group_id"]: g for g in composition["groups"]}

	if not isinstance(choices, list):
		raise ValueError("Formato de composição inválido")

	choices_by_group = {}
	for c in choices:
		if not isinstance(c, dict) or "group_id" not in c or "item_id" not in c:
			raise ValueError("Escolha de composição inválida")
		if c["group_id"] in choices_by_group:
			raise ValueError("Grupo de composição duplicado")
		choices_by_group[c["group_id"]] = c["item_id"]

	unknown_groups = set(choices_by_group) - set(groups_by_id)
	if unknown_groups:
		raise ValueError("Grupo de composição inválido para essa cesta")

	for group_id, group in groups_by_id.items():
		selected = choices_by_group.get(group_id, [])
		expected_len = quantity * int(group["quantity"])

		if not isinstance(selected, list) or len(selected) != expected_len:
			raise ValueError(
				f"Quantidade de escolhas inválida para o grupo '{group['group_name']}'"
			)

		valid_options_id = {opt["item_id"] for opt in group["options"]}
		for item_id in selected:
			if item_id not in valid_options_id:
				raise ValueError(
					f"Escolha inválida no grupo '{group['group_name']}'"
				)

def validate_order_items(items_payload):
	if not isinstance(items_payload, list) or not items_payload:
		raise ValueError("O pedido deve conter pelo menos uma cesta")

	in_order = set()

	for item in items_payload:
		if not isinstance(item, dict):
			raise ValueError("Item de pedido inválido")

		if "basket_id" not in item or "quantity" not in item:
			raise ValueError("Item de pedido incompleto")

		basket_id = item["basket_id"]
		item["quantity"] = validate_int_qty(item["quantity"])

		if basket_id in in_order:
			raise ValueError("Essa cesta já está no pedido")

		in_order.add(basket_id)

		if not validate_id(Table.Baskets, "id_produto", basket_id):
			raise ValueError("Cesta inválida")

		validate_basket_choices(basket_id, item["quantity"], item.get("choices", []))

	return items_payload

def validate_basket_items(items):
	if not isinstance(items, list) or not items:
		raise ValueError("A cesta deve conter pelo menos um item")

	in_basket = set()

	for item in items:
		if not isinstance(item, dict):
			raise ValueError("Item de cesta inválido")

		if "item_id" not in item or "quantity" not in item or "category" not in item:
			raise ValueError("Item de cesta incompleto")

		item_id = item["item_id"]
		category = item["category"]
		unit = item["unit"]

		key = (category, item_id)

		if key in in_basket:
			raise ValueError("Esse item já está na cesta")

		in_basket.add(key)

		item["quantity"] = validate_qty(item["quantity"])

		if category == "items":
			if unit.lower() == 'un':
				item["quantity"] = validate_int_qty(item["quantity"])	

			if not validate_id(Table.Items, "id_insumo", item_id):
				raise ValueError("Item inválido")

		elif category == "groups":
			item["quantity"] = validate_int_qty(item["quantity"])
			if not validate_id(Table.Groups, "id_grupo", item_id):
				raise ValueError("Grupo inválido")

		else:
			raise ValueError("Categoria de item inválida")

	return items

def validate_group_items(items):
	if not isinstance(items, list) or not items:
		raise ValueError("O grupo deve conter pelo menos um item")

	if len(items) < 2:
		raise ValueError("O grupo deve possuir pelo menos dois itens")

	in_group = set()

	for item in items:
		if not isinstance(item, (list, tuple)) or len(item) != 2:
			raise ValueError("Item do grupo inválido")

		item_id, item_qty = item

		if item_id in in_group:
			raise ValueError("Esse item já está no grupo")

		in_group.add(item_id)

		if not validate_id(Table.Items, "id_insumo", item_id):
			raise ValueError("Item inválido")

		_, rows = run_select("""
		SELECT unidade_medida
		FROM IGOR_CG_ESTOQUE
		WHERE id_insumo = ?
		AND isDeleted = 0
		""", (item_id,))

		if not rows:
			raise ValueError("Item inválido")

		unit = rows[0][0]

		if unit.lower() == "un":
			item_qty = validate_int_qty(item_qty)
		else:
			item_qty = validate_qty(item_qty)

	return items

def validate_order_stock(cursor, items_payload):
	available_stock = get_available_stock(cursor)
	order_requirements = {}

	for item in items_payload:
		requirements = get_stock_requirements(cursor, item)

		for item_id, quantity in requirements.items():
			order_requirements[item_id] = (
				order_requirements.get(item_id, 0) + quantity
			)

	for item_id, required_qty in order_requirements.items():
		available_qty = available_stock.get(item_id, 0)

		if required_qty > available_qty:
			cursor.execute("""
			SELECT
			nome_insumo
			FROM IGOR_CG_ESTOQUE
			WHERE id_insumo = ?
			AND isDeleted = 0
			""", (item_id,))

			row = cursor.fetchone()
			item_name = row[0] if row else f"ID {item_id}"
			raise ValueError(
				f"Estoque insuficiente para o item {item_name}"
			)

# ---------------------------

OPEN_ORDER_STATUS = (
	orderStatus.PENDING.name,
	orderStatus.CONFIRMED.name,
	orderStatus.PREPARING.name,
	orderStatus.READY.name,
)

placeholders = ",".join("?" for _ in OPEN_ORDER_STATUS)

def basket_has_open_orders(id):
	_, rows = run_select(f"""
	SELECT 1
	FROM IGOR_CG_CESTAS_PEDIDO cp
	JOIN IGOR_CG_PEDIDOS p
	ON p.id_pedido = cp.id_pedido
	WHERE cp.id_produto = ?
	AND p.isDeleted = 0
	AND p.status_pedido IN ({placeholders}) 
	""", (id, *OPEN_ORDER_STATUS))

	return bool(rows)

def client_has_open_orders(id):
	_, rows = run_select(f"""
	SELECT 1
	FROM IGOR_CG_PEDIDOS
	WHERE id_cliente = ?
	AND isDeleted = 0
	AND status_pedido IN ({placeholders}) 
	""", (id, *OPEN_ORDER_STATUS))

	return bool(rows)

def item_has_open_orders(id):
	_, rows = run_select(f"""
	SELECT 1
	FROM IGOR_CG_CESTAS_PEDIDO cp
	JOIN IGOR_CG_PEDIDOS p
	ON p.id_pedido = cp.id_pedido
	JOIN IGOR_CG_CESTA_ESTOQUE ce
	ON ce.id_produto = cp.id_produto
	AND ce.isDeleted = 0
	WHERE p.isDeleted = 0
	AND p.status_pedido IN ({placeholders})
	AND (
		ce.id_insumo = ?
		OR EXISTS (
			SELECT 1
			FROM IGOR_CG_MEMBROS_GRUPO mg
			WHERE mg.id_grupo = ce.id_grupo
			AND mg.id_insumo = ?
			AND mg.isDeleted = 0
		)
	)
	""", (*OPEN_ORDER_STATUS, id, id))

	return bool(rows)

def group_has_open_orders(id):
	_, rows = run_select(f"""
	SELECT 1
	FROM IGOR_CG_CESTAS_PEDIDO cp
	JOIN IGOR_CG_PEDIDOS p
	ON p.id_pedido = cp.id_pedido
	JOIN IGOR_CG_CESTA_ESTOQUE ce
	ON ce.id_produto = cp.id_produto
	WHERE ce.id_grupo = ?
	AND ce.isDeleted = 0
	AND p.isDeleted = 0
	AND p.status_pedido IN ({placeholders})
	""", (id, *OPEN_ORDER_STATUS))

	return bool(rows)