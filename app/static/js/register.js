document.addEventListener('DOMContentLoaded', function () {
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') register();
  });

  var btn = document.getElementById('btn-register');
  if (btn) btn.addEventListener('click', register);
});

function register() {
  var name    = document.getElementById('name').value.trim();
  var email   = document.getElementById('email').value.trim();
  var pwd     = document.getElementById('password').value;
  var btn     = document.getElementById('btn-register');
  var spinner = document.getElementById('spinner');
  var btnText = document.getElementById('btn-text');

  if (!name || !email || !pwd) { showError('Preencha todos os campos.'); return; }

  btn.disabled = true;
  spinner.style.display = 'block';
  btnText.textContent = 'Criando conta…';
  document.getElementById('alert-msg').classList.remove('show');

  fetch('/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: name, email: email, password: pwd }),
  })
    .then(function (res) { return res.json(); })
    .then(function (data) {
      if (data.ok) {
        window.location.href = '/dashboard';
      } else {
        showError(data.error || 'Erro ao criar conta.');
      }
    })
    .catch(function () {
      showError('Erro de conexão. Tente novamente.');
    })
    .finally(function () {
      btn.disabled = false;
      spinner.style.display = 'none';
      btnText.textContent = 'Criar conta grátis';
    });
}

function showError(msg) {
  var el = document.getElementById('alert-msg');
  el.textContent = msg;
  el.classList.add('show');
}
