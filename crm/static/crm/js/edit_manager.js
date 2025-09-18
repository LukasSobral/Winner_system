document.addEventListener('DOMContentLoaded', () => {
  document.body.addEventListener('click', function(e) {
    // Edit button click handler
    if (e.target.classList.contains('edit-lead-btn')) {
      const leadId = e.target.getAttribute('data-id');

      fetch(`/crm/${leadId}/edit/ajax/`)
      .then(response => response.text())
      .then(html => {
        document.getElementById('editLeadModalBody').innerHTML = html;

        const modalElement = document.getElementById('editLeadModal');
        const modal = new bootstrap.Modal(modalElement);
        modal.show();

        // Submit handler inside modal
        const editForm = document.getElementById('leadEditForm');
        editForm.addEventListener('submit', function(ev) {
          ev.preventDefault();

          const formData = new FormData(editForm);
          const url = editForm.getAttribute('action');

          fetch(url, {
            method: 'POST',
            headers: {
              'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
            },
            body: formData
          })
          .then(response => response.json())
          .then(data => {
            if (data.success) {
              // Atualiza a linha na tabela sem reload
              const row = document.querySelector(`#lead-row-${leadId}`);
              row.outerHTML = data.row_html;

              // Fecha modal
              modal.hide();
            } else {
              document.getElementById('leadEditErrors').innerText = 'Erro: ' + JSON.stringify(data.errors);
            }
          })
          .catch(error => {
            console.error('Erro na requisição AJAX:', error);
            document.getElementById('leadEditErrors').innerText = 'Erro interno. Tente novamente.';
          });
        });
      })
      .catch(error => {
        console.error('Erro ao carregar formulário de edição:', error);
      });
    }
  });
});
