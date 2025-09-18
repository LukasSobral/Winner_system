document.addEventListener('submit', function(e) {
  if (e.target && e.target.id === 'leadCreateForm') {
    console.log("Interceptando submit via delegação global");
    e.preventDefault();

    const createForm = e.target;
    const formData = new FormData(createForm);
    const url = createForm.getAttribute('action');

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
        const modalElement = document.getElementById('createLeadModal');
        const modal = bootstrap.Modal.getInstance(modalElement);
        modal.hide();

        createForm.reset();

        const tableBody = document.getElementById('leadsTable').querySelector('tbody');
        tableBody.insertAdjacentHTML('afterbegin', data.row_html);
      } else {
        document.getElementById('leadFormErrors').innerText = 'Erro: ' + JSON.stringify(data.errors);
      }
    })
    .catch(error => {
      console.error('Erro na requisição AJAX:', error);
      document.getElementById('leadFormErrors').innerText = 'Erro interno. Tente novamente.';
    });
  }
});
