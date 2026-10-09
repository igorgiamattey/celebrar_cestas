from datetime import date, timedelta

from flask import Blueprint, jsonify, render_template, request

from db import format_date, run_select
from enums.order_status import orderStatus
from services.home_service import getCloseOrders, getMissingItems, getLateOrders
from services.routes_service import (getAvailableBaskets, getAvailableClients,
                                     getAvailableGroups, getAvailableItems,
                                     getAvailableOrderStatus)

home_bp = Blueprint("home_bp", __name__)

@home_bp.route("/")
def home(): 
	page = request.args.get("page", 1, type=int)
	page = max(page, 1)
	per_page = 3
	
	where_clause = """
		WHERE p.isDeleted = 0
		AND p.status_pedido NOT IN ('DELIVERED', 'CANCELLED')
	"""

	_, count_rows = run_select(f"""
	SELECT COUNT(*)
	FROM IGOR_CG_PEDIDOS p
	JOIN IGOR_CG_CLIENTES c
	ON p.id_cliente = c.id_cliente
	{where_clause}
	""",)

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
	p.valor_pedido AS Valor,
	p.status_pedido AS Status
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
	""", (offset, per_page))

	columns = [
		columns[3],
		columns[2],
		columns[5]
	]

	today = date.today()
	limit_date = today + timedelta(days=5)

	rows = [
		{
			"id": row[0],
			"delivery": format_date(row[3]),
			"items": row[2],
			"status": orderStatus[row[5]].value,
			"warning": row[3] is not None and today <= row[3] <= limit_date and orderStatus[row[5]].name not in ("DELIVERED", "CANCELLED"),
			"late": row[3] is not None and today > row[3] and orderStatus[row[5]].name not in ("DELIVERED", "CANCELLED")
		}
		for row in rows
	]

	finances = {
		"receivables": "R$ 1.580,00",
		"delivery_fee": "R$ 120,00",
		"invoicing": "R$ 1.700,00",
	}

	available_items = getAvailableItems()
	available_groups = getAvailableGroups()
	available_clients = getAvailableClients()
	available_baskets = getAvailableBaskets()
	statuses = getAvailableOrderStatus()

	missing_items = getMissingItems()
	close_orders = getCloseOrders()
	late_orders = getLateOrders()

	return render_template("home/home.html",
						rows=rows,
						columns=columns,
						page=page,
						total_pages=total_pages,
						finances=finances,
						user="Vendedor",
						available_items=available_items,
						available_groups=available_groups,
						available_clients=available_clients,
						available_baskets=available_baskets,
						statuses=statuses,
						missing_items=missing_items,
						close_orders=close_orders,
						late_orders=late_orders)

@home_bp.route("/home/<int:id>/items")
def order_items(id):
	_, rows = run_select(f"""
	SELECT
	cp.quantidade, pr.nome_cesta
	FROM IGOR_CG_CESTAS_PEDIDO cp
	JOIN IGOR_CG_PRODUTOS pr
	ON pr.id_produto = cp.id_produto
	WHERE cp.id_pedido = ?
	AND pr.isDeleted = 0
	ORDER BY pr.nome_cesta
	""", (id,))

	items = [
		{
			"quantity": row[0],
			"name": row[1]
		}
		for row in rows
	]

	return jsonify({"items": items})