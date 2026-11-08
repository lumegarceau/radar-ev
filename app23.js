(function(){
  var st=document.createElement("style");
  st.textContent=".r18{display:flex;gap:10px;align-items:flex-start;margin:10px 0 0;padding:8px 10px;background:#fff;border:1px solid var(--line);border-radius:8px;font-size:12px;color:var(--mu);line-height:1.4}"+
    ".r18 .b18{flex:none;background:var(--tx);color:#fff;font-weight:800;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-size:12px}"+
    ".r18 a{color:var(--ac);font-weight:700}"+
    ".bk small b{color:var(--tx)}"+
    ".bk .g small{display:block;margin-top:2px}";
  document.head.appendChild(st);
  var BONO={
    "betfair":"Apuesta 50 € y recibe hasta 200 €.",
    "betway":"Regístrate y llévate hasta 200 € en freebets.",
    "grancasinomadrid":"Hasta 100 € en freebets, sin cuota mínima.",
    "codere":"Duplica tu primer depósito: te devuelven el 100 % hasta 200 €.",
    "williamhill":"Empieza con hasta 150 € en freebets.",
    "winamax":"Sin bono de bienvenida.",
    "yosports":"Hasta 50 € en apuestas gratis al registrarte.",
    "speedybet":"Llévate 30 € en freebets.",
    "paf":"Llévate 20 € en freebets.",
    "sportium":"Dobla tu depósito hasta 200 €.",
    "marcaapuestas":"Hasta 200 € en apuestas gratis.",
    "daznbet":"Recibe el 100 % de tu primera apuesta, hasta 200 €, ganes o pierdas.",
    "versus":"Sin bono de bienvenida.",
    "888sports":"10 € gratis al registrarte y tu primera apuesta asegurada hasta 100 €.",
    "bet365":"Hasta 200 € en créditos de apuestas.",
    "bwin":"Una apuesta gratuita de hasta 100 €.",
    "1xbet":"Hasta 300 € en freebets con tus tres primeros depósitos."
  };
  var AVISO='<div class="r18"><span class="b18">+18</span><span>Solo para mayores de 18 años. Juega con responsabilidad: apostar puede crear adicción. Si el juego te causa problemas, pide ayuda en <a href="https://www.jugarbien.es" target="_blank" rel="noopener">jugarbien.es</a>.</span></div>';
  bookies=function(){
    var h='<h2>Bonos de bienvenida</h2>'+AVISO.replace("Solo para mayores de 18 años.","Solo para mayores de 18 años. Bonos de bienvenida sujetos a los términos y condiciones de cada casa.")+'<div class="box" style="margin-top:10px">';
    Object.keys(AFF).forEach(function(n){
      var t=BONO[nk(n)];
      var sin=t&&t.indexOf("Sin bono")===0;
      h+='<div class="row bk"><div class="g"><b>'+esc(n)+'</b><small>'+esc(t||"Consulta el bono de bienvenida actual en su web.")+'</small></div><a href="'+esc(AFF[n])+'" target="_blank" rel="sponsored noopener">'+(sin?"Ir a la web":"Ver bono")+'</a></div>';
    });
    return h+'</div>'+AVISO.replace("Solo para mayores de 18 años. ","");
  };
})();
// fin
