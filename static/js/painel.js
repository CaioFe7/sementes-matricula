// Gráficos do painel de indicadores (Chart.js).
// Os dados chegam em um bloco JSON gerado pelo Django (id "dados-graficos").
(function () {
  "use strict";

  var bloco = document.getElementById("dados-graficos");
  if (!bloco || typeof Chart === "undefined") {
    return;
  }
  var dados = JSON.parse(bloco.textContent);
  var cores = ["#146c43", "#0d6efd", "#fd7e14", "#6f42c1", "#d63384", "#0aa2c0", "#6c757d", "#b02a37"];

  function criarGrafico(id, tipo, serie, opcoes) {
    var tela = document.getElementById(id);
    if (!tela || !serie) {
      return;
    }
    var umaCorPorItem = tipo === "doughnut";
    new Chart(tela, {
      type: tipo,
      data: {
        labels: serie.rotulos,
        datasets: [{
          label: "Total",
          data: serie.valores,
          backgroundColor: umaCorPorItem ? cores : cores[0]
        }]
      },
      options: Object.assign({
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: umaCorPorItem, position: "bottom" } },
        scales: umaCorPorItem ? {} : {
          x: { beginAtZero: true, ticks: { precision: 0 } },
          y: { beginAtZero: true, ticks: { precision: 0 } }
        }
      }, opcoes || {})
    });
  }

  criarGrafico("grafico-sexo", "doughnut", dados.sexo);
  criarGrafico("grafico-faixa", "bar", dados.faixa);
  criarGrafico("grafico-bairro", "bar", dados.bairro, { indexAxis: "y" });
  criarGrafico("grafico-atividade", "bar", dados.atividade, { indexAxis: "y" });
})();
