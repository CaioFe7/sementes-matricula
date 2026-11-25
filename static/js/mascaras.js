// Máscaras de CPF, telefone e CEP.
// Qualquer campo com o atributo data-mascara="cpf", "telefone" ou "cep" é
// formatado enquanto a pessoa digita. O servidor guarda só os números.
(function () {
  "use strict";

  function soDigitos(texto) {
    return texto.replace(/\D/g, "");
  }

  var formatos = {
    cpf: function (d) {
      d = d.slice(0, 11);
      var texto = d.slice(0, 3);
      if (d.length > 3) { texto += "." + d.slice(3, 6); }
      if (d.length > 6) { texto += "." + d.slice(6, 9); }
      if (d.length > 9) { texto += "-" + d.slice(9, 11); }
      return texto;
    },
    telefone: function (d) {
      d = d.slice(0, 11);
      if (d.length === 0) { return ""; }
      if (d.length <= 2) { return "(" + d; }
      var ddd = d.slice(0, 2);
      var numero = d.slice(2);
      var corte = d.length > 10 ? 5 : 4;
      var texto = "(" + ddd + ") " + numero.slice(0, corte);
      if (numero.length > corte) { texto += "-" + numero.slice(corte); }
      return texto;
    },
    cep: function (d) {
      d = d.slice(0, 8);
      var texto = d.slice(0, 5);
      if (d.length > 5) { texto += "-" + d.slice(5); }
      return texto;
    }
  };

  function aplicar(campo) {
    var formato = formatos[campo.getAttribute("data-mascara")];
    if (formato) {
      campo.value = formato(soDigitos(campo.value));
    }
  }

  // Disponível para testes: window.mascaras.cpf("12345678909")
  window.mascaras = formatos;

  document.addEventListener("DOMContentLoaded", function () {
    var campos = document.querySelectorAll("[data-mascara]");
    Array.prototype.forEach.call(campos, function (campo) {
      aplicar(campo);
      campo.addEventListener("input", function () { aplicar(campo); });
    });
  });
})();
