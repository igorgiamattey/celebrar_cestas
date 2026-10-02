let searchTimeout;
const checkbox = document.getElementById('orders-checkbox');

function handleSearch() {
	clearTimeout(searchTimeout);
	
	const query = document.getElementById('orders-search-bar').value;
	const openOnly = checkbox.checked;

	const params = new URLSearchParams();

	if (query)
		params.set('search', query);

	if (openOnly)
		params.set('openonly', 'true');

	history.replaceState({}, '', `/pedidos${params.toString() ? `?${params.toString()}` : ''}`)

	searchTimeout = setTimeout(() => {
		fetch(`/pedidos/search?search=${encodeURIComponent(query)}&openonly=${openOnly}`)
			.then(res => res.text())
			.then(html => {
				document.getElementById('ordersTableBody').innerHTML = html;
			});
	}, 300);
}

checkbox.addEventListener('change', () => {
	handleSearch();
})