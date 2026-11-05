from enum import Enum

class FinancialStatus(Enum):
	PENDING = "Pendente"
	PAID = "Pago"
	CANCELLED = "Cancelado"

DATE_REQUIRED_STATUSES = [
	FinancialStatus.PAID.name,
]