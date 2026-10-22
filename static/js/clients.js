let searchTimeout;

function handleSearch() {
	clearTimeout(searchTimeout);
	const query = document.getElementById('clients-search-bar').value;

	history.replaceState({}, '', `/clientes${query ? `?search=${encodeURIComponent(query)}` : ''}`)
		
	searchTimeout = setTimeout(() => {
		fetchText(`/clientes/search?search=${encodeURIComponent(query)}`)
			.then(html => {
				const tableBody = document.getElementById('clientsTableBody');

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

					cell.append('Nenhum cliente correspondente à pesquisa: ', queryStyle);

					row.appendChild(cell);
					tableBody.appendChild(row);
				}
			})
			.catch(handleError);
	}, 300);
}