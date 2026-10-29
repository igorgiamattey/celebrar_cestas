function toggleLoginButton(fieldIds, buttonId) {
	const button = document.getElementById(buttonId)

	const allFieldsFilled = fieldIds.every(fieldId => {
		const field = document.getElementById(fieldId);
		return field.value.trim() !== "";
	});

	button.disabled = !(allFieldsFilled);
	button.title = allFieldsFilled
					? ""
					: "Preencha todos os campos";
}

document.addEventListener('DOMContentLoaded', () => {
	const input = document.getElementById('password');
	setPasswordVisible(false);

	document.getElementById('toggle-password').addEventListener('click', () => {
		setPasswordVisible(input.type === 'password');
		input.focus();
	});
	
	toggleLoginButton(['login_id', 'password'], 'login-button')
});

function setPasswordVisible(visible) {
	const input = document.getElementById('password');
	const button = document.getElementById('toggle-password');

	input.type = visible ? 'text' : 'password';
	button.innerHTML = visible ? ICON_HIDE_PWD : ICON_SHOW_PWD;
	button.title = visible ? 'Ocultar senha' : 'Mostrar senha';
}