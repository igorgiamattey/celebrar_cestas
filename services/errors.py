class StaleDataError(ValueError):
	"""
	The record was changed by someone else after the user opened it.

	Routes answer with HTTP 409 so the front-end shows a warning snackbar.
	"""