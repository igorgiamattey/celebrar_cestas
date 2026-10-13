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
	toggleLoginButton(['login_id', 'password'], 'login-button')
});