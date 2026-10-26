let originalFinancialValues = {};
let viewFinancialEditing = false;

const REQUIRED_DATE_STATUSES = ['PAID']
const EDITABLE_DATE_ORIGINS = ['PENDING']

function setPlaceholder(selector, text) {
	selector.settings.placeholder = text;
	selector.control_input.setAttribute('placeholder', text);
	selector.inputState();
}

function fillViewModal(data) {
	viewFinancialEditing = false;
	document.getElementById('viewFinancial-id').value = data.id_lancamento;

	viewFinancialTypeSelector.setValue(data.tipo, true);
	viewFinancialCategorySelector.clear(true);
	viewFinancialCategorySelector.clearOptions();
	viewFinancialCategorySelector.addOptions(availableCategories[data.tipo] || []);
	viewFinancialCategorySelector.setValue(data.categoria, true);

	activateExtraField(data.categoria, 'view');

	viewFinancialStatusSelector.clear(true);
	viewFinancialStatusSelector.clearOptions();
	availableFinancialStatuses
		.filter(s => data.allowed_status.includes(s.id))
		.forEach(s => viewFinancialStatusSelector.addOption(s));
	viewFinancialStatusSelector.setValue(data.status_pagamento, true);

	viewFinancialOrderSelector.setValue(data.id_pedido ?? '', true);
	document.getElementById('viewFinancial-supplier').value = data.fornecedor ?? '';

	document.getElementById('viewFinancial-description').value = data.descricao;

	const valueInput = document.getElementById('viewFinancial-value');
	valueInput.value = Number(data.valor).toFixed(2);
	valueInput.readOnly = data.categoria === 'ORDER_PAYMENT';
	valueInput.dispatchEvent(new Event('input', {bubbles: true}));

	document.getElementById('viewFinancial-date').value = data.data_pagamento ?? '';
	updateDateField(data.status_pagamento, 'view');

	const canRefund = data.status_pagamento === 'PAID'
		&& !data.refunded
		&& data.categoria !== 'REFUND';
	document.getElementById('viewFinancial-refundBtn').style.display = canRefund
		? 'inline-block'
		: 'none'
}

function fillOrderValue(orderId, mode) {
	const selector = mode === 'new' ? newFinancialOrderSelector : viewFinancialOrderSelector;
	const input = document.getElementById(`${mode}Financial-value`);
	const order = selector.options[orderId];

	const price = order ? Number(order.price) : NaN;

	if (!order || Number.isNaN(price)) {
		input.value = '';
		input.readOnly = false;
	}
	else {
		input.value = price.toFixed(2)
		input.readOnly = true;
	}
	
	input.dispatchEvent(new Event('input', {bubbles: true}));
}

function updateCategoryOptions(type, mode) {
	const catSelector = mode === 'new' ? newFinancialCategorySelector : viewFinancialCategorySelector;

	const allowedCats = availableCategories[type] || [];
	catSelector.clear();
	catSelector.clearOptions();
	catSelector.addOptions(allowedCats);
	catSelector.refreshOptions(false);

	if (allowedCats.length) {
		catSelector.enable();
		setPlaceholder(catSelector, "Categoria da transação...")
	}
	else {
		catSelector.disable();
		setPlaceholder(catSelector, "Selecione o tipo primeiro")
	}
}

function activateExtraField(cat, mode) {
	const showOrder = document.getElementById(`${mode}Financial-showOrder`);
	const showSupplier = document.getElementById(`${mode}Financial-showSupplier`);
	const orderSelector = mode === 'new' ? newFinancialOrderSelector : viewFinancialOrderSelector;
	const supplierInput = document.getElementById(`${mode}Financial-supplier`);
	const orderCat = 'ORDER_PAYMENT';
	const supplierCat = 'MARKET';

	showOrder.style.display = cat === orderCat ? 'inline-block' : 'none';
	showSupplier.style.display = cat === supplierCat ? 'inline-block' : 'none';

	if (cat !== orderCat)
		orderSelector.clear();
	if (cat !== supplierCat)
		supplierInput.value = '';
}

function updateDateField(status, mode) {
	const input = document.getElementById(`${mode}Financial-date`);
	const label = document.getElementById(`${mode}Financial-dateLbl`);
	const requiresDate = REQUIRED_DATE_STATUSES.includes(status)

	const canEdit = mode === 'new'
		|| (viewFinancialEditing && EDITABLE_DATE_ORIGINS.includes(originalFinancialValues.status_pagamento));

	label.textContent = requiresDate ? 'Data de Pagamento*:' : 'Data de Pagamento:';
	input.disabled = !(requiresDate && canEdit);

	if (!requiresDate && canEdit)
		input.value = '';
}

