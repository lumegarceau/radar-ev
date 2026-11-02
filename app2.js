(function(){
  var s=document.createElement("style");
  s.textContent=".dias{display:flex;gap:6px;margin:14px 0 4px;align-items:stretch}"+
  ".dia{flex:1;border:1px solid var(--line);background:var(--card);border-radius:10px;padding:8px 2px;font:inherit;color:var(--mu);cursor:pointer;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1px;line-height:1.2}"+
  ".dia.hoy{flex:1.8;padding:14px 4px;border-color:var(--ac)}"+
  ".dia span{font-size:12px}.dia b{font-size:15px;color:var(--tx)}"+
  ".dia.hoy b{font-size:19px}.dia.hoy span{font-size:13px;font-weight:700}"+
  ".dia i{font-style:normal;font-size:11px}"+
  ".dia.on{background:var(--ac);border-color:var(--ac);color:#fff}.dia.on b{color:#fff}"+
  ".pa,.lg{margin-top:8px}"+
  ".pa>summary,.lg>summary{list-style:none;cursor:pointer;display:flex;justify-content:space-between;align-items:center;gap:8px}"+
  ".pa>summary::-webkit-details-marker,.lg>summary::-webkit-details-marker{display:none}"+
  ".pa>summary{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px;font-weight:800;font-size:16px}"+
  ".lg>summary{padding:9px 6px 9px 12px;font-weight:700;font-size:14px;color:var(--mu);border-bottom:1px solid var(--line)}"+
  ".pa>summary::after,.lg>summary::after{content:'▾';color:var(--mu);margin-left:auto}"+
  ".pa[open]>summary::after,.lg[open]>summary::after{transform:rotate(180deg)}"+
  ".ct{background:var(--bg);border:1px solid var(--line);border-radius:12px;padding:1px 9px;font-size:12px;color:var(--mu);font-weight:600}"+
  ".lgb{padding:8px 0 0 8px}";
  document.head.appendChild(s);
})();
function sD(d){S.dia=d;draw()}
function abre(x){
  S.open={};
  if(x)S.keys.forEach(function(k){S.open[k]=1});
  draw();
}
function cap(s){return s.charAt(0).toUpperCase()+s.slice(1)}
function fl(d,o){
  var op=Object.assign({timeZone:"UTC"},o);
  return new Date(d+"T12:00:00Z").toLocaleDateString("es-ES",op);
}
function diasTabs(){
  var h=hoyS(),ds=[addd(h,-1),h,addd(h,1),addd(h,2)];
  var nm=["Ayer","Hoy","Mañana",null];
  return '<div class="dias">'+ds.map(function(d,i){
    var n=S.data.filter(function(c){return c.dia===d}).length;
    var cls="dia"+(i===1?" hoy":"")+(S.dia===d?" on":"");
    var t=nm[i]||cap(fl(d,{weekday:"long"}));
    return '<button class="'+cls+'" onclick="sD(\''+d+'\')"><span>'+t+'</span><b>'+fl(d,{day:"numeric",month:"short"})+'</b><i>'+n+' sel.</i></button>';
  }).join("")+"</div>";
}
function sel(v,t){return '<option value="'+v+'"'+(S.ord===v?" selected":"")+'>'+t+'</option>'}
function radar(){
  var h=diasTabs();
  var all=S.data.filter(function(c){return c.dia===S.dia});
  h+="<h2>"+cap(fl(S.dia,{weekday:"long",day:"numeric",month:"long",year:"numeric"}))+"</h2>";
  if(!all.length)return h+'<div class="empty">No hay selecciones para este día.</div>';
  var tp=all.slice().sort(function(a,b){return b.prob-a.prob}).slice(0,5);
  var te=all.slice().sort(function(a,b){return b.ev-a.ev}).slice(0,5);
  h+='<div class="tops">';
  h+=topBox("Top 5 probabilidad",tp,function(c){return '<span class="v">'+pc(c.prob)+'</span>'});
  h+=topBox("Top 5 EV",te,function(c){return '<span class="v '+(c.ev>=0?"pos":"neg")+'">'+evt(c)+'</span>'});
  h+='</div><div class="filters">';
  h+='<label>EV mínimo (%)<input id="fe" type="number" inputmode="decimal" value="'+S.minEv+'"></label>';
  h+='<label>Probabilidad mínima (%)<input id="fp" type="number" inputmode="decimal" value="'+S.minP+'"></label>';
  h+='<label>Cuota mínima<input id="fc" type="number" inputmode="decimal" step="0.01" value="'+S.minC+'"></label>';
  h+='<label>Ordenar por<select id="fo">'+sel("prob","Probabilidad (mayor)")+sel("ev","EV (mayor)")+sel("cuota","Cuota (mayor)")+sel("cuota_asc","Cuota (menor)")+'</select></label></div>';
  var l=all.filter(function(c){
    return (S.minEv===""||c.ev*100>=+S.minEv)&&(S.minP===""||c.prob*100>=+S.minP)&&(S.minC===""||c.best.c>=+S.minC);
  });
  var key={prob:function(c){return -c.prob},ev:function(c){return -c.ev},cuota:function(c){return -c.best.c},cuota_asc:function(c){return c.best.c}}[S.ord];
  l.sort(function(a,b){return key(a)-key(b)});
  var P={};
  l.forEach(function(c){P[c.pais]=P[c.pais]||{};(P[c.pais][c.liga]=P[c.pais][c.liga]||[]).push(c)});
  var ps=Object.keys(P).sort(function(a,b){var i=ORDER.indexOf(a),j=ORDER.indexOf(b);return (i<0?99:i)-(j<0?99:j)||a.localeCompare(b)});
  S.keys=[];
  if(!ps.length)return h+'<div class="empty">Ninguna selección cumple esos filtros.</div>';
  h+='<div class="chips"><button onclick="abre(1)">Abrir todo</button><button onclick="abre(0)">Cerrar todo</button></div>';
  ps.forEach(function(p){
    var ls=Object.keys(P[p]).sort(function(a,b){var i=LIGAS.indexOf(a),j=LIGAS.indexOf(b);return (i<0?99:i)-(j<0?99:j)});
    var n=0;
    ls.forEach(function(lg){n+=P[p][lg].length});
    var kp="p|"+p;
    S.keys.push(kp);
    h+='<details class="pa" data-k="'+esc(kp)+'"'+(S.open[kp]?" open":"")+'><summary><span>'+(FLAG[p]||"🌍")+' '+esc(p)+'</span><span class="ct">'+n+'</span></summary>';
    ls.forEach(function(lg){
      var kl="l|"+p+"|"+lg;
      S.keys.push(kl);
      h+='<details class="lg" data-k="'+esc(kl)+'"'+(S.open[kl]?" open":"")+'><summary><span>'+esc(lg)+'</span><span class="ct">'+P[p][lg].length+'</span></summary><div class="lgb">'+P[p][lg].map(card).join("")+'</div></details>';
    });
    h+='</details>';
  });
  return h;
}
function errores(){
  var l=S.data.filter(function(c){return c.gap>0.25&&!c.empez}).sort(function(a,b){return b.gap-a.gap});
  var h='<h2>Posibles errores de cuota</h2><p class="upd">Selecciones donde la mejor cuota supera en más de un 25 % a la segunda. Puede que una casa haya calculado mal la probabilidad.</p>';
  return h+(l.length?l.map(card).join(""):'<div class="empty">Ahora mismo no hay diferencias superiores al 25 %.</div>');
}
function bookies(){
  var h='<h2>Bookies y bonos de bienvenida</h2><div class="box">';
  Object.keys(AFF).forEach(function(n){
    h+='<div class="row bk"><div class="g"><b>'+esc(n)+'</b><small>Consulta el bono de bienvenida actual en su web.</small></div><a href="'+esc(AFF[n])+'" target="_blank" rel="sponsored noopener">Ver bono</a></div>';
  });
  return h+'</div>';
}
function draw(){
  nav();
  var h=S.demo?'<div class="demo">Datos de ejemplo. Se sustituirán por los reales cuando se ejecute la actualización automática.</div>':"";
  var T={radar:radar,errores:errores,bookies:bookies,resultados:(window.resultados||function(){return ""})};
  h+=T[S.tab]();
  var a=document.getElementById("app");
  a.innerHTML=h;
  if(!a._tg){
    a._tg=1;
    a.addEventListener("toggle",function(e){
      var t=e.target,k=t.getAttribute&&t.getAttribute("data-k");
      if(!k)return;
      if(t.open)S.open[k]=1;else delete S.open[k];
    },true);
  }
  [["fe","minEv"],["fp","minP"],["fc","minC"]].forEach(function(p){
    var e=document.getElementById(p[0]);
    if(e)e.onchange=function(){S[p[1]]=e.value;draw()};
  });
  var o=document.getElementById("fo");
  if(o)o.onchange=function(){S.ord=o.value;draw()};
}
load();
