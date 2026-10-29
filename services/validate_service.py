import math
from datetime import date, datetime

import phonenumbers

from db import parse_price, run_select
from enums.delivery_status import OPEN_DELIVERY_STATUS, deliveryStatus
from enums.financial_status import financialStatus, DATE_REQUIRED_STATUSES
from enums.movement_types import (CAT_BY_TYPE, financialMovementCategories,
                                  financialMovementTypes, storageMovementTypes)
from enums.order_status import OPEN_ORDER_STATUS, orderStatus
from enums.table_names import Table
from enums.unit_measurement import Unit
from services.order_service import (get_available_stock,
                                    get_basket_composition,
                                    get_stock_requirements)
from services.status_transitions import is_valid_transition

MAX_DECIMAL = 100_000_000

def validate_qty(qty, allow_zero=False, integer=False):
	try:
		qty = float(qty)
	except (TypeError, ValueError):
		raise ValueError("Quantidade Inválida")

	if not math.isfinite(qty):
		raise ValueError("Quantidade não pode ser infinita")
	
	if not integer and qty >= MAX_DECIMAL:
		raise ValueError("Quantidade muito alta")

	if integer:
		if not qty.is_integer():
			raise ValueError("A quantidade deve ser um número inteiro")
		qty = int(qty)

	if qty < 0:
		raise ValueError("A quantidade não pode ser negativa")
	
	if qty == 0 and not allow_zero:
		raise ValueError("A quantidade deve ser maior que zero")

	return qty

def validate_price(price, allow_free=False):
	try:
		price = parse_price(price)
	except ValueError:
		raise ValueError("Preço inválido")

	if price >= MAX_DECIMAL:
		raise ValueError("Preço muito alto")

	if allow_free:
		if price < 0:
			raise ValueError("O preço não pode ser negativo")
	elif price <= 0:
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
		if required:
			raise ValueError(f"Data do pedido inválida")
		
		else:
			raise ValueError(f"Data de entrega inválida")

	if min_date is not None and parsed_date < min_date:
		raise ValueError("Data de entrega não pode ser anterior à data do pedido")

	return parsed_date

def validate_pay_date(value, status):
	if status not in DATE_REQUIRED_STATUSES:
		return None

	if value is None or value == "":
		raise ValueError("A data de pagamento é obrigatória")

	try:
		parsed_date = datetime.strptime(value, "%Y-%m-%d").date()
	except (TypeError, ValueError):
		raise ValueError("Data de pagamento inválida")

	if parsed_date > date.today():
		raise ValueError("A data de pagamento não pode ser futura")

	return parsed_date

def validate_date_id(value, delivery_id=None):
	try:
		value = date.fromisoformat(value)
	except (TypeError, ValueError):
		return False

	_, rows = run_select(f"""
	SELECT 1
	FROM CELEBRAR_ORDERS
	WHERE isDeleted = 0
	AND isDelivery = 1
	AND (delivery_id IS NULL OR delivery_id = ?)
	AND order_status = ?
	AND delivery_date = ?
	""", (delivery_id, orderStatus.READY.name, value))

	return bool(rows)
	
def validate_order_status(status):
	try:
		return orderStatus[status].name
	except KeyError:
		raise ValueError("Status inválido")

def validate_delivery_status(status):
	try:
		return deliveryStatus[status].name
	except KeyError:
		raise ValueError("Status inválido")

def validate_financial_status(status):
	try:
		return financialStatus[status].name
	except KeyError:
		raise ValueError("Status inválido")

def validate_financial_type(fin_type):
	try:
		return financialMovementTypes[fin_type].name
	except KeyError:
		raise ValueError("Tipo de lançamento inválido")

def validate_financial_category(category, fin_type):
	try:
		category = financialMovementCategories[category]
		if category == financialMovementCategories.REFUND:
			raise ValueError("Estornos só podem ser criados pela opção de estorno")
	except KeyError:
		raise ValueError("Categoria inválida")

	if category not in CAT_BY_TYPE[fin_type]:
		raise ValueError("Categoria inválida para o tipo selecionado")

	return category.name

def validate_move(move):
	try:
		return storageMovementTypes[move].name
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

def validate_status_transition(current, new, mode):
	if not is_valid_transition(current, new, mode):
		raise ValueError(
			f"Não é possível alterar o status de "
			f"{current.title} para {new.title}"
		)
	return new

