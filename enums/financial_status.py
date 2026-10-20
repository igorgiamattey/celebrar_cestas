from enum import Enum

class financialStatus(Enum):
	PENDING = "Pendente"
	PAID = "Pago"
	CANCELLED = "Cancelado"

DATE_REQUIRED_STATUSES = [
	financialStatus.PAID.name,
]