async function refundFinancial() {
	const id = document.getElementById('viewFinancial-id').value;
	
	const confirmed = await openConfirm('Confirmar estorno?', 'Tem certeza que deseja estornar esse lançamento? Será criado um lançamento de estorno com o valor de oposto.');
	
	if (!confirmed)
		return;

	const csrfToken = document.querySelector('input[name="csrf_token"]').value;
	fetch(`/financeiro/${id}/estornar`, { method: 'POST', headers: {'X-CSRFToken': csrfToken} })
		.then(res => handleResponse(res, 'Lançamento estornado com sucesso!'))
		.catch(handleError);
}

const availableTypes = JSON.parse(
	document.getElementById('newFinancial-type').dataset.types
);

const availableCategories = JSON.parse(
	document.getElementById('newFinancial-category').dataset.category
);

const availableFinancialStatuses = JSON.parse(
	document.getElementById('newFinancial-status').dataset.status
);

const availableOrders = JSON.parse(
	document.getElementById('newFinancial-order').dataset.orders
);

const newFinancialTypeSelector = new TomSelect('#newFinancial-type', {
	options: availableTypes,
	valueField: 'id',
	labelField: 'title',
	searchField: 'title',
	create: false,
	maxItems: 1,
	maxOptions: null,
	onChange: (value) => updateCategoryOptions(value, 'new'),
	sortField: [
		{
			field: 'title',
			direction: 'asc'
		}
	]
});

const newFinancialCategorySelector = new TomSelect('#newFinancial-category', {
	valueField: 'id',
	labelField: 'title',
	searchField: 'title',
	create: false,
	maxItems: 1,
	maxOptions: null,
	placeholder: 'Selecione o tipo primeiro...',
	onChange: (value) => activateExtraField(value, 'new'),
	sortField: [
		{
			field: '$order',
			direction: 'asc'
		}
	]
});

const newFinancialStatusSelector = new TomSelect('#newFinancial-status', {
	options: availableFinancialStatuses,
	valueField: 'id',
	labelField: 'title',
	searchField: 'title',
	create: false,
	maxItems: 1,
	maxOptions: null,
	onChange: (value) => {updateDateField(value, 'new'); saveButton('new')},
	sortField: [
		{
			field: 'title',
			direction: 'asc'
		}
	]
});

const newFinancialOrderSelector = new TomSelect('#newFinancial-order', {
	options: availableOrders,
	valueField: 'id',
	labelField: 'title',
	searchField: 'title',
	create: false,
	maxItems: 1,
	maxOptions: null,
	onChange: (value) => fillOrderValue(value, 'new'),
	sortField: [
		{
			field: '$order',
			direction: 'asc'
		}
	]
});

let viewFinancialTypeSelector = null;
let viewFinancialCategorySelector = null;
let viewFinancialStatusSelector = null;
let viewFinancialOrderSelector = null;
const viewFinancialForm = document.getElementById('viewFinancial-form');

if (viewFinancialForm) {
	viewFinancialTypeSelector = new TomSelect('#viewFinancial-type', {
		options: availableTypes,
		valueField: 'id',
		labelField: 'title',
		searchField: 'title',
		create: false,
		maxItems: 1,
		maxOptions: null,
		onChange: (value) => updateCategoryOptions(value, 'view'),
		sortField: [
			{
				field: 'title',
				direction: 'asc'
			}
		]
	});

	viewFinancialCategorySelector = new TomSelect('#viewFinancial-category', {
		valueField: 'id',
		labelField: 'title',
		searchField: 'title',
		create: false,
		maxItems: 1,
		maxOptions: null,
		onChange: (value) => activateExtraField(value, 'view'),
		sortField: [
			{
				field: '$order',
				direction: 'asc'
			}
		]
	});

	viewFinancialStatusSelector = new TomSelect('#viewFinancial-status', {
		options: availableFinancialStatuses,
		valueField: 'id',
		labelField: 'title',
		searchField: 'title',
		create: false,
		maxItems: 1,
		maxOptions: null,
		onChange: (value) => {updateDateField(value, 'view'); saveButton('view')},
		sortField: [
			{
				field: 'title',
				direction: 'asc'
			}
		]
	});

	viewFinancialOrderSelector = new TomSelect('#viewFinancial-order', {
		options: availableOrders,
		valueField: 'id',
		labelField: 'title',
		searchField: 'title',
		create: false,
		maxItems: 1,
		maxOptions: null,
		onChange: (value) => fillOrderValue(value, 'view'),
		sortField: [
			{
				field: '$order',
				direction: 'asc'
			}
		]
	});

	viewFinancialTypeSelector.disable();
	viewFinancialCategorySelector.disable();
	viewFinancialStatusSelector.disable();
	viewFinancialOrderSelector.disable();
}

