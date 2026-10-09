from enum import Enum

class deliveryStatus(Enum):
	CANCELLED = "Cancelada"
	PENDING = "Pendente"
	TRANSIT = "Em trânsito"
	DELIVERED = "Entregue"