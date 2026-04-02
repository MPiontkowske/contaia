document.addEventListener('DOMContentLoaded', function () {
  document.getElementById('btn-enviar').addEventListener('click', enviar);
  document.getElementById('email').addEventListener('keydown', function (e) {
    if (e.key === 'Enter') enviar();
  });
});

function enviar() {
  var email = document.getElementById('email').value.trim();
  var btn = document.getElementById('btn-enviar');
  var spinner = document.getElementById('spinner');
  var btnText = document.getElementById('btn-text');

  if (!email) { showError('Informe o e-mail.'); return; }

  btn.disabled = true;
  spinner.style.display = 'block';
  btnText.textContent = 'Enviando…';
  hideAlerts();

  fetch('/esqueci-senha', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: email }),
  })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (data.ok) {
        document.getElementById('form-area').style.display = 'none';
        showSuccess('Se este e-mail estiver cadastrado, você receberá o link em instantes. Verifique sua caixa de entrada.');
      } else {
        showError(data.error || 'Erro ao processar solicitação.');
      }
    })
    .catch(function () { showError('Erro de conexão. Tente novamente.'); })
    .finally(function () {
      btn.disabled = false;
      spinner.style.display = 'none';
      btnText.textContent = 'Enviar link de redefinição';
    });
}

function showError(msg) {
  var el = document.getElementById('alert-error');
  el.textContent = msg;
  el.classList.add('show');
}
function showSuccess(msg) {
  var el = document.getElementById('alert-success');
  el.textContent = msg;
  el.classList.add('show');
}
function hideAlerts() {
  document.getElementById('alert-error').classList.remove('show');
  document.getElementById('alert-success').classList.remove('show');
}
