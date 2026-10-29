from flask import (Blueprint, jsonify, redirect, render_template, request,
                   session, url_for)

from db import run_select, run_transaction
from enums.financial_status import financialStatus
from enums.movement_types import (financialMovementCategories,
                                  financialMovementTypes)
from enums.table_names import Table
from services.errors import StaleDataError
from services.financial_service import (get_balance, get_financial,
                                        get_monthly_statement, get_order_total)
from services.order_service import get_today
from services.routes_service import (getAvailableFinancialCategoriesByType,
                                     getAvailableFinancialStatus,
                                     getAvailableFinancialTypes,
                                     getAvailableMonths,
                                     getAvailableOrdersFinancial)
from services.status_transitions import get_allowed_status
from services.validate_service import (validate_financial_category,
                                       validate_financial_status,
                                       validate_financial_type, validate_id,
                                       validate_name, validate_opt_text,
                                       validate_pay_date, validate_price,
                                       validate_status_transition)

financial_bp = Blueprint("financial_bp", __name__)
financial_mode = "FINANCIAL"

@financial_bp.route("/financeiro")
def financial():
	columns, rows, page, total_pages, search = get_financial()

	available_orders = getAvailableOrdersFinancial()
	statuses = getAvailableFinancialStatus()
	available_types = getAvailableFinancialTypes()
	cat_by_type = getAvailableFinancialCategoriesByType()
	available_months = getAvailableMonths()
	balance_values = get_balance()
	statement_rows = get_monthly_statement()

	return render_template("financial/financial.html",
						columns=columns,
						rows=rows,
						page=page,
						total_pages=total_pages,
						search=search,
						user=session.get("username"),
						available_types=available_types,
						available_categories=cat_by_type,
						available_orders=available_orders,
						available_months=available_months,
						financial_statuses=statuses,
						balance_values=balance_values,
						statement_rows=statement_rows,
						today=get_today())

@financial_bp.route("/search_financial")
def financial_search():
	columns, rows, _, _, search = get_financial()

	return render_template("financial/_financial_table_rows.html",
							columns=columns,
							rows=rows,
							search=search)

@financial_bp.route("/new_financial", methods=["POST"])
def new_financial():
	try:
		fin_type = validate_financial_type(request.form["type"])
		category = validate_financial_category(request.form["category"], fin_type)
		status = validate_financial_status(request.form["status"])
		value = validate_price(request.form["value"])
		pay_date = validate_pay_date(request.form.get("date"), status)

		order_id = None
		supplier = None

		if category == financialMovementCategories.ORDER_PAYMENT.name:
			order_id = request.form.get("order", type=int)
			if order_id is None:
				return "Pedido inválido", 400
			value = get_order_total(order_id)

		elif category == financialMovementCategories.MARKET.name:
			supplier = validate_name(request.form.get("supplier"))

		backup_desc = str(financialMovementCategories[category].value)
		if order_id:
			backup_desc += f" [Pedido #{order_id}]"
		elif supplier:
			backup_desc += f" [{supplier}]"
		
		description = (
			validate_opt_text(request.form.get("description"), "Descrição", 150)
			or backup_desc
		)

		with run_transaction() as cursor:
			cursor.execute("""
			INSERT INTO CELEBRAR_FINANCIAL_PAYMENTS
			(order_id, payment_type, payment_description, payment_value, payment_date,
			payment_status, supplier, payment_category)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?)
			""", (
				order_id, fin_type, description,
				value, pay_date, status, supplier, category
			))

	except KeyError:
		return "Dados do lançamento inválidos", 400
	except ValueError as e:
		return str(e), 400
	
	return redirect(request.referrer or url_for("financial_bp.financial"))

@financial_bp.route("/financial_data/<int:id>")
def financial_data(id):
	columns, rows = run_select("""
	SELECT
	payment_id, order_id, payment_type, payment_description, payment_value, payment_date,
	payment_status, supplier, payment_category
	FROM CELEBRAR_FINANCIAL_PAYMENTS
	WHERE payment_id = ? AND isDeleted = 0
	""", (id,))

	if not rows:
		return jsonify({"error": "Financial not found"}), 404

	row = rows[0]
	financial = dict(zip(columns, row))

	pay_date = financial["payment_date"]
	financial["payment_date"] = pay_date.strftime("%Y-%m-%d") if pay_date else ""
	financial["payment_value"] = str(financial["payment_value"])

	financial["allowed_status"] = sorted(get_allowed_status(financial["payment_status"], financial_mode))

	_, refund_rows = run_select("""
	SELECT 1
	FROM CELEBRAR_FINANCIAL_PAYMENTS
	WHERE origin_payment_id = ?
	AND isDeleted = 0
	""", (id,))
	financial["refunded"] = bool(refund_rows)
	
	return jsonify(financial)

