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

document.addEventListener("DOMContentLoaded", () => {
	const toggle = document.querySelector(".user-menu-toggle");
	const dropdown = document.getElementById("user-dropdown");

	if (!toggle || !dropdown) return;

	function closeDropdown() {
		dropdown.classList.remove("show");
		toggle.setAttribute("aria-expanded", "false");
	}

	toggle.addEventListener("click", (event) => {
		event.stopPropagation();

		const isOpen = dropdown.classList.toggle("show");
		toggle.setAttribute("aria-expanded", String(isOpen));
	});

	document.addEventListener("click", (event) => {
		if (!event.target.closest(".user-menu")) {
			closeDropdown();
		}
	});

	document.addEventListener("keydown", (event) => {
		if (event.key === "Escape") {
			closeDropdown();
			toggle.focus();
		}
	});
});

const search_icon = document.getElementById('search-icon')
if (search_icon)
	search_icon.innerHTML = ICON_SEARCH;

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
	let v = input.value.replace(/[^0-9.,]/g, '');
	const i = v.search(/[.,]/);

	if (i !== -1) {
		const int = v.slice(0, i) || '0';
		const dec = v.slice(i+1).replace(/[.,]/g,'').slice(0, 5);
		v = int + v[i] + dec;
	}
	input.value = v;
}

function inputPrice(input) {
	let v = input.value.replace(/[^0-9.,]/g, '');
	const i = v.search(/[.,]/);

	if (i !== -1) {
		const int = v.slice(0, i) || '0';
		const dec = v.slice(i+1).replace(/[.,]/g,'').slice(0, 2);
		v = int + v[i] + dec;
	}
	input.value = v;
}

function inputInt(input) {
	input.value = input.value.replace(/\D/g, '');
}

function inputPhone(input) {
	input.value = input.value.replace(/[^0-9+() -]/g, '');
}

function inputUserMail(input) {
	input.value = input.value.replace(/[^A-Za-z0-9._@+-]/g, '')
}

const noResults = text => ({
	no_results: () => `<div class="no-results">${text}</div>`
});