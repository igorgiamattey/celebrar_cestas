function getModalIds() {
	return [...document.querySelectorAll('.modal-overlay')].map(el => el.id);
}

function closeModal(modalId) {
	document.getElementById(modalId).style.display = "none";
}

function toggleSaveButton(fieldIds, buttonId, arrayIds = []) {
	const button = document.getElementById(buttonId)

	const allFieldsFilled = fieldIds.every(fieldId => {
		const field = document.getElementById(fieldId);
		return field.value.trim() !== "";
	});

	const arraysFilled = arrayIds.every(array => array.length > 0);

	button.disabled = !(allFieldsFilled && arraysFilled);
	button.title = allFieldsFilled
					? (arraysFilled
						? ""
						: "Adicione pelo menos um item na lista."
					)
					: "Preencha os campos obrigatórios!";
}

function autoGrow(text) {
	text.style.height = "auto";
	text.style.height = text.scrollHeight + "px";
}

document.addEventListener('keydown', (e) => {
	if (e.key !== 'Escape') return;
	getModalIds().forEach(id => {
		const modal = document.getElementById(id);
		if (modal && modal.style.display === 'flex') closeModal(id);
	});
});

getModalIds().forEach(id => {
	const modal = document.getElementById(id);
	if (modal) {
		modal.addEventListener('click', (e) => {
			if (e.target.id === id) closeModal(id);
		});
	}
});