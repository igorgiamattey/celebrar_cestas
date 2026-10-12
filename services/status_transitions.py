from enums.delivery_status import deliveryStatus
from enums.order_status import orderStatus

d_transit = deliveryStatus.TRANSIT.name
d_cancelled = deliveryStatus.CANCELLED.name
d_delivered = deliveryStatus.DELIVERED.name
d_pending = deliveryStatus.PENDING.name

o_pending = orderStatus.PENDING.name
o_confirmed = orderStatus.CONFIRMED.name
o_cancelled = orderStatus.CANCELLED.name
o_delivered = orderStatus.DELIVERED.name
o_preparing = orderStatus.PREPARING.name
o_ready = orderStatus.READY.name

STATUS_TRANSITIONS_ORDERS = {
	o_pending: {o_pending, o_confirmed, o_cancelled},
	o_confirmed: {o_confirmed, o_preparing, o_cancelled},
	o_preparing: {o_preparing, o_ready, o_cancelled},
	o_ready: {o_ready, o_delivered, o_cancelled},
	o_delivered: {o_delivered},
	o_cancelled: {o_cancelled},
}

STATUS_TRANSITIONS_DELIVERIES = {
	d_pending: {d_pending, d_transit, d_cancelled},
	d_transit: {d_transit, d_delivered, d_cancelled},
	d_delivered: {d_delivered},
	d_cancelled: {d_cancelled},
}

TRANSITIONS = {
	"ORDER": STATUS_TRANSITIONS_ORDERS,
	"DELIVERY": STATUS_TRANSITIONS_DELIVERIES
}

def is_valid_transition(current, new, mode):
	return new in get_allowed_status(current, mode)

def get_allowed_status(status, mode):
	try:
		transitions = TRANSITIONS[mode]
	except KeyError:
		raise ValueError(f"Modo inválido: {mode}")
	
	return frozenset(transitions.get(status, ()))