function saveNewFinancial() {
	submitModal('newFinancial-form', 'Lançamento criado com sucesso!');
}

function updateFinancial() {
	const financial_id = document.getElementById('viewFinancial-id').value;

	submitModal('viewFinancial-form', `Lançamento #${financial_id} atualizado com sucesso!`);
}

function saveButton(mode) {
	const statusSelector = mode === 'new'
		? newFinancialStatusSelector
		: viewFinancialStatusSelector;

	const categorySelector = mode === 'new'
		? newFinancialCategorySelector
		: viewFinancialCategorySelector;

	const ids = [
		`${mode}Financial-status`,
		`${mode}Financial-type`,
		`${mode}Financial-category`,
		`${mode}Financial-value`,
	];

	if (REQUIRED_DATE_STATUSES.includes(statusSelector.getValue()))
		ids.push(`${mode}Financial-date`);

	if (categorySelector.getValue() === 'MARKET')
		ids.push(`${mode}Financial-supplier`);

	if (categorySelector.getValue() === 'ORDER_PAYMENT')
		ids.push(`${mode}Financial-order`);

	toggleSaveButton(ids, `${mode}Financial-saveBtn`);
}

function openNewFinancialModal() {
	document.getElementById('newFinancial-form').reset();

	newFinancialTypeSelector.clear(true);
	newFinancialCategorySelector.clear(true);
	newFinancialStatusSelector.clear(true);
	newFinancialOrderSelector.clear(true);

	const valueInput = document.getElementById('newFinancial-value');
	valueInput.value = '';
	valueInput.readOnly = false;

	updateCategoryOptions('', 'new');
	activateExtraField('', 'new');
	updateDateField('', 'new');

	saveButton("new");
	document.getElementById('newFinancial-modal').style.display = "flex";
}

function openViewFinancialModal(id) {
	id = parseInt(id, 10);
	fetchJson(`/financeiro/${id}/data`)
		.then(data => {
			originalFinancialValues = {
				id_lancamento: data.id_lancamento,
				id_pedido: data.id_pedido,
				tipo: data.tipo,
				categoria: data.categoria,
				descricao: data.descricao,
				status_pagamento: data.status_pagamento,
				fornecedor: data.fornecedor,
				valor: data.valor,
				data_pagamento: data.data_pagamento,
				allowed_status: data.allowed_status,
				refunded: data.refunded
			};

			fillViewModal(data);
			resetViewFinancialModalState();

			document.getElementById('viewFinancial-modal').style.display = "flex";
			saveButton('view');
		})
		.catch(handleError);
}

function enableEditFinancial() {
	const status = viewFinancialStatusSelector.getValue();
	if (status === "CANCELLED" || status === "PAID")
		return;
	
	viewFinancialEditing = true;
	
	viewFinancialStatusSelector.enable();
	viewFinancialTypeSelector.enable();
	viewFinancialCategorySelector.enable();
	viewFinancialOrderSelector.enable();
	
	document.getElementById('viewFinancial-description').disabled = false;
	document.getElementById('viewFinancial-value').disabled = false;
	document.getElementById('viewFinancial-supplier').disabled = false;

	updateDateField(status, 'view');

	document.getElementById('viewFinancial-editBtn').style.display = 'none';
	document.getElementById('viewFinancial-saveBtn').style.display = 'inline-block';
	document.getElementById('viewFinancial-cancelBtn').style.display = 'inline-block';

	saveButton('view');
}

function cancelEditFinancial() {
	fillViewModal(originalFinancialValues);
	resetViewFinancialModalState();
	saveButton('view');
}

function resetViewFinancialModalState() {
	viewFinancialEditing = false;
	viewFinancialCategorySelector.disable();
	viewFinancialOrderSelector.disable();
	viewFinancialStatusSelector.disable();
	viewFinancialTypeSelector.disable();
	const status = viewFinancialStatusSelector.getValue();
	document.getElementById('viewFinancial-editBtn').style.display = 'inline-block';
	if (status === "PAID" || status === "CANCELLED")
		document.getElementById('viewFinancial-editBtn').style.display = 'none';

	document.getElementById('viewFinancial-supplier').disabled = true;
	document.getElementById('viewFinancial-value').disabled = true;
	document.getElementById('viewFinancial-date').disabled = true;
	document.getElementById('viewFinancial-description').disabled = true;
	
	document.getElementById('viewFinancial-saveBtn').style.display = 'none';
	document.getElementById('viewFinancial-cancelBtn').style.display = 'none';
}

function openBalance() {
	document.getElementById('viewBalance-modal').style.display = 'flex';
}

function openMonthStatement() {
	document.getElementById('viewStatement-modal').style.display = 'flex';
}