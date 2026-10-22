(function () {
	const DURATIONS = { success: 4000, info: 4000, warning: 6000, error: 8000};
	const MAX_VISIBLE = 4;

	const ICONS = {
		success: SUCCESS_ICON,
		warning: WARNING_ICON,
		error: ERROR_ICON,
		info: INFO_ICON
	};

	function getContainer() {
		let el = document.getElementById('snackbar-container');
		if (!el) {
			el = document.createElement('div');
			el.id = 'snackbar-container';
			el.className = 'snackbar-container';
			document.body.appendChild(el);
		}
		return el;
	}

	function dismiss(el) {
		if (el.dataset.leaving)
			return;

		el.dataset.leaving = '1';
		el.classList.add('leaving');
		setTimeout(() => el.remove(), 200);
	}

	window.showSnackbar = function (message, type = 'info', opts = {}) {
		if (!ICONS[type]) type = 'info';

		const container = getContainer();
		while (container.children.length >= MAX_VISIBLE)
			container.firstElementChild.remove();

		const el = document.createElement('div');
		el.className = `snackbar ${type}`;
		el.setAttribute('role', type === 'error' || type === 'warning' ? 'alert' : 'status');

		const icon = document.createElement('span');
		icon.className = 'snackbar-icon';
		icon.innerHTML = ICONS[type];

		const text = document.createElement('span');
		text.className = 'snackbar-message';
		text.textContent = message;

		const close = document.createElement('button');
		close.type = 'button';
		close.className = 'snackbar-close';
		close.setAttribute('aria-label', 'Fechar');
		close.innerHTML = '&times;';
		close.addEventListener('click', () => dismiss(el));

		el.append(icon, text, close);
		container.appendChild(el);

		const duration = opts.duration ?? DURATIONS[type];
		if (duration > 0) {
			let timer = setTimeout(() => dismiss(el), duration);
			el.addEventListener('mouseenter', () => clearTimeout(timer));
			el.addEventListener('mouseleave', () => {
				timer = setTimeout(() => dismiss(el), 2000);
			});
		}
	
		return el;
	
	};

	document.addEventListener('DOMContentLoaded', function () {
		const holder = document.getElementById('flash-data');
		if (!holder) return;

		JSON.parse(holder.dataset.messages).forEach(function (m) {
			window.showSnackbar(m[1], m[0]);
		});
	});

})();