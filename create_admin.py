from getpass import getpass
from werkzeug.security import generate_password_hash

from db import run_transaction

def create_admin():
	username = input("Username: ").strip()
	email = input("Email: ").strip().lower()
	password = getpass("Password: ")
	confirm = getpass("Confirm: ")

	if not username or not email or not password:
		print("All fields are required.")
		return

	if password != confirm:
		print("Passwords do not match.")
		return

	hash = generate_password_hash(password)

	query = """
	INSERT INTO CELEBRAR_USERS
	(username, user_email, hash_pwd)
	OUTPUT INSERTED.user_id
	VALUES (?, ?, ?)
	"""

	try:
		with run_transaction() as cursor:
			cursor.execute(query, (username, email, hash))
			user_id = cursor.fetchone()[0]

		print(f"User created. ID: {user_id}")

	except Exception as error:
		print(f"Could not create user: {error}")

if __name__ == "__main__":
	create_admin()