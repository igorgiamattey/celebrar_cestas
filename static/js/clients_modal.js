let originalClientsValues = {};

function openNewClientModal() {
	document.getElementById('newClient-form').reset();
	document.getElementById('newClient-modal').style.display = "flex";
	toggleSaveButton(['newClient-name', 'newCliente-phone'], 'newClient-saveBtn');
}

function openViewClientModal(id) {
	id = parseInt(id, 10);
	fetchJson(`/clientes/${id}/data`)
		.then(data => {
			document.getElementById('viewClient-id').value = data.id_cliente;
			document.getElementById('viewClient-name').value = data.nome_razao;
			document.getElementById('viewClient-phone').value = data.telefone;

			originalClientsValues = {
				nome_razao: data.nome_razao,
				telefone: data.telefone,
			}

			resetViewClientModalState();
			document.getElementById('viewClient-modal').style.display = "flex";
			toggleSaveButton(['viewClient-name', 'viewClient-phone'], 'viewClient-saveBtn');
		})
		.catch(handleError);
}

function enableEditClient() {
	document.getElementById('viewClient-name').disabled = false;
	document.getElementById('viewClient-phone').disabled = false;

	document.getElementById('viewClient-editBtn').style.display = 'none';
	document.getElementById('viewClient-saveBtn').style.display = 'inline-block';
	document.getElementById('viewClient-cancelBtn').style.display = 'inline-block';

	toggleSaveButton(['viewClient-name', 'viewClient-phone'], 'viewClient-saveBtn');
}

function cancelEditClient() {
	document.getElementById('viewClient-name').value = originalClientsValues.nome_razao;
	document.getElementById('viewClient-phone').value = originalClientsValues.telefone;

	resetViewClientModalState();
}

function resetViewClientModalState() {
	document.getElementById('viewClient-name').disabled = true;
	document.getElementById('viewClient-phone').disabled = true;

	document.getElementById('viewClient-editBtn').style.display = 'inline-block';
	document.getElementById('viewClient-saveBtn').style.display = 'none';
	document.getElementById('viewClient-cancelBtn').style.display = 'none';
}

async function deleteClient() {
	const id = document.getElementById('viewClient-id').value;

	const confirmed = await openConfirm('Excluir cliente?', 'Tem certeza que deseja excluir este cliente?');

	if (confirmed) {
		const csrfToken = document.querySelector('input[name="csrf_token"]').value;
		fetch(`/clientes/${id}/delete`, { method: 'POST', headers: {'X-CSRFToken': csrfToken} })
			.then(res => handleResponse(res, 'Cliente excluído com sucesso!'))
			.catch(handleError);
	}
}