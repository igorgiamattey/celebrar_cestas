let originalBasketValues = {};

let newBasketItems = [];
let viewBasketItems = [];

const availableItems = JSON.parse(
	document.getElementById('newBasket-itemSelect').dataset.items
);

const availableGroups = JSON.parse(
	document.getElementById('newBasket-itemSelect').dataset.groups
);

const availableList = [
	...availableGroups.map(item => ({
		...item,
		id: `group_${item.id}`,
		originalId: item.id,
		category: 'groups',
		categoryOrder: 1
	})),

	...availableItems.map(item => ({
		...item,
		id: `item_${item.id}`,
		originalId: item.id,
		category: 'items',
		categoryOrder: 2
	}))
];

const newBasketItemSelector = new TomSelect('#newBasket-itemSelect', {
	options: availableList,
	valueField: 'id',
	labelField: 'title',
	searchField: 'title',

	optgroupField: 'category',

	optgroups: [
		{value: 'groups', label: 'Grupos'},
		{value: 'items', label: 'Itens independentes'}
	],

	create: false,
	maxItems: 1,
	maxOptions: null,
	sortField: [
		{
			field: 'categoryOrder',
			direction: 'asc'
		},
		{
			field: 'title',
			direction: 'asc'
		}
	]
});

let viewBasketItemSelector = null;
const viewBasketForm = document.getElementById('viewBasket-form');

if (viewBasketForm) {
	viewBasketItemSelector = new TomSelect('#viewBasket-itemSelect',  {
		options: availableList,
		valueField: 'id',
		labelField: 'title',
		searchField: 'title',
		optgroupField: 'category',

		optgroups: [
			{value: 'groups', label: 'Grupos'},
			{value: 'items', label: 'Itens independentes'}
		],

		create: false,
		maxItems: 1,
		maxOptions: null,
		sortField: [
			{
				field: 'categoryOrder',
				direction: 'asc'
			},
			{
				field: 'title',
				direction: 'asc'
			}
		]
	});

	viewBasketItemSelector.disable();
}

function saveNewBasket() {
	document.getElementById('newBasket-items').value = JSON.stringify(newBasketItems);

	submitModal('newBasket-form', 'Cesta criada com sucesso!');
}

function updateBasket() {
	document.getElementById('viewBasket-items').value = JSON.stringify(viewBasketItems);
	const basket_name = document.getElementById('viewBasket-name').value;

	submitModal('viewBasket-form', `Cesta "${basket_name}" atualizada com sucesso`);
}

function openNewBasketModal() {
	document.getElementById('newBasket-form').reset();

	newBasketItems = [];
	renderBasketItems('new');

	newBasketItemSelector.clear();

	document.getElementById('newBasket-modal').style.display = "flex";

	toggleSaveButton([
		'newBasket-name',
		'newBasket-price'
	], 'newBasket-saveBtn', [newBasketItems])
}

function openViewBasketModal(id) {
	id = parseInt(id, 10);
	fetchJson(`/catalogo/${id}/data`)
		.then(data => {
			document.getElementById('viewBasket-id').value = data.id_produto;
			document.getElementById('viewBasket-name').value = data.nome_cesta;
			document.getElementById('viewBasket-price').value = data.preco_venda;

			viewBasketItems = data.items || [];

			originalBasketValues = {
				nome_cesta: data.nome_cesta,
				preco_venda: data.preco_venda,
				items: structuredClone(viewBasketItems)
			};
			

			resetViewBasketModalState();
			renderBasketItems('view');

			document.getElementById('viewBasket-modal').style.display = "flex";
			toggleSaveButton([
				'viewBasket-name',
				'viewBasket-price'
			], 'viewBasket-saveBtn', [viewBasketItems]);
		})
		.catch(handleError);
}

function enableEditBasket() {
	document.getElementById('viewBasket-name').disabled = false;
	document.getElementById('viewBasket-price').disabled = false;

	document.getElementById('viewBasket-addItemRow').style.display = 'flex';
	document.getElementById('viewBasket-addItemLbl').style.display = 'flex';
	viewBasketItemSelector.enable();
	document.getElementById('viewBasket-itemQty').disabled = false;
	
	document.getElementById('viewBasket-editBtn').style.display = 'none';
	document.getElementById('viewBasket-saveBtn').style.display = 'inline-block';
	document.getElementById('viewBasket-cancelBtn').style.display = 'inline-block';

	renderBasketItems('view');

	toggleSaveButton([
		'viewBasket-name',
		'viewBasket-price'
	], 'viewBasket-saveBtn', [viewBasketItems])
}

