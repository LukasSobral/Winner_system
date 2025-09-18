document.addEventListener('DOMContentLoaded', function () {
    // STATUS DROPDOWN
    document.querySelectorAll('.status-dropdown').forEach(select => {
        select.addEventListener('change', function () {
            const sessionId = this.dataset.sessionId;
            const status = this.value;
            const url = `/sessions/update-status/${sessionId}/`;

            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ status: status })
            })
                .then(response => response.json())
                .then(data => {
                    if (!data.success) {
                        alert('Erro ao atualizar status.');
                    }
                })
                .catch(err => console.error('Erro ao atualizar status:', err));
        });
    });

    // SUBSTITUTE DROPDOWN
    document.querySelectorAll('.substitute-dropdown').forEach(select => {
        select.addEventListener('change', function () {
            const sessionId = this.dataset.sessionId;
            const substituteId = this.value;
            const url = `/sessions/update-substitute/${sessionId}/`;

            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ substitute_id: substituteId })
            })
                .then(response => response.json())
                .then(data => {
                    if (!data.success) {
                        alert('Erro ao atualizar substituto.');
                    }
                })
                .catch(err => console.error('Erro ao atualizar substituto:', err));
        });
    });
});

// Helper para obter CSRF Token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
