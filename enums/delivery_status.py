from enum import Enum

class DeliveryStatus(Enum):
	CANCELLED = "Cancelada"
	PENDING = "Pendente"
	TRANSIT = "Em trânsito"
	DELIVERED = "Entregue"

OPEN_DELIVERY_STATUS = (
	DeliveryStatus.PENDING.name,
	DeliveryStatus.TRANSIT.name,
)