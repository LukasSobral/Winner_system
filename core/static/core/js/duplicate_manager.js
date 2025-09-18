document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.duplicate-btn').forEach(button => {
        button.addEventListener('click', function () {
            const sessionId = this.dataset.sessionId;
            const url = `/sessions/duplicate-modal/${sessionId}/`;

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    const modalElement = document.getElementById('mainModal');
                    const modalContent = document.getElementById('modalContent');
                    modalContent.innerHTML = data.form_html;

                    const modal = new bootstrap.Modal(modalElement);
                    modal.show();

                    // Adiciona listener para o formulário de duplicação
                    const form = modalContent.querySelector('form');
                    form.addEventListener('submit', function (e) {
                        e.preventDefault();
                        const formData = new FormData(form);

                        fetch(url, {
                            method: 'POST',
                            body: formData,
                            headers: {
                                'X-Requested-With': 'XMLHttpRequest',
                                'X-CSRFToken': getCookie('csrftoken')
                            }
                        })
                            .then(response => response.json())
                            .then(data => {
                                if (data.success) {
                                    const tbody = document.querySelector('table tbody');
                                    tbody.insertAdjacentHTML('beforeend', data.row_html);
                                    modal.hide();
                                } else {
                                    modalContent.innerHTML = data.form_html;
                                }
                            });
                    });
                });
        });
    });
});

// Helper para CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        for (let cookie of document.cookie.split(';')) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.slice(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
