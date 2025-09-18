document.addEventListener('DOMContentLoaded', () => {
  document.body.addEventListener('click', function(e) {
    if (e.target.classList.contains('delete-lead-btn')) {
      const leadId = e.target.getAttribute('data-id');

      if (confirm('Tem certeza que deseja excluir este lead?')) {
        fetch(`/crm/${leadId}/delete/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
          }
        })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            // Remove a linha da tabela
            const row = e.target.closest('tr');
            row.parentNode.removeChild(row);
          } else {
            alert('Erro ao excluir lead.');
          }
        });
      }
    }
  });
});