def validate_address(address):
	if not isinstance(address, str):
		raise ValueError("Endereço inválido")

	address = address.strip()

	if not address:
		raise ValueError("O endereço não pode estar vazio")

	if len(address) > 200:
		raise ValueError("O endereço é muito longo (max. 200 caracteres)")

	return address

def validate_delivery(delivery_details):
	if not isinstance(delivery_details, dict):
		raise ValueError("Detalhes de entrega inválidos")
	
	address_id = delivery_details.get("address_id")
	if address_id == "":
		address_id = None
	address_txt = delivery_details.get("address_txt")
	delivery_fee = delivery_details.get("delivery_fee")
	
	if not address_txt:
		raise ValueError("Entrega precisa de um endereço")
	
	address_txt = validate_address(address_txt)

	if address_id is not None:
		if not validate_id(Table.Addresses, "address_id", address_id):
			raise ValueError("Endereço inválido")

	delivery_details["address_id"] = address_id
	delivery_details["delivery_fee"] = validate_price(delivery_fee, allow_free=True)
	delivery_details["address_txt"] = address_txt or None

	return delivery_details

def validate_address_belonging(client, address):
	_, rows = run_select("""
	SELECT address_id
	FROM CELEBRAR_ADDRESSES
	WHERE address_id = ?
	AND client_id = ?
	AND isDeleted = 0
	""", (address, client))

	if not rows:
		raise ValueError("Esse endereço não pertence ao cliente selecionado")

def validate_isDelivery_check(is_delivery, details):
	if not isinstance(details, dict):
		raise ValueError("Detalhes de entrega inválidos")
	
	is_delivery = is_delivery == "on"

	if not is_delivery:
		address_id = details.get("address_id")
		address_txt = details.get("address_txt")
		delivery_fee = details.get("delivery_fee")
		has_fee = delivery_fee not in (None, "") and parse_price(delivery_fee) != 0

		if address_id or address_txt or has_fee:
			raise ValueError("Endereço e taxa de entrega só podem existir para entregas")

	return int(is_delivery)

def validate_opt_text(value, field_name, max_len):
	if value is None:
		return ""
	
	if not isinstance(value, str):
		raise ValueError(f"{field_name} inválido(a)")

	value = value.strip()

	if len(value) > max_len:
		raise ValueError(f"{field_name} deve ter no máximo {max_len} caracteres.")

	return value

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
		item["quantity"] = validate_qty(item["quantity"], integer=True)

		if basket_id in in_order:
			raise ValueError("Essa cesta já está no pedido")

		in_order.add(basket_id)

		if not validate_id(Table.Baskets, "basket_id", basket_id):
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
				item["quantity"] = validate_qty(item["quantity"], integer=True)	

			if not validate_id(Table.Items, "item_id", item_id):
				raise ValueError("Item inválido")

		elif category == "groups":
			item["quantity"] = validate_qty(item["quantity"], integer=True)
			if not validate_id(Table.Groups, "group_id", item_id):
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

	for index, item in enumerate(items):
		if not isinstance(item, (list, tuple)) or len(item) != 2:
			raise ValueError("Item do grupo inválido")

		item_id, item_qty = item

		if item_id in in_group:
			raise ValueError("Esse item já está no grupo")

		in_group.add(item_id)

		if not validate_id(Table.Items, "item_id", item_id):
			raise ValueError("Item inválido")

		_, rows = run_select("""
		SELECT item_unit
		FROM CELEBRAR_STORAGE
		WHERE item_id = ?
		AND isDeleted = 0
		""", (item_id,))

		if not rows:
			raise ValueError("Item inválido")

		unit = rows[0][0]

		if unit.lower() == "un":
			item_qty = validate_qty(item_qty, integer=True)
		else:
			item_qty = validate_qty(item_qty)

		items[index] = (item_id, item_qty)

	return items

