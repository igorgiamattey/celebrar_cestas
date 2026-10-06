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

document.addEventListener('keydown', (e) => {
	if (e.key !== 'Escape')
		return;

	const visibleIds = getModalIds().filter(id => {
		const modal = document.getElementById(id);
		return modal && modal.style.display === 'flex';
	});

	if (visibleIds.length === 0)
		return;

	const topId = visibleIds[visibleIds.length - 1];
	closeModal(topId);

	if (topId === 'deliveryOrder-modal') {
		cancelDeliveryDetails('new');
		cancelDeliveryDetails('view');
	}
});

getModalIds().forEach(id => {
	const modal = document.getElementById(id);
	if (modal) {
		modal.addEventListener('click', (e) => {
			if (e.target.id === id) {
				if (id === 'deliveryOrder-modal') {
					cancelDeliveryDetails('new');
					cancelDeliveryDetails('view');
				}
				else {
					closeModal(id);
				}
			}
		});
	}
});