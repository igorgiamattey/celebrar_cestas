async function handleResponse(response) {
	if (!response.ok)
		throw new Error(await response.text());

	window.location.reload();
}

function handleError(error) {
	alert(error.message);
}

function submitModal(id) {
	const form = document.getElementById(id);
	const formData = new FormData(form);

	fetch(form.action, {
		method: 'POST',
		body: formData
	})
		.then(handleResponse)
		.catch(handleError);
}

document.getElementById('search-icon').innerHTML = ICON_SEARCH;

const searchClear = document.getElementById('search-clear');
const searchInput = document.querySelector('.search-bar');

if (searchClear && searchInput) {
	searchClear.innerHTML = ICON_CLEAR_SEARCH;
	const wrapper = searchInput.closest('.search-wrapper');

	const finishClear = () => {
		searchInput.value = '';
		searchInput.dispatchEvent(new Event('input', {bubbles: true}));
		searchInput.focus();
	}

	searchClear.addEventListener('click', () => {
		if (wrapper.classList.contains('is-clearing')) return;

		if (matchMedia('(prefers-reduced-motion: reduce)').matches) {
			finishClear();
			return;
		}

		const cs = getComputedStyle(searchInput);
		const padL = parseFloat(cs.paddingLeft);
		const padR = parseFloat(cs.paddingRight);

		const ghost = document.createElement('span');
		ghost.className = 'search-ghost';
		ghost.setAttribute('aria-hidden', 'true');
		ghost.textContent = searchInput.value;
		ghost.style.font = cs.font;
		ghost.style.color = cs.color;
		ghost.style.left = (padL + parseFloat(cs.borderLeftWidth)) + 'px';
		ghost.style.maxWidth = (searchInput.clientWidth - padL - padR) + 'px';

		wrapper.appendChild(ghost);
		wrapper.classList.add('is-clearing');
		searchInput.readOnly = true;

		const g = ghost.getBoundingClientRect();
		const t = searchClear.querySelector('svg').getBoundingClientRect();
		const dx = (t.left + t.width/2) - (g.left + g.width/2);
		const dy = (t.top + t.height * 0.6) - (g.top + g.height/2);

		ghost.animate([
			{transform: 'translate(0, 0) scale(1)', opacity: 1},
			{opacity: 1, offset: 0.92},
			{transform: `translate(${dx}px, ${dy}px) scale(0.25)`, opacity: 0}
		], {
			duration: 800,
			delay: 100,
			easing: 'cubic-bezier(0.5, 0, 0.9, 0.6)',
			fill: 'forwards'
		}).onfinish = () => {
			ghost.remove();
			searchInput.readOnly = false;
			wrapper.classList.remove('is-clearing');
			finishClear();
		};
	});
}

function inputNumber(input) {
	input.value = input.value.replace(/[^0-9.,]/g, '');
}

function inputPhone(input) {
	input.value = input.value.replace(/[^0-9+() -]/g, '');
}