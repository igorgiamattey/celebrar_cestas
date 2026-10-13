import re

def validate_loginId(key):
	valid_chars = re.compile(r'^[A-Za-z0-9._@+-]+$')
	email_pattern = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
	user_pattern = re.compile(r'^(?!.*[._-]{2})[A-Za-z0-9](?:[A-Za-z0-9._-]{1,28}[A-Za-z0-9])$')

	if not isinstance(key, str):
		raise ValueError("Email/usuário inválido")
	
	key = key.strip().lower()
	
	if not key:
		raise ValueError("Preencha o email/usuário")
	
	if len(key) > 100:
		raise ValueError("Email/usuário muito longo")
	
	if len(key) < 3:
			raise ValueError("Email/usuário muito curto")

	if not valid_chars.fullmatch(key):
		raise ValueError("Email/usuário com caracteres inválidos")

	valid_email = email_pattern.fullmatch(key)
	valid_user = user_pattern.fullmatch(key)

	if not valid_email and not valid_user:
		raise ValueError("Email/usuário inválido")

	return key

def validate_password(pwd):
	if not isinstance(pwd, str):
		raise ValueError("Senha inválida")

	if not pwd.strip():
		raise ValueError("Preencha a senha")
	
	if len(pwd) < 8:
		raise ValueError("Senha deve possuir pelo menos 8 caracteres")

	if len(pwd) > 128:
			raise ValueError("Senha deve possuir no máximo 128 caracteres")
	
	return pwd
