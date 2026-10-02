import pyodbc
import os
from dotenv import load_dotenv
from datetime import datetime
from contextlib import contextmanager

load_dotenv()

def get_connection():
	conn_str = (
		f"DRIVER={{{os.environ['DB_DRIVER']}}};"
		f"SERVER={os.environ['DB_SERVER']};"
		f"PORT={os.environ['DB_PORT']};"
		f"DATABASE={os.environ['DB_NAME']};"
		f"UID={os.environ['DB_USER']};"
		f"PWD={os.environ['DB_PASSWORD']};"
		"TDS_Version=7.4;"
	)

	try:
		connection = pyodbc.connect(conn_str)
		return connection
	except pyodbc.Error as e:
		print("Failed:", e)
		return None

def run_select(query, params=None):
	conn = get_connection()

	if conn is None:
		raise ConnectionError("Não foi possível fazer conexão com o banco de dados.")

	try:
		cursor = conn.cursor()
		cursor.execute(query, params or ())
		columns = [col[0] for col in cursor.description]
		rows = cursor.fetchall()
		return columns, rows
	finally:
		conn.close()

def run_update(query, params=None):
	conn = get_connection()

	if conn is None:
		raise ConnectionError("Não foi possível fazer conexão com o banco de dados.")

	try:
		cursor = conn.cursor()
		cursor.execute(query, params or ())
		conn.commit()
	finally:
		conn.close()

def format_currency(value):
	currency = f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
	return currency

def parse_price(value):
	value = value.strip().replace(",", ".")
	try:
		return float(value)
	except ValueError:
		raise ValueError(f"Invalid price value: {value}")

def format_date(value):
	if value is None:
		return '---'
	if isinstance(value, str):
		value = datetime.strptime(value, "%Y-%m-%d")
	return value.strftime("%d/%m/%Y")

@contextmanager
def run_transaction():
	conn = get_connection()

	if conn is None:
		raise ConnectionError("Não foi possível fazer conexão com o banco de dados.")
	
	try:
		cursor = conn.cursor()
		yield cursor
		conn.commit()
	except:
		conn.rollback()
		raise
	finally:
		conn.close()