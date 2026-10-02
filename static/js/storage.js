let searchTimeout;

function handleSearch() {
	clearTimeout(searchTimeout);
	const query = document.getElementById('storage-search-bar').value;

	history.replaceState({}, '', `/estoque${query ? `?search=${encodeURIComponent(query)}` : ''}`)
		
	searchTimeout = setTimeout(() => {
		fetch(`/estoque/search?search=${encodeURIComponent(query)}`)
			.then(res => res.text())
			.then(html => {
				document.getElementById('storageTableBody').innerHTML = html;
			});
	}, 300);
}