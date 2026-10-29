let searchTimeout;

function handleSearch() {
	clearTimeout(searchTimeout);
	const query = document.getElementById('storage-search-bar').value;

	history.replaceState({}, '', `/estoque${query ? `?search=${encodeURIComponent(query)}` : ''}`)
		
	searchTimeout = setTimeout(() => {
		fetchText(`/search_item?search=${encodeURIComponent(query)}`)
			.then(html => {
				const tableBody = document.getElementById('storageTableBody');

				tableBody.innerHTML = html;

				if (!html.trim() && query.trim()) {
					const row = document.createElement('tr');
					row.classList.add('empty-search-row');
					
					const cell = document.createElement('td');
					
					cell.colSpan = tableBody.closest('table').querySelectorAll('thead th').length;
					cell.classList.add('text-center', 'py-4');
					
					const queryStyle = document.createElement('span');
					queryStyle.textContent = query;
					queryStyle.classList.add('search-query');

					cell.append('Nenhum item correspondente à pesquisa: ', queryStyle);

					row.appendChild(cell);
					tableBody.appendChild(row);
				}
			})
			.catch(handleError);
	}, 300);
}