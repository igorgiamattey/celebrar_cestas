from enum import Enum

class orderStatus(Enum):
	CANCELLED = "Cancelado"
	CONFIRMED = "Confirmado"
	DELIVERED = "Entregue"
	PENDING = "Pagamento pendente"
	PREPARING = "Em preparação"
	READY = "Pronto"