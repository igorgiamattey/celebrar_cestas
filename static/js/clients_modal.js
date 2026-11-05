// === GLOBAL VARIABLES ===
let originalClientValues = {};

// === HELPERS ===
function toggleSaveClientButton(mode) {
	const fields = [
		`${mode}Client-name`,
		`${mode}Client-phone`,
	];

	const button = `${mode}Client-saveBtn`;
	
	toggleSaveButton(
			fields,
			button
		)
}

// === CRUD ===
async function deleteClient() {
	const id = document.getElementById('viewClient-id').value;

	const confirmed = await openConfirm('Excluir cliente?', 'Tem certeza que deseja excluir este cliente?');

	if (confirmed) {
		const csrfToken = document.querySelector('input[name="csrf_token"]').value;
		fetch(`/delete_client/${id}`, { method: 'POST', headers: {'X-CSRFToken': csrfToken} })
			.then(res => handleResponse(res, 'Cliente excluído com sucesso!'))
			.catch(handleError);
	}
}

function saveNewClient() {
	submitModal('newClient-form', 'Cliente criado com sucesso!');
}

function updateClient() {
	const client_name = document.getElementById('viewClient-name').value;
	submitModal('viewClient-form', `Cliente "${client_name}" atualizado com sucesso`);
}

// === OPEN MODAL ===
function fillClientViewModal(data) {
	document.getElementById('viewClient-id').value = data.client_id;
	document.getElementById('viewClient-name').value = data.client_name;
	document.getElementById('viewClient-phone').value = data.client_phone;
}

function openNewClientModal() {
	document.getElementById('newClient-form').reset();
	document.getElementById('newClient-modal').style.display = "flex";
	toggleSaveClientButton('new');
}

function openViewClientModal(id) {
	id = parseInt(id, 10);
	fetchJson(`/client_data/${id}`)
		.then(data => {
			originalClientValues = {
				client_id: data.client_id,
				client_name: data.client_name,
				client_phone: data.client_phone,
			}

			fillClientViewModal(data);
			resetViewClientModalState();

			document.getElementById('viewClient-modal').style.display = "flex";
			toggleSaveClientButton('view');
		})
		.catch(handleError);
}

// === EDIT VIEW MODAL ===
function enableEditClient() {
	document.getElementById('viewClient-name').disabled = false;
	document.getElementById('viewClient-phone').disabled = false;

	document.getElementById('viewClient-editBtn').style.display = 'none';
	document.getElementById('viewClient-saveBtn').style.display = 'inline-block';
	document.getElementById('viewClient-cancelBtn').style.display = 'inline-block';

	toggleSaveClientButton('view');
}

function cancelEditClient() {
	fillClientViewModal(originalClientValues);
	resetViewClientModalState();
	toggleSaveClientButton('view');
}

function resetViewClientModalState() {
	document.getElementById('viewClient-name').disabled = true;
	document.getElementById('viewClient-phone').disabled = true;

	document.getElementById('viewClient-editBtn').style.display = 'inline-block';
	document.getElementById('viewClient-saveBtn').style.display = 'none';
	document.getElementById('viewClient-cancelBtn').style.display = 'none';
}