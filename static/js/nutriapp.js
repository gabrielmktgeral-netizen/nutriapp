/* NutriApp — folha de adicionar refeição.
   O ecrã é todo renderizado pelo Flask; este ficheiro só trata da folha
   (abrir, fechar, procurar, escolher, contar) e submete por POST normal.
   O acordeão das refeições é <details> nativo — não precisa de JS. */

(function () {
  'use strict';

  var folha = document.querySelector('[data-folha]');
  if (!folha) { return; }

  var campoTipo = folha.querySelector('[data-tipo-campo]');
  var busca = folha.querySelector('[data-busca]');
  var escolhidos = folha.querySelector('[data-escolhidos]');
  var semResultados = folha.querySelector('[data-sem-resultados]');
  var resumo = folha.querySelector('[data-resumo]');
  var total = folha.querySelector('[data-total]');
  var guardar = folha.querySelector('[data-guardar]');
  var pratos = Array.prototype.slice.call(folha.querySelectorAll('.food'));

  var picks = []; // [{ id, kcal }]

  function num(n) { return Math.round(n).toLocaleString('pt-PT'); }

  function atualizarTotais() {
    var n = picks.length;
    var soma = picks.reduce(function (a, p) { return a + p.kcal; }, 0);
    var tipo = campoTipo.value;

    resumo.textContent = n === 0
      ? 'Escolhe alimentos da despensa'
      : n + (n === 1 ? ' alimento escolhido' : ' alimentos escolhidos');
    total.textContent = num(soma) + ' kcal';
    guardar.textContent = n === 0
      ? 'Guardar em ' + tipo
      : 'Guardar ' + num(soma) + ' kcal em ' + tipo;

    // campos que vão no POST
    escolhidos.innerHTML = '';
    picks.forEach(function (p) {
      var i = document.createElement('input');
      i.type = 'hidden';
      i.name = 'alimento_id';
      i.value = p.id;
      escolhidos.appendChild(i);
    });

    // contagem por alimento
    pratos.forEach(function (b) {
      var c = picks.filter(function (p) { return String(p.id) === b.dataset.id; }).length;
      b.classList.toggle('is-picked', c > 0);
      b.querySelector('[data-contagem]').textContent = c > 1 ? ' ×' + c : '';
    });
  }

  function abrir(tipo) {
    if (tipo) { campoTipo.value = tipo; }
    folha.querySelectorAll('[data-tipo]').forEach(function (b) {
      b.setAttribute('aria-pressed', b.dataset.tipo === campoTipo.value ? 'true' : 'false');
    });
    picks = [];
    busca.value = '';
    filtrar();
    atualizarTotais();
    folha.classList.add('is-open');
    document.body.style.overflow = 'hidden';
    busca.focus();
  }

  function fechar() {
    folha.classList.remove('is-open');
    document.body.style.overflow = '';
  }

  function filtrar() {
    var q = busca.value.trim().toLowerCase();
    var visiveis = 0;
    pratos.forEach(function (b) {
      var ok = !q || b.dataset.nome.indexOf(q) > -1;
      b.hidden = !ok;
      if (ok) { visiveis += 1; }
    });
    semResultados.hidden = visiveis > 0;
  }

  document.querySelectorAll('[data-abrir-folha]').forEach(function (b) {
    b.addEventListener('click', function () { abrir(b.dataset.abrirFolha); });
  });

  folha.querySelector('[data-fechar-folha]').addEventListener('click', fechar);
  folha.addEventListener('click', function (e) { if (e.target === folha) { fechar(); } });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && folha.classList.contains('is-open')) { fechar(); }
  });

  folha.querySelectorAll('[data-tipo]').forEach(function (b) {
    b.addEventListener('click', function () {
      campoTipo.value = b.dataset.tipo;
      folha.querySelectorAll('[data-tipo]').forEach(function (o) { o.setAttribute('aria-pressed', 'false'); });
      b.setAttribute('aria-pressed', 'true');
      atualizarTotais();
    });
  });

  busca.addEventListener('input', filtrar);

  pratos.forEach(function (b) {
    b.addEventListener('click', function () {
      picks.push({ id: b.dataset.id, kcal: parseFloat(b.dataset.kcal) || 0 });
      atualizarTotais();
    });
  });

  folha.querySelector('.sheet').addEventListener('submit', function (e) {
    if (!picks.length) { e.preventDefault(); fechar(); }
  });
})();

/* ===== Cronometro e exercicios do ecra Exercicio =====
   So isto precisa de JavaScript: um relogio no browser. O que fica feito
   segue no POST do formulario (campos "segundos" e "feitos"). */

(function () {
  'use strict';

  var botao = document.querySelector('[data-cronometro]');
  if (!botao) { return; }

  var rotulo = document.querySelector('[data-cronometro-rotulo]');
  var icone = botao.querySelector('svg');
  var mostrador = document.querySelector('[data-tempo]');
  var campoSegundos = document.querySelector('[data-campo-segundos]');
  var campoFeitos = document.querySelector('[data-campo-feitos]');
  var contagem = document.querySelector('[data-feitos]');
  var guardar = document.querySelector('[data-guardar-treino]');
  var tarefas = Array.prototype.slice.call(document.querySelectorAll('[data-exercicio]'));

  var PLAY = '<path d="M7 4.5v15l13-7.5z"></path>';
  var PAUSE = '<path d="M7 4.5h4v15H7zM13 4.5h4v15h-4z"></path>';

  var segundos = 0;
  var relogio = null;
  var feitos = [];

  function pintarTempo() {
    var m = String(Math.floor(segundos / 60)).padStart(2, '0');
    var s = String(segundos % 60).padStart(2, '0');
    mostrador.textContent = m + ':' + s;
    campoSegundos.value = segundos;
  }

  botao.addEventListener('click', function () {
    if (relogio) {
      clearInterval(relogio);
      relogio = null;
      botao.className = 'btn btn-primary';
      icone.innerHTML = PLAY;
      rotulo.textContent = 'Retomar';
      guardar.hidden = false;
    } else {
      botao.className = 'btn btn-secondary';
      icone.innerHTML = PAUSE;
      rotulo.textContent = 'Parar';
      guardar.hidden = true;
      relogio = setInterval(function () { segundos += 1; pintarTempo(); }, 1000);
    }
  });

  tarefas.forEach(function (t) {
    t.addEventListener('click', function () {
      var i = t.dataset.exercicio;
      var k = feitos.indexOf(i);
      if (k > -1) { feitos.splice(k, 1); } else { feitos.push(i); }
      t.classList.toggle('is-done', k === -1);
      t.setAttribute('aria-pressed', k === -1 ? 'true' : 'false');
      campoFeitos.value = feitos.join(',');
      contagem.textContent = feitos.length + ' de ' + tarefas.length + ' exercícios feitos';
      if (feitos.length) { guardar.hidden = false; }
    });
  });

  pintarTempo();
})();
