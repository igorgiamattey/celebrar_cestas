let originalDeliveryValues = {};

let newDeliveryOrders = [];
let viewDeliveryOrders = [];

let viewAvailableOrders = [];

let defaultStatus = 'PENDING';

const availableCouriers = JSON.parse(
	document.getElementById('newDelivery-courier').dataset.couriers
);

const availableStatuses = JSON.parse(
	document.getElementById('newDelivery-status').dataset.status
);

const availableOrders = JSON.parse(
	document.getElementById('newDelivery-orders').dataset.orders
);

const availableDates = JSON.parse(
	document.getElementById('newDelivery-date').dataset.dates
);

const newDeliveryCourierSelector = new TomSelect('#newDelivery-courier', {
	options: availableCouriers,
	valueField: 'id',
	labelField: 'name',
	searchField: 'name',
	create: false,
	maxItems: 1,
	sortField: [
		{
			field: 'name',
			direction: 'asc'
		}
	]
});

const newDeliveryOrderSelector = new TomSelect('#newDelivery-orders', {
	options: [],
	valueField: 'id',
	labelField: 'title',
	searchField: 'title',
	create: false,
	maxItems: 1,
	sortField: [
		{
			field: 'title',
			direction: 'asc'
		}
	]
});

const newDeliveryStatusSelector = new TomSelect('#newDelivery-status', {
	options: availableStatuses,
	valueField: 'id',
	labelField: 'title',
	searchField: 'title',
	create: false,
	maxItems: 1,
	sortField: [
		{
			field: 'title',
			direction: 'asc'
		}
	]
});

const newDeliveryDateSelector = new TomSelect('#newDelivery-date', {
	options: availableDates,
	valueField: 'id',
	labelField: 'date',
	searchField: 'date',
	create: false,
	maxItems: 1,
	onChange: () => onDateChange('new')


});

function refreshOrderOptions(dateId, mode) {
	const orderSelector = mode === 'new'
		? newDeliveryOrderSelector
		: viewDeliveryOrderSelector

	const orders = mode === 'new'
		? newDeliveryOrders
		: viewDeliveryOrders;

	const orders_source = mode === 'new'
		? availableOrders
		: viewAvailableOrders;

	const taken = new Set(orders.map(ord => ord.id));
	
	orderSelector.clear(true);
	orderSelector.clearOptions();

	orders_source
		.filter(ord => ord.date === dateId && !taken.has(ord.id))
		.forEach(ord => orderSelector.addOption(ord));
}

let viewDeliveryCourierSelector = null;
let viewDeliveryOrderSelector = null;
let viewDeliveryStatusSelector = null;
let viewDeliveryDateSelector = null;
const viewDeliveryForm = document.getElementById('viewDelivery-form');

if (viewDeliveryForm) {
	viewDeliveryCourierSelector = new TomSelect('#viewDelivery-courier', {
		options: availableCouriers,
		valueField: 'id',
		labelField: 'name',
		searchField: 'name',
		create: false,
		maxItems: 1,
		sortField: [
			{
				field: 'name',
				direction: 'asc'
			}
		]
	});

	viewDeliveryOrderSelector = new TomSelect('#viewDelivery-orders', {
		options: [],
		valueField: 'id',
		labelField: 'title',
		searchField: 'title',
		create: false,
		maxItems: 1,
		sortField: [
			{
				field: 'title',
				direction: 'asc'
			}
		]
	});

	viewDeliveryStatusSelector = new TomSelect('#viewDelivery-status', {
		options: availableStatuses,
		valueField: 'id',
		labelField: 'title',
		searchField: 'title',
		create: false,
		maxItems: 1,
		sortField: [
			{
				field: 'title',
				direction: 'asc'
			}
		]
	});

	viewDeliveryDateSelector = new TomSelect('#viewDelivery-date', {
		options: availableDates,
		valueField: 'id',
		labelField: 'date',
		searchField: 'date',
		create: false,
		maxItems: 1,
		onChange: () => onDateChange('view')
	});

	viewDeliveryCourierSelector.disable();
	viewDeliveryOrderSelector.disable();
	viewDeliveryStatusSelector.disable();
	viewDeliveryDateSelector.disable();
}

