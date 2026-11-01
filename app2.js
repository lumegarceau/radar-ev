function sel(v,x,t){return '<option value="'+v+'"'+(S.ord===v?" selected":"")+'>'+t+'</option>'}
function radar(){
  var all=S.data,h="";
  if(!all.length)return '<div class="empty">Hoy no hay selecciones que cumplan los filtros.</div>';
  var tp=all.slice().sort(function(a,b){return b.prob-a.prob}).slice(0,5);
  var te=all.slice().sort(function(a,b){return b.ev-a.ev}).slice(0,5);
  h+='<h2>Lo mejor de hoy</h2><div class="tops">';
  h+=topBox("Top 5 probabilidad",tp,function(c){return '<span class="v">'+pc(c.prob)+'</span>'});
  h+=topBox("Top 5 EV",te,function(c){return '<span class="v '+(c.ev>=0?"pos":"neg")+'">'+evt(c)+'</span>'});
  h+='</div><div class="filters">';
  h+='<label>EV mínimo (%)<input id="fe" type="number" inputmode="decimal" value="'+S.minEv+'"></label>';
  h+='<label>Probabilidad mínima (%)<input id="fp" type="number" inputmode="decimal" value="'+S.minP+'"></label>';
  h+='<label>Cuota mínima<input id="fc" type="number" inputmode="decimal" step="0.01" value="'+S.minC+'"></label>';
  h+='<label>Ordenar por<select id="fo">'+sel("prob",0,"Probabilidad (mayor)")+sel("ev",0,"EV (mayor)")+sel("cuota",0,"Cuota (mayor)")+sel("cuota_asc",0,"Cuota (menor)")+'</select></label></div>';
  var l=all.filter(function(c){
    return (S.minEv===""||c.ev*100>=+S.minEv)&&(S.minP===""||c.prob*100>=+S.minP)&&(S.minC===""||c.best.c>=+S.minC);
  });
  var key={prob:function(c){return -c.prob},ev:function(c){return -c.ev},cuota:function(c){return -c.best.c},cuota_asc:function(c){return c.best.c}}[S.ord];
  l.sort(function(a,b){return key(a)-key(b)});
  var P={};
  l.forEach(function(c){P[c.pais]=P[c.pais]||{};(P[c.pais][c.liga]=P[c.pais][c.liga]||[]).push(c)});
  var ps=Object.keys(P).sort(function(a,b){var i=ORDER.indexOf(a),j=ORDER.indexOf(b);return (i<0?99:i)-(j<0?99:j)||a.localeCompare(b)});
  if(!ps.length)h+='<div class="empty">Ninguna selección cumple esos filtros.</div>';
  ps.forEach(function(p){
    h+='<div class="country">'+(FLAG[p]||"🌍")+' '+esc(p)+'</div>';
    Object.keys(P[p]).sort(function(a,b){var i=LIGAS.indexOf(a),j=LIGAS.indexOf(b);return (i<0?99:i)-(j<0?99:j)}).forEach(function(lg){
      h+='<div class="league">'+esc(lg)+'</div>'+P[p][lg].map(card).join("");
    });
  });
  return h;
}
function errores(){
  var l=S.data.filter(function(c){return c.gap>0.25}).sort(function(a,b){return b.gap-a.gap});
  var h='<h2>Posibles errores de cuota</h2><p class="upd">Selecciones donde la mejor cuota supera en más de un 25 % a la segunda. Puede que una casa haya calculado mal la probabilidad.</p>';
  return h+(l.length?l.map(card).join(""):'<div class="empty">Hoy no hay diferencias superiores al 25 %.</div>');
}
function bookies(){
  var h='<h2>Bookies y bonos de bienvenida</h2><div class="box">';
  Object.keys(AFF).forEach(function(n){
    h+='<div class="row bk"><div class="g"><b>'+esc(n)+'</b><small>Consulta el bono de bienvenida actual en su web.</small></div><a href="'+esc(AFF[n])+'" target="_blank" rel="sponsored noopener">Ver bono</a></div>';
  });
  return h+'</div>';
}
function resultados(){
  return '<h2>Resultados</h2><div class="empty">Aquí verás el balance por día, semana, mes y año, y por liga. Se activará cuando haya selecciones corregidas.</div>';
}
function draw(){
  nav();
  var h=S.demo?'<div class="demo">Datos de ejemplo. Se sustituirán por los reales cuando se ejecute la actualización automática.</div>':"";
  h+=({radar:radar,errores:errores,bookies:bookies,resultados:resultados})[S.tab]();
  document.getElementById("app").innerHTML=h;
  [["fe","minEv"],["fp","minP"],["fc","minC"]].forEach(function(p){
    var e=document.getElementById(p[0]);
    if(e)e.onchange=function(){S[p[1]]=e.value;draw()};
  });
  var o=document.getElementById("fo");
  if(o)o.onchange=function(){S.ord=o.value;draw()};
}
load();
