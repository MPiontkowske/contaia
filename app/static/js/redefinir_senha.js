document.addEventListener('DOMContentLoaded', function () {
  var btn = document.getElementById('btn-salvar');
  if (btn) btn.addEventListener('click', salvar);
});

function salvar() {
  var pwd = document.getElementById('password').value;
  var pwd2 = document.getElementById('password2').value;
  var btn = document.getElementById('btn-salvar');
  var spinner = document.getElementById('spinner');
  var btnText = document.getElementById('btn-text');

  if (pwd.length < 6) { showError('Senha deve ter ao menos 6 caracteres.'); return; }
  if (pwd !== pwd2) { showError('As senhas não coincidem.'); return; }

  btn.disabled = true;
  spinner.style.display = 'block';
  btnText.textContent = 'Salvando…';
  hideAlerts();

  fetch('/redefinir-senha/' + RESET_TOKEN, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password: pwd }),
  })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (data.ok) {
        document.getElementById('form-area').style.display = 'none';
        showSuccess('Senha redefinida com sucesso! Redirecionando…');
        setTimeout(function () { window.location.href = '/login'; }, 2000);
      } else {
        showError(data.error || 'Erro ao redefinir senha.');
      }
    })
    .catch(function () { showError('Erro de conexão. Tente novamente.'); })
    .finally(function () {
      btn.disabled = false;
      spinner.style.display = 'none';
      btnText.textContent = 'Salvar nova senha';
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
