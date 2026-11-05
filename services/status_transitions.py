from enums.delivery_status import DeliveryStatus
from enums.order_status import OrderStatus
from enums.financial_status import FinancialStatus

D_TRANSIT = DeliveryStatus.TRANSIT.name
D_CANCELLED = DeliveryStatus.CANCELLED.name
D_DELIVERED = DeliveryStatus.DELIVERED.name
D_PENDING = DeliveryStatus.PENDING.name

O_PENDING = OrderStatus.PENDING.name
O_CONFIRMED = OrderStatus.CONFIRMED.name
O_CANCELLED = OrderStatus.CANCELLED.name
O_DELIVERED = OrderStatus.DELIVERED.name
O_PREPARING = OrderStatus.PREPARING.name
O_READY = OrderStatus.READY.name

F_PENDING = FinancialStatus.PENDING.name
F_PAID = FinancialStatus.PAID.name
F_CANCELLED = FinancialStatus.CANCELLED.name

STATUS_TRANSITIONS_ORDERS = {
	O_PENDING: {O_PENDING, O_CONFIRMED, O_CANCELLED},
	O_CONFIRMED: {O_CONFIRMED, O_PREPARING, O_CANCELLED},
	O_PREPARING: {O_PREPARING, O_READY, O_CANCELLED},
	O_READY: {O_READY, O_DELIVERED, O_CANCELLED},
	O_DELIVERED: {O_DELIVERED},
	O_CANCELLED: {O_CANCELLED},
}

STATUS_TRANSITIONS_DELIVERIES = {
	D_PENDING: {D_PENDING, D_TRANSIT, D_CANCELLED},
	D_TRANSIT: {D_TRANSIT, D_DELIVERED, D_CANCELLED},
	D_DELIVERED: {D_DELIVERED},
	D_CANCELLED: {D_CANCELLED},
}

STATUS_TRANSITIONS_FINANCIALS = {
	F_PENDING: {F_PENDING, F_PAID, F_CANCELLED},
	F_PAID: {F_PAID},
	F_CANCELLED: {F_CANCELLED}
}

TRANSITIONS = {
	"ORDER": STATUS_TRANSITIONS_ORDERS,
	"DELIVERY": STATUS_TRANSITIONS_DELIVERIES,
	"FINANCIAL": STATUS_TRANSITIONS_FINANCIALS
}

def is_valid_transition(current, new, mode):
	return new in get_allowed_status(current, mode)

def get_allowed_status(status, mode):
	try:
		transitions = TRANSITIONS[mode]
	except KeyError:
		raise ValueError(f"Modo inválido: {mode}")
	
	return frozenset(transitions.get(status, ()))