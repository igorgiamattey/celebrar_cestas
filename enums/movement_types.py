from enum import Enum

class StorageMovementTypes(Enum):
	DECREASE = "Saída"
	INCREASE = "Entrada"
	DECREASE_ORDER = "Saída (Pedido)"
	INCREASE_ORDER = "Entrada (Pedido)"

class FinancialMovementTypes(Enum):
	EXPENSE = "Saída"
	INCOME = "Entrada"

class FinancialMovementCategories(Enum):
	ORDER_PAYMENT = "Pagamento de pedido"
	MARKET = "Compras"
	OTHER = "Outros"
	REFUND = "Estorno"

CAT_BY_TYPE = {
	FinancialMovementTypes.INCOME.name: [
		FinancialMovementCategories.ORDER_PAYMENT,
		FinancialMovementCategories.REFUND,
		FinancialMovementCategories.OTHER
	],
	FinancialMovementTypes.EXPENSE.name: [
		FinancialMovementCategories.MARKET,
		FinancialMovementCategories.REFUND,
		FinancialMovementCategories.OTHER
	]
}