from enum import Enum

class OrderStatus(Enum):
	CANCELLED = "Cancelado"
	CONFIRMED = "Confirmado"
	DELIVERED = "Entregue"
	PENDING = "Pagamento pendente"
	PREPARING = "Em preparação"
	READY = "Pronto"

OPEN_ORDER_STATUS = (
	OrderStatus.PENDING.name,
	OrderStatus.CONFIRMED.name,
	OrderStatus.PREPARING.name,
	OrderStatus.READY.name,
)

CLOSED_ORDER_STATUS = (
	OrderStatus.CANCELLED.name,
	OrderStatus.DELIVERED.name
)