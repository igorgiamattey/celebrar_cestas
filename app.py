import os

from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, request, session, url_for
from flask_wtf.csrf import CSRFProtect

from error_handlers import register_error_handlers
from routes.auth import auth_bp
from routes.catalogue import catalogue_bp
from routes.clients import clients_bp
from routes.deliveries import deliveries_bp
from routes.financial import financial_bp
from routes.home import home_bp
from routes.orders import orders_bp
from routes.storage import storage_bp

load_dotenv()
app = Flask(__name__)

APP_ENV = os.getenv("APP_ENV", "development").lower()
IS_PROD = APP_ENV == "production"

app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")

if not app.config["SECRET_KEY"]:
	raise RuntimeError("FLASK_SECRET_KEY não está definida no arquivo .env")

CSRFProtect(app)

app.register_blueprint(auth_bp)
app.register_blueprint(catalogue_bp)
app.register_blueprint(clients_bp)
app.register_blueprint(deliveries_bp)
app.register_blueprint(financial_bp)
app.register_blueprint(home_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(storage_bp)

PUBLIC_ENDPOINTS = {
	"auth_bp.login",
	"static"
}

app.config.update(
	SESSION_COOKIE_HTTPONLY=True,
	SESSION_COOKIE_SAMESITE="Lax",
	SESSION_COOKIE_SECURE=IS_PROD
)

@app.route("/health")
def health_check():
	return jsonify(status="ok"), 200

register_error_handlers(app)

def is_navigation():
	mode = request.headers.get("Sec-Fetch-Mode")
	
	if mode is not None:
		return mode == "navigate"
	
	return request.accept_mimetypes.accept_html and (
		request.accept_mimetypes["text/html"] >= request.accept_mimetypes["application/json"]
	)

@app.before_request
def require_login():
	if request.endpoint is None:
		return

	if request.endpoint in PUBLIC_ENDPOINTS:
		return

	if "user_id" not in session:
		if not is_navigation():
			return jsonify(error="Sessão expirada. Faça login novamente."), 401
		
		flash("Sua sessão expirou. Faça login novamente.", "warning")
		return redirect(url_for("auth_bp.login"))

if __name__ == "__main__":
	app.run(debug=not IS_PROD)