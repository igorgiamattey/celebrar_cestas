let searchTimeout;

function handleSearch() {
	clearTimeout(searchTimeout);
	const query = document.getElementById('catalogue-search-bar').value;

	history.replaceState({}, '', `/catalogo${query ? `?search=${encodeURIComponent(query)}` : ''}`)

	searchTimeout = setTimeout(() => {
		fetch(`/catalogo/search?search=${encodeURIComponent(query)}`)
			.then(res => res.text())
			.then(html => {
				document.getElementById('catalogueTableBody').innerHTML = html;
			});
	}, 300);
}