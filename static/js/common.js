const GENERIC_ERROR = 'Ocorreu um erro inesperado. Tente novamente.';
const NETWORK_ERROR = 'Erro de conexão. Verifique sua internet e tente novamente.';
const SNACKBAR_QUEUE_KEY = 'pendingSnackbar';

class ApiError extends Error {
	constructor(message, status) {
		super(message);
		this.name = 'ApiError';
		this.status = status;
	}
}

function queueSnackbar(message, mode) {
	try {
		sessionStorage.setItem(SNACKBAR_QUEUE_KEY, JSON.stringify({message, mode}));
	}
	catch (_) {

	}
}

document.addEventListener('DOMContentLoaded', () => {
	let pending = null;
	
	try {
		pending = JSON.parse(sessionStorage.getItem(SNACKBAR_QUEUE_KEY));
		sessionStorage.removeItem(SNACKBAR_QUEUE_KEY);
	}
	catch (_) {

	}

	if (pending && typeof showSnackbar === 'function')
		showSnackbar(pending.message, pending.mode);
});

async function  readError(response) {
	const text = (await response.text()).trim();
	
	if (response.status === 401)
		return 'Sua sessão expirou. Recarregue a página e faça login novamente.';

	if (!text || text.startsWith('<'))
		return GENERIC_ERROR;

	try {
		const body = JSON.parse(text);
		if (body && body.error)
			return body.error;
	}
	catch (_) {

	}
	
	return text;
}

async function checkResponse(response) {
	if (!response.ok)
		throw new ApiError(await readError(response), response.status);

	return response;
}

async function fetchJson(url, options) {
	const response = await checkResponse(await fetch(url, options));
	return response.json();	
}

async function fetchText(url, options) {
	const response = await checkResponse(await fetch(url, options));
	return response.text();
}

async function handleResponse(response, successMessage) {
	await checkResponse(response);

	if (successMessage)
		queueSnackbar(successMessage, 'success');
	
	window.location.reload();
}

function handleError(error) {
	if (error instanceof ApiError)
		return showSnackbar(error.message, error.status === 409 ? 'warning' : 'error');

	console.error(error);

	const isNetworkError = error instanceof TypeError && /fetch|network|load failed/i.test(error.message);

	showSnackbar(isNetworkError ? NETWORK_ERROR : GENERIC_ERROR, 'error');
}

function renderEmptySearchRow(tableBody, query, label) {
	if (!query.trim())
		return;

	const row = document.createElement('tr');
	row.classList.add('empty-search-row');

	const cell = document.createElement('td');
	cell.colSpan = tableBody.closest('table').querySelectorAll('thead th').length;
	cell.classList.add('text-center', 'py-4');

	const queryStyle = document.createElement('span');
	queryStyle.textContent = query;
	queryStyle.classList.add('search-query');

	cell.append(label, queryStyle);
	row.appendChild(cell);
	tableBody.appendChild(row);
}

function createSearch({
	input, url, body, pageUrl, label, getFilters = () => new URLSearchParams()
}) {
	let searchTimeout;

	const searchInput = typeof input === 'string'
		? document.querySelector(input)
		: input;

	const tableBody = typeof body === 'string'
		? document.querySelector(body)
		: body;

	function handleSearch() {
		clearTimeout(searchTimeout);

		const query = searchInput.value;
		const filters = getFilters();

		const requestParams = new URLSearchParams(filters);
		requestParams.set('search', query);

		const urlParams = new URLSearchParams(filters);

		if (query)
			urlParams.set('search', query);

		history.replaceState({}, '', `${pageUrl}${urlParams.toString() ? `?${urlParams}` : ''}`);

		searchTimeout = setTimeout(() => {
			fetchText(`${url}?${requestParams}`)
				.then(html => {
					tableBody.innerHTML = html;

					if (!html.trim() && query.trim()) {
						renderEmptySearchRow(tableBody, query, label);
					}
				})
				.catch(handleError);
		}, 300);
	}

	return handleSearch;
}

async function submitModal(id, successMessage) {
	const form = document.getElementById(id);
	
	try {
		const response = await fetch(form.action, {
			method: 'POST',
			body: new FormData(form)
		});

		return await handleResponse(response, successMessage);
	}
	catch (error) {
		return handleError(error);
	}
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

const searchIcon = document.getElementById('search-icon')
if (searchIcon)
	searchIcon.innerHTML = ICON_SEARCH;

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
	zeroResults: () => `<div class="no-results">${text}</div>`
});