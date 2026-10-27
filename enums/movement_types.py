from enum import Enum

class storageMovementTypes(Enum):
	DECREASE = "Saída"
	INCREASE = "Entrada"
	DECREASE_ORDER = "Saída (Pedido)"
	INCREASE_ORDER = "Entrada (Pedido)"

class financialMovementTypes(Enum):
	EXPENSE = "Saída"
	INCOME = "Entrada"

class financialMovementCategories(Enum):
	ORDER_PAYMENT = "Pagamento de pedido"
	MARKET = "Compras"
	OTHER = "Outros"
	REFUND = "Estorno"

CAT_BY_TYPE = {
	financialMovementTypes.INCOME.name: [
		financialMovementCategories.ORDER_PAYMENT,
		financialMovementCategories.REFUND,
		financialMovementCategories.OTHER
	],
	financialMovementTypes.EXPENSE.name: [
		financialMovementCategories.MARKET,
		financialMovementCategories.REFUND,
		financialMovementCategories.OTHER
	]
}