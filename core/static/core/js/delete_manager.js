let deleteUrl = '';
let deleteRowId = '';

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', function () {
            deleteUrl = this.dataset.url;
            deleteRowId = this.dataset.rowId;

            const modal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
            modal.show();
        });
    });

    document.getElementById('confirmDeleteBtn').addEventListener('click', function () {
        fetch(deleteUrl, {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCookie('csrftoken') }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById(`row-${deleteRowId}`).remove();
                    bootstrap.Modal.getInstance(document.getElementById('deleteConfirmModal')).hide();
                } else {
                    alert('Erro ao excluir.');
                }
            })
            .catch(err => console.error('Erro:', err));
    });
});

// Função auxiliar para obter CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
