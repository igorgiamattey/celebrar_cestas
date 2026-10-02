let searchTimeout;

function handleSearch() {
	clearTimeout(searchTimeout);
	const query = document.getElementById('clients-search-bar').value;

	history.replaceState({}, '', `/clientes${query ? `?search=${encodeURIComponent(query)}` : ''}`)
		
	searchTimeout = setTimeout(() => {
		fetch(`/clientes/search?search=${encodeURIComponent(query)}`)
			.then(res => res.text())
			.then(html => {
				document.getElementById('clientsTableBody').innerHTML = html;
			});
	}, 300);
}