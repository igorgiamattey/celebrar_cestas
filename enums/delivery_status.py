from enum import Enum

class deliveryStatus(Enum):
	CANCELLED = "Cancelada"
	PENDING = "Pendente"
	TRANSIT = "Em trânsito"
	DELIVERED = "Entregue"

OPEN_DELIVERY_STATUS = (
	deliveryStatus.PENDING.name,
	deliveryStatus.TRANSIT.name,
)