function saveButton(mode) {
	mode === 'new'
		? toggleSaveButton(
			['newDelivery-date'],
			'newDelivery-saveBtn',
			[newDeliveryOrders]
		)
		: toggleSaveButton(
			['viewDelivery-date'],
			'viewDelivery-saveBtn',
			[viewDeliveryOrders]
		)
}

function openNewDeliveryModal() {
	document.getElementById('newDelivery-form').reset();

	newDeliveryDateSelector.clear();
	newDeliveryOrderSelector.clear(true);
	newDeliveryOrderSelector.clearOptions();
	newDeliveryCourierSelector.clear();
	newDeliveryStatusSelector.setValue(defaultStatus);
	newDeliveryStatusSelector.disable();

	newDeliveryOrders = [];

	renderDeliveryOrders('new');
	saveButton('new');
	document.getElementById('newDelivery-modal').style.display = "flex";
}

function openViewDeliveryModal(id) {
	id = parseInt(id, 10);
	fetch(`/entregas/${id}/data`)
		.then(res => {
			if (!res.ok) throw new Error(res.status);
			return res.json();
		})
		.then(data => {
			document.getElementById('viewDelivery-id').value = data.id_entrega;
			viewDeliveryCourierSelector.setValue(data.id_entregador ?? '', true);
			
			viewDeliveryStatusSelector.clear(true);
			viewDeliveryStatusSelector.clearOptions();
			const allowedStatuses = [...data.allowed_status];
			availableStatuses
				.filter(status => allowedStatuses.includes(status.id))
				.forEach(status => {viewDeliveryStatusSelector.addOption(status)});
			viewDeliveryStatusSelector.setValue(data.status_entrega, true);
			
			viewDeliveryDateSelector.clear(true);
			viewDeliveryDateSelector.clearOptions()
			data.available_dates.forEach(date_op => viewDeliveryDateSelector.addOption(date_op));
			
			if (data.data_entrega && !viewDeliveryDateSelector.options[data.data_entrega]) {
				viewDeliveryDateSelector.addOption({
					id: data.data_entrega,
					date: data.data_entrega.split('-').reverse().join('/')
				});
			}
			viewDeliveryDateSelector.setValue(data.data_entrega ?? '', true);
			
			viewDeliveryOrders = data.orders || [];
			viewAvailableOrders = data.available_orders;
			refreshOrderOptions(data.data_entrega, 'view');

			originalDeliveryValues = {
				id_entregador: data.id_entregador,
				status_entrega: data.status_entrega,
				data_entrega: data.data_entrega,
				orders: structuredClone(viewDeliveryOrders)
			};

			resetViewDeliveryModalState();

			document.getElementById('viewDelivery-modal').style.display = "flex";
			saveButton('view');
		})
		.catch(
			err => (
				console.error('Não foi possível abrir a entrega', err),
				alert("Não foi possívela abrir a entrega.")
			)
		);
}

function saveNewDelivery() {
	document.getElementById('newDelivery-items').value = JSON.stringify(serialiseDeliveryOrders('new'));

	submitModal('newDelivery-form');
}

function updateDelivery() {
	document.getElementById('viewDelivery-items').value = JSON.stringify(serialiseDeliveryOrders('view'));

	submitModal('viewDelivery-form');
}

function enableEditDelivery() {
	const status = viewDeliveryStatusSelector.getValue();
	viewDeliveryStatusSelector.enable();
	viewDeliveryCourierSelector.enable();

	if (status === "PENDING"){
		viewDeliveryDateSelector.enable();
		
		document.getElementById('viewDelivery-addOrderRow').style.display = 'flex';
		viewDeliveryOrderSelector.enable()
	}

	document.getElementById('viewDelivery-editBtn').style.display = 'none';
	document.getElementById('viewDelivery-saveBtn').style.display = 'inline-block';
	document.getElementById('viewDelivery-cancelBtn').style.display = 'inline-block';

	renderDeliveryOrders('view');
	saveButton('view');
}