@financial_bp.route("/update_financial", methods=["POST"])
def update_financial():
	try:
		id = request.form.get("id", type=int)
		if not validate_id(Table.Financial, "payment_id", id):
			raise ValueError("Lançamento inválido")
		
		_, data_rows = run_select("""
		SELECT
		order_id, payment_type, payment_value, payment_date,
		payment_status, supplier, payment_category
		FROM CELEBRAR_FINANCIAL_PAYMENTS
		WHERE payment_id = ? AND isDeleted = 0
		""", (id,))
	
		if not data_rows:
			return "Lançamento não encontrado.", 404

		current_order = data_rows[0][0]
		current_type = data_rows[0][1]
		current_value = data_rows[0][2]
		current_date = data_rows[0][3]
		current_status = data_rows[0][4]
		current_supplier = data_rows[0][5]
		current_category = data_rows[0][6]
			

		if current_status == financialStatus.CANCELLED.name:
			return "Um lançamento cancelado não pode ser alterado.", 400
		
		if current_status == financialStatus.PENDING.name:
			fin_type = validate_financial_type(request.form["type"])
			category = validate_financial_category(request.form["category"], fin_type)
			status = validate_financial_status(request.form["status"])
			value = validate_price(request.form["value"])
			pay_date = validate_pay_date(request.form.get("date"), status)
			validate_status_transition(current_status, status, financial_mode)

			order_id = None
			supplier = None

			if category == financialMovementCategories.ORDER_PAYMENT.name:
				order_id = request.form.get("order", type=int)
				if order_id is None:
					return "Pedido inválido", 400
				value = get_order_total(order_id)

			elif category == financialMovementCategories.MARKET.name:
				supplier = validate_name(request.form.get("supplier"))

		else:
			fin_type = current_type
			category = current_category
			status = current_status
			value = current_value
			pay_date = current_date
			order_id = current_order
			supplier = current_supplier
		
		backup_desc = str(financialMovementCategories[category].value)
		if order_id:
			backup_desc += f" [Pedido #{order_id}]"
		elif supplier:
			backup_desc += f" [{supplier}]"
		
		description = (
			validate_opt_text(request.form.get("description"), "Descrição", 150)
			or backup_desc
		)

		with run_transaction() as cursor:
			cursor.execute("""
			UPDATE CELEBRAR_FINANCIAL_PAYMENTS
			SET
			order_id = ?,
			payment_type = ?,
			payment_description = ?,
			payment_value = ?,
			payment_date = ?,
			payment_status = ?,
			supplier = ?,
			payment_category = ?
			WHERE payment_id = ?
			AND isDeleted = 0
			AND payment_status = ?
			""", (
				order_id, fin_type, description,
				value, pay_date, status, supplier, category, id, current_status
			))

			if cursor.rowcount != 1:
				raise StaleDataError("Este lançamento já foi alterado")
		
	except KeyError:
		return "Dados do lançamento inválidos", 400
	except StaleDataError as e:
		return str(e), 409
	except ValueError as e:
		return str(e), 400

	return redirect(request.referrer or url_for("financial_bp.financial"))

@financial_bp.route("/refund/<int:id>", methods=["POST"])
def refund_financial(id):
	try:
		with run_transaction() as cursor:
			cursor.execute("""
			SELECT
			order_id, payment_type, payment_value, payment_category, supplier
			FROM CELEBRAR_FINANCIAL_PAYMENTS
			WHERE payment_id = ?
			and isDeleted = 0
			AND payment_status = ?
			AND payment_category <> ?
			AND origin_payment_id IS NULL
			""", (id, financialStatus.PAID.name, financialMovementCategories.REFUND.name))
			
			original = cursor.fetchone()
			
			if not original:
				raise ValueError("Apenas lançamentos pagos podem ser estornados")

			cursor.execute("""
			SELECT 1
			FROM CELEBRAR_FINANCIAL_PAYMENTS
			WHERE origin_payment_id = ?
			AND isDeleted = 0
			""", (id,))

			if cursor.fetchone():
				raise StaleDataError("Esse lançamento já foi estornado")

			order_id, fin_type, value, _, supplier = original
			opposite = (financialMovementTypes.EXPENSE.name
			            if fin_type == financialMovementTypes.INCOME.name
						else financialMovementTypes.INCOME.name)

			desc = f"Estorno do lançamento #{id}"
			if order_id:
				desc += f" - Pedido #{order_id}"
			elif supplier:
				desc += f" - {supplier}"
			
			cursor.execute("""
			INSERT INTO CELEBRAR_FINANCIAL_PAYMENTS
			(order_id, payment_type, payment_description, payment_value, payment_date,
			payment_status, supplier, payment_category, origin_payment_id)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
			""", (order_id, opposite, desc, value,
			      get_today(), financialStatus.PAID.name, supplier, financialMovementCategories.REFUND.name, id))

	except StaleDataError as e:
		return str(e), 409
	except ValueError as e:
		return str(e), 400
	
	return redirect(request.referrer or url_for("financial_bp.financial"))