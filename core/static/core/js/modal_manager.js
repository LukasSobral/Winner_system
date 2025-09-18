document.addEventListener('DOMContentLoaded', function () {
    attachModalListeners();
});

function attachModalListeners() {
    document.querySelectorAll('.open-modal').forEach(button => {
        // Evita múltiplos listeners
        button.removeEventListener('click', handleOpenModal);
        button.addEventListener('click', handleOpenModal);
    });
}

function handleOpenModal() {
    const url = this.dataset.url;
    const rowId = this.dataset.rowId || ''; // pode estar vazio no "create"
    openModal(url, rowId);
}

function getCSRFToken() {
    const cookie = document.cookie
        .split(';')
        .find(c => c.trim().startsWith('csrftoken='));
    return cookie ? cookie.trim().split('=')[1] : '';
}

function openModal(url, rowId) {
    fetch(url, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('modalContent').innerHTML = data.form_html;
        const modal = new bootstrap.Modal(document.getElementById('mainModal'));
        modal.show();

        const form = document.getElementById('ajax-form');
        if (form) {
            form.addEventListener('submit', function (e) {
                e.preventDefault();
                submitForm(url, form, modal, rowId);
            });
        }
    })
    .catch(err => console.error("Erro ao abrir modal:", err));
}

function submitForm(url, form, modal, rowId) {
    const formData = new FormData(form);

    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const tableRow = document.querySelector(`#row-${rowId}`);
            if (tableRow) {
                tableRow.outerHTML = data.row_html; // edição
            } else {
                const tbody = document.querySelector('table tbody');
                if (tbody) {
                    tbody.insertAdjacentHTML('beforeend', data.row_html); // novo
                }
            }

            // 🔁 Reanexa os listeners nos novos botões
            attachModalListeners();

            modal.hide();
        } else {
            document.getElementById('modalContent').innerHTML = data.form_html;
        }
    })
    .catch(err => console.error("Erro ao submeter formulário:", err));
}