function cancelEditBasket() {
	document.getElementById('viewBasket-name').value = originalBasketValues.nome_cesta;
	document.getElementById('viewBasket-price').value = originalBasketValues.preco_venda;

	viewBasketItems = structuredClone(originalBasketValues.items);
	renderBasketItems('view');
	viewBasketItemSelector.clear();
	document.getElementById('viewBasket-itemQty').value = '';

	resetViewBasketModalState();
}

function resetViewBasketModalState() {
	document.getElementById('viewBasket-name').disabled = true;
	document.getElementById('viewBasket-price').disabled = true;
	
	document.getElementById('viewBasket-addItemRow').style.display = 'none';
	document.getElementById('viewBasket-addItemLbl').style.display = 'none';
	viewBasketItemSelector.disable();
	document.getElementById('viewBasket-itemQty').disabled = true;

	document.getElementById('viewBasket-editBtn').style.display = 'inline-block';
	document.getElementById('viewBasket-saveBtn').style.display = 'none';
	document.getElementById('viewBasket-cancelBtn').style.display = 'none';

	renderBasketItems('view');
}

async function deleteBasket() {
	const id = document.getElementById('viewBasket-id').value;

	const confirmed = await openConfirm('Excluir cesta?', 'Tem certeza que deseja excluir esta cesta?');
	
	if (confirmed) {
		const csrfToken = document.querySelector('input[name="csrf_token"]').value;
		fetch(`/catalogo/${id}/delete`, { method: 'POST', headers: {'X-CSRFToken': csrfToken} })
			.then(res => handleResponse(res, 'Cesta excluída com sucesso!'))
			.catch(handleError);
	}
}

function addItemToBasket(mode) {
	const qtyInput = document.getElementById(`${mode}Basket-itemQty`);

	const selector = mode === 'new'
		? newBasketItemSelector
		: viewBasketItemSelector;

	const itemId = selector.getValue();
	const quantity = parseFloat(qtyInput.value.replace(',','.'));

	if (!itemId) {
		showSnackbar('Selecione um item.', 'warning');
		return;
	}

	if (!quantity || quantity <= 0) {
		showSnackbar('Informe uma quantidade válida', 'warning');
		return;
	}

	const selectedItem = selector.options[itemId];

	if (
		(selectedItem.category === 'groups' ||
			selectedItem.unit === 'un' ||
			selectedItem.unit === 'UN') &&
			!Number.isInteger(quantity)
		) {
			showSnackbar('A quantidade deve ser um número inteiro.', 'warning');
			return;
		}

	const item = {
		item_id: selectedItem.originalId,
		item_name: selectedItem.name,
		unit: selectedItem.unit,
		quantity: quantity,
		category: selectedItem.category
	};

	const items = mode === 'new'
		? newBasketItems
		: viewBasketItems;

	const existingItem = items.find(
		existing =>
			existing.item_id === item.item_id &&
			existing.category === item.category
	);

	if (existingItem) {
		showSnackbar('Esse item já foi adicionado à cesta.', 'error');
		return;
	}

	items.unshift(item);

	renderBasketItems(mode);

	mode === 'new'
		? toggleSaveButton(
			['newBasket-name', 'newBasket-price'],
			'newBasket-saveBtn',
			[newBasketItems]
		)
		: toggleSaveButton(
			['viewBasket-name','viewBasket-price'],
			'viewBasket-saveBtn',
			[viewBasketItems]
		)

	selector.clear();
	qtyInput.value = '';
}

function renderBasketItems(mode) {
	const container = document.getElementById(`${mode}Basket-itemsList`);

	const items = mode === 'new'
		? newBasketItems
		: viewBasketItems;

	const isEditable = mode === 'new'
		|| !document.getElementById('viewBasket-itemQty').disabled;
	
	container.innerHTML = '';

	items.forEach((item, index) => {
		const row = document.createElement('div');
		
		const unitDisplay = item.category === 'items'
			? item.unit
			: 'un';

		row.className = 'basket-item-row';

		row.innerHTML = `
			<span class="basket-item-name"></span>

			<span class="basket-item-quantity"></span>

			${isEditable ? `
			<button
				type="button"
				class="btn-remove-item"
			>
				&times;
			</button>
			` : ''}
		`;

		row.querySelector('.basket-item-name').textContent = item.item_name;
		row.querySelector('.basket-item-quantity').textContent = `
				${item.quantity} ${unitDisplay.toLowerCase()}
		`;

		if (isEditable) {
			row.querySelector('.btn-remove-item').onclick = () => removeItemFromBasket(mode, index);
		}

		container.appendChild(row);
	});
}

function removeItemFromBasket(mode, index) {
	const items = mode === 'new'
		? newBasketItems
		: viewBasketItems;

	items.splice(index, 1);

	renderBasketItems(mode);
}