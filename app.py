from flask import Flask
# from werkzeug.middleware.dispatcher import DispatcherMiddleware
# from werkzeug.exceptions import NotFound

from routes.catalogue import catalogue_bp
from routes.clients import clients_bp
from routes.deliveries import deliveries_bp
from routes.financial import financial_bp
from routes.home import home_bp
from routes.orders import orders_bp
from routes.storage import storage_bp

# flask_app = Flask(__name__)
app = Flask(__name__)

app.register_blueprint(catalogue_bp)
app.register_blueprint(clients_bp)
app.register_blueprint(deliveries_bp)
app.register_blueprint(financial_bp)
app.register_blueprint(home_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(storage_bp)

# flask_app.register_blueprint(catalogue_bp)
# flask_app.register_blueprint(clients_bp)
# flask_app.register_blueprint(deliveries_bp)
# flask_app.register_blueprint(financial_bp)
# flask_app.register_blueprint(home_bp)
# flask_app.register_blueprint(orders_bp)
# flask_app.register_blueprint(storage_bp)

# app = DispatcherMiddleware(NotFound(), {
# 	'/python': flask_app
# })

if __name__ == "__main__":
	# from werkzeug.serving import run_simple
	# run_simple('127.0.0.1', 5000, app, use_reloader=True, use_debugger=True)
	app.run(debug=True)