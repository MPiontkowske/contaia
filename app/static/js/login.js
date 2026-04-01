document.addEventListener('DOMContentLoaded', function () {
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') login();
  });

  var btn = document.getElementById('btn-login');
  if (btn) btn.addEventListener('click', login);
});

function login() {
  var email   = document.getElementById('email').value.trim();
  var pwd     = document.getElementById('password').value;
  var btn     = document.getElementById('btn-login');
  var alert   = document.getElementById('alert-msg');
  var spinner = document.getElementById('spinner');
  var btnText = document.getElementById('btn-text');

  if (!email || !pwd) { showError('Preencha e-mail e senha.'); return; }

  btn.disabled = true;
  spinner.style.display = 'block';
  btnText.textContent = 'Entrando…';
  alert.classList.remove('show');

  fetch('/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: email, password: pwd }),
  })
    .then(function (res) { return res.json(); })
    .then(function (data) {
      if (data.ok) {
        window.location.href = data.admin ? '/admin/' : '/dashboard';
      } else {
        showError(data.error || 'Erro ao entrar.');
      }
    })
    .catch(function () {
      showError('Erro de conexão. Tente novamente.');
    })
    .finally(function () {
      btn.disabled = false;
      spinner.style.display = 'none';
      btnText.textContent = 'Entrar';
    });
}

function showError(msg) {
  var el = document.getElementById('alert-msg');
  el.textContent = msg;
  el.classList.add('show');
}