function cancelEditDelivery() {
	viewDeliveryCourierSelector.setValue(originalDeliveryValues.id_entregador ?? '', true);
	viewDeliveryStatusSelector.setValue(originalDeliveryValues.status_entrega, true);
	viewDeliveryDateSelector.setValue(originalDeliveryValues.data_entrega ?? '', true);

	viewDeliveryOrders = structuredClone(originalDeliveryValues.orders);
	refreshOrderOptions(originalDeliveryValues.data_entrega, 'view');
	
	resetViewDeliveryModalState();
}

function resetViewDeliveryModalState() {
	viewDeliveryCourierSelector.disable();
	viewDeliveryDateSelector.disable();
	viewDeliveryStatusSelector.disable();
	
	document.getElementById('viewDelivery-addOrderRow').style.display = 'none';
	viewDeliveryOrderSelector.disable()
	
	document.getElementById('viewDelivery-editBtn').style.display = 'inline-block';
	document.getElementById('viewDelivery-saveBtn').style.display = 'none';
	document.getElementById('viewDelivery-cancelBtn').style.display = 'none';

	renderDeliveryOrders('view');
}

function addOrderToDelivery(mode) {
	const orderSelector = mode === 'new'
		? newDeliveryOrderSelector
		: viewDeliveryOrderSelector;

	const orders = mode === 'new'
		? newDeliveryOrders
		: viewDeliveryOrders;

	const orderId = Number(orderSelector.getValue());

	if (!orderId) {
		alert('Selecione um pedido.');
		return;
	}

	const existingOrder = orders.find(
		existing => existing.id === orderId
	);

	if (existingOrder) {
		alert('Esse pedido já foi adicionado.');
		return;
	}

	orders.unshift({...orderSelector.options[orderId]});
	orderSelector.removeOption(String(orderId));

	renderDeliveryOrders(mode);

	saveButton(mode);
}

function removeOrderFromDelivery(mode, index) {
	const orderSelector = mode === 'new'
		? newDeliveryOrderSelector
		: viewDeliveryOrderSelector;
	
	const orders = mode === 'new'
		? newDeliveryOrders
		: viewDeliveryOrders;

	const [removed] = orders.splice(index, 1);
	orderSelector.addOption(removed)

	renderDeliveryOrders(mode);

	saveButton(mode);
}

function renderDeliveryOrders(mode) {
	const container = document.getElementById(`${mode}Delivery-orderList`);
	
	const orders = mode === 'new'
		? newDeliveryOrders
		: viewDeliveryOrders;
	
	const isEditable = mode === 'new'
		|| !document.getElementById('viewDelivery-date').disabled;
	
	container.innerHTML = '';
		
	orders.forEach((order, index) => {
		const row = document.createElement('div');
		row.className = 'delivery-orders-row';

		row.innerHTML = `
			<span class="delivery-orders-name"></span>

			<div class="delivery-orders-actions">
				${isEditable ? `
				<button
					type="button"
					class="btn-remove-item"
				>
					&times;
				</button>
				` : ''}
			</div>
		`;

		row.querySelector('.delivery-orders-name').textContent = order.title;

		if (isEditable) {
			row.querySelector('.btn-remove-item').onclick = () => removeOrderFromDelivery(mode, index);
		}

		container.appendChild(row);
	});
}

function serialiseDeliveryOrders(mode) {
	const orders = mode === 'new'
		? newDeliveryOrders
		: viewDeliveryOrders;

	return orders.map(order => order.id);
}

function onDateChange(mode) {
	const dateSelector = mode === 'new'
		? newDeliveryDateSelector
		: viewDeliveryDateSelector;

	const orders = mode === 'new'
		? newDeliveryOrders
		: viewDeliveryOrders;

	orders.length = 0
	
	refreshOrderOptions(dateSelector.getValue(), mode);
	renderDeliveryOrders(mode);
	saveButton(mode);
}