def validate_order_stock(cursor, items_payload, exclude_order_id=None):
	available_stock = get_available_stock(cursor, exclude_order_id)
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
			item_name
			FROM CELEBRAR_STORAGE
			WHERE item_id = ?
			AND isDeleted = 0
			""", (item_id,))

			row = cursor.fetchone()
			item_name = row[0] if row else f"ID {item_id}"
			raise ValueError(
				f"Estoque insuficiente para o item {item_name}"
			)

def validate_delivery_orders(orders, delivery_date, delivery_id=None):
	if not isinstance(orders, list) or not orders:
		raise ValueError("A entrega deve conter pelo menos um pedido")

	if not all(isinstance(order, int) and not isinstance(order, bool) for order in orders):
		raise ValueError("Pedido inválido")

	if len(set(orders)) != len(orders):
		raise ValueError("Pedido duplicado")

	placeholders = ", ".join("?" * len(orders))

	_, rows = run_select(f"""
	SELECT order_id
	FROM CELEBRAR_ORDERS
	WHERE isDeleted = 0
	AND isDelivery = 1
	AND (delivery_id IS NULL OR delivery_id = ?)
	AND order_status = ?
	AND delivery_date = ?
	AND order_id IN ({placeholders})
	""", (delivery_id, orderStatus.READY.name, delivery_date, *orders))

	valid_ids = {row[0] for row in rows}
	if valid_ids != set(orders):
		raise ValueError("Um ou mais pedidos não são válidos para entrega")

	return orders

# ---------------------------

OPEN_ORDERS_PLACEHOLDERS = ",".join("?" for _ in OPEN_ORDER_STATUS)
OPEN_DELIVERIES_PLACEHOLDERS = ",".join("?" for _ in OPEN_DELIVERY_STATUS)

def basket_has_open_orders(id):
	_, rows = run_select(f"""
	SELECT 1
	FROM CELEBRAR_ORDER_ITEMS oi
	JOIN CELEBRAR_ORDERS o
	ON o.order_id = oi.order_id
	WHERE oi.basket_id = ?
	AND o.isDeleted = 0
	AND o.order_status IN ({OPEN_ORDERS_PLACEHOLDERS}) 
	""", (id, *OPEN_ORDER_STATUS))

	return bool(rows)

def client_has_open_orders(id):
	_, rows = run_select(f"""
	SELECT 1
	FROM CELEBRAR_ORDERS
	WHERE client_id = ?
	AND isDeleted = 0
	AND order_status IN ({OPEN_ORDERS_PLACEHOLDERS}) 
	""", (id, *OPEN_ORDER_STATUS))

	return bool(rows)

def item_has_open_orders(id):
	_, rows = run_select(f"""
	SELECT 1
	FROM CELEBRAR_ORDER_ITEMS oi
	JOIN CELEBRAR_ORDERS o
	ON o.order_id = oi.order_id
	JOIN CELEBRAR_BASKET_ITEMS bi
	ON bi.basket_id = oi.basket_id
	AND bi.isDeleted = 0
	WHERE o.isDeleted = 0
	AND o.order_status IN ({OPEN_ORDERS_PLACEHOLDERS})
	AND (
		bi.item_id = ?
		OR EXISTS (
			SELECT 1
			FROM CELEBRAR_GROUP_MEMBERS m
			WHERE m.group_id = bi.group_id
			AND m.item_id = ?
			AND m.isDeleted = 0
		)
	)
	""", (*OPEN_ORDER_STATUS, id, id))

	return bool(rows)

def group_has_open_orders(id):
	_, rows = run_select(f"""
	SELECT 1
	FROM CELEBRAR_ORDER_ITEMS oi
	JOIN CELEBRAR_ORDERS o
	ON o.order_id = oi.order_id
	JOIN CELEBRAR_BASKET_ITEMS bi
	ON bi.basket_id = oi.basket_id
	WHERE bi.group_id = ?
	AND bi.isDeleted = 0
	AND o.isDeleted = 0
	AND o.order_status IN ({OPEN_ORDERS_PLACEHOLDERS})
	""", (id, *OPEN_ORDER_STATUS))

	return bool(rows)

def courier_has_open_deliveries(id):
	_, rows = run_select(f"""
	SELECT 1
	FROM CELEBRAR_COURIERS c
	JOIN CELEBRAR_DELIVERIES d
	ON d.courier_id = c.courier_id
	WHERE d.courier_id = ?
	AND d.isDeleted = 0
	AND c.isDeleted = 0
	AND d.delivery_status IN ({OPEN_DELIVERIES_PLACEHOLDERS})
	""", (id, *OPEN_DELIVERY_STATUS))

	return bool(rows)