from enum import Enum

class orderStatus(Enum):
	CANCELLED = "Cancelado"
	CONFIRMED = "Confirmado"
	DELIVERED = "Entregue"
	PENDING = "Pagamento pendente"
	PREPARING = "Em preparação"
	READY = "Pronto"

OPEN_ORDER_STATUS = (
	orderStatus.PENDING.name,
	orderStatus.CONFIRMED.name,
	orderStatus.PREPARING.name,
	orderStatus.READY.name,
)