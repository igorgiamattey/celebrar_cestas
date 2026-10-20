from flask import render_template
from flask_wtf.csrf import CSRFError

def register_error_handlers(app):
	@app.errorhandler(CSRFError)
	def handle_csrf_error(e):
		return render_template("errors/csrf_error.html"), 400

	@app.errorhandler(404)
	def handle_not_found(e):
		return render_template("errors/404.html"), 404