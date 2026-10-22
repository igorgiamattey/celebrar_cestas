let confirmResolve = null;

function openConfirm(title, msg) {
	if (confirmResolve) confirmResolve(false);

	const titleEl = document.getElementById('confirm-title');
	const msgEl = document.getElementById('confirm-message');
	
	titleEl.textContent = title;
	msgEl.textContent = msg;

	document.getElementById('confirm-modal').style.display = "flex";
	document.getElementById('confirm-cancel').focus();

	return new Promise((resolve) => {
		confirmResolve = resolve;
	});
}

function confirmChoice(result) {
	document.getElementById('confirm-modal').style.display = 'none';
	if (confirmResolve) {
		confirmResolve(result);
		confirmResolve = null;
	}
}

document.getElementById('confirm-modal').addEventListener('click', (e) => {
	if (e.target === e.currentTarget) confirmChoice(false);
});

document.addEventListener('keydown', (e) => {
	const modal = document.getElementById('confirm-modal');
	if (e.key === 'Escape' && modal.style.display !== 'none') {
		e.stopImmediatePropagation();
		confirmChoice(false);
	}
}, true);