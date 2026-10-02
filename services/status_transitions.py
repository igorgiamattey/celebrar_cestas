from enums.order_status import orderStatus

pending = orderStatus.PENDING.name
confirmed = orderStatus.CONFIRMED.name
cancelled = orderStatus.CANCELLED.name
delivered = orderStatus.DELIVERED.name
preparing = orderStatus.PREPARING.name
ready = orderStatus.READY.name


STATUS_TRANSITIONS = {
	pending: {pending, confirmed, cancelled},
	confirmed: {confirmed, preparing, cancelled},
	preparing: {preparing, ready, cancelled},
	ready: {ready, delivered, cancelled},
	delivered: {delivered},
	cancelled: {cancelled},
}

def is_valid_transition(current, new):
	return new in STATUS_TRANSITIONS.get(current, set())

def get_allowed_status(status):
	return STATUS_TRANSITIONS.get(status, set())