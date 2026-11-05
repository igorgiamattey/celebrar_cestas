const filterInput = monthFilter;
const searchBar = document.getElementById('financial-search-bar');

const handleSearch = createSearch({
	input: '#financial-search-bar',
	url: '/search_financial',
	body: '#financialTableBody',
	pageUrl: '/financeiro',
	label: 'Nenhum lançamento correspondente à pesquisa: ',
	getFilters: () => {
		const chosenMonth = filterInput.getValue();
		const monthId = chosenMonth === '' ? null : Number(chosenMonth);

		const params = new URLSearchParams();

		if (monthId)
			params.set('month', monthId);

		return params;
	}
});

const calendarIcon = document.getElementById('calendar-icon')
if (calendarIcon) {
	calendarIcon.innerHTML = ICON_CALENDAR;
	filterInput.control.appendChild(calendarIcon)
}