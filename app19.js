if(ORDER.indexOf("Europa")<0)ORDER.unshift("Europa");
if(LIGAS.indexOf("Champions League")<0)LIGAS.unshift("Champions League","Europa League");
FLAG["Europa"]="🇪🇺";
function lgErr(i){
  if(!i.getAttribute("data-f")){
    i.setAttribute("data-f","1");
    i.src="logos./"+i.getAttribute("data-k")+".png";
    return;
  }
  i.style.display="none";
  i.nextSibling.style.display="inline";
}
function logo(n){
  var k=nk(n);
  return '<span class="lw"><img src="logos/'+k+'.png" data-k="'+k+'" alt="" title="'+esc(n)+'" onerror="lgErr(this)"><span class="lt">'+esc(n)+'</span></span>';
}
(function(){
  var s=document.createElement("style");
  s.textContent=".pm{margin:8px 0 0 6px}"+
  ".pm>summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:8px;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 10px;font-size:14px}"+
  ".pm>summary::-webkit-details-marker{display:none}"+
  ".pm>summary::after{content:'▾';color:var(--mu);margin-left:auto;padding-left:6px}"+
  ".pm[open]>summary::after{transform:rotate(180deg)}"+
  ".pm .pt{display:flex;flex-direction:column;gap:2px;min-width:0;flex:1}"+
  ".pm .pt b{font-size:14px;color:var(--tx);display:flex;align-items:center;gap:4px;flex-wrap:wrap}"+
  ".pm .pt small{color:var(--mu);font-size:12px}"+
  ".pm .pb{padding-top:6px}"+
  ".pm .res{font-size:12px;font-weight:700;color:var(--mu);white-space:nowrap}";
  document.head.appendChild(s);
})();
function resumenP(a){
  var g=0,p=0,n=0;
  a.forEach(function(c){
    if(c.estado==="ganada")g++;
    else if(c.estado==="perdida")p++;
    else if(c.estado==="nula")n++;
  });
  var t=[];
  if(g)t.push(g+" ✔");
  if(p)t.push(p+" ✘");
  if(n)t.push(n+" nula"+(n>1?"s":""));
  return t.join(" · ");
}
function cardSel(c){
  return '<article class="card"><div class="desc">'+esc(c.suceso)+bd(c)+'</div>'+cbody(c)+'</article>';
}
function partidoHtml(a){
  var c=a[0],k="m|"+c.fixture;
  S.keys.push(k);
  var rs=resumenP(a);
  var h='<details class="pm" data-k="'+esc(k)+'"'+(S.open[k]?" open":"")+'><summary><div class="pt"><b>'+cr(c.hid)+esc(c.local)+' v '+cr(c.aid)+esc(c.visitante)+'</b><small>'+esc(c.hm)+'</small></div>';
  if(rs)h+='<span class="res">'+rs+'</span>';
  h+='<span class="ct">'+a.length+'</span></summary><div class="pb">'+a.map(cardSel).join("")+'</div></details>';
  return h;
}
function radar19(){
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
  h+='<label>Orden dentro de cada partido<select id="fo">'+sel("prob","Probabilidad (mayor)")+sel("ev","EV (mayor)")+sel("cuota","Cuota (mayor)")+sel("cuota_asc","Cuota (menor)")+'</select></label></div>';
  var l=all.filter(function(c){
    return (S.minEv===""||c.ev*100>=+S.minEv)&&(S.minP===""||c.prob*100>=+S.minP)&&(S.minC===""||c.best.c>=+S.minC);
  });
  var key={prob:function(c){return -c.prob},ev:function(c){return -c.ev},cuota:function(c){return -c.best.c},cuota_asc:function(c){return c.best.c}}[S.ord];
  l.sort(function(a,b){
    var d=(a.fin||0)-(b.fin||0);
    if(d)return d;
    var fa=String(a.fixture),fb=String(b.fixture);
    if(fa!==fb)return fa<fb?-1:1;
    return key(a)-key(b);
  });
  var P={};
  l.forEach(function(c){
    var x=(P[c.pais]=P[c.pais]||{});
    var y=(x[c.liga]=x[c.liga]||{});
    (y[c.fixture]=y[c.fixture]||[]).push(c);
  });
  var ps=Object.keys(P).sort(function(a,b){var i=ORDER.indexOf(a),j=ORDER.indexOf(b);return (i<0?99:i)-(j<0?99:j)||a.localeCompare(b)});
  S.keys=[];
  if(!ps.length)return h+'<div class="empty">Ninguna selección cumple esos filtros.</div>';
  h+='<div class="chips"><button onclick="abre(1)">Abrir todo</button><button onclick="abre(0)">Cerrar todo</button></div>';
  ps.forEach(function(p){
    var ls=Object.keys(P[p]).sort(function(a,b){var i=LIGAS.indexOf(a),j=LIGAS.indexOf(b);return (i<0?99:i)-(j<0?99:j)});
    var n=0;
    ls.forEach(function(lg){Object.keys(P[p][lg]).forEach(function(f){n+=P[p][lg][f].length})});
    var kp="p|"+p;
    S.keys.push(kp);
    h+='<details class="pa" data-k="'+esc(kp)+'"'+(S.open[kp]?" open":"")+'><summary><span>'+(FLAG[p]||"🌍")+' '+esc(p)+'</span><span class="ct">'+n+'</span></summary>';
    ls.forEach(function(lg){
      var kl="l|"+p+"|"+lg;
      S.keys.push(kl);
      var fx=Object.keys(P[p][lg]).sort(function(a,b){
        return (P[p][lg][a][0].fin||0)-(P[p][lg][b][0].fin||0)||(a<b?-1:1);
      });
      var m=0;
      fx.forEach(function(f){m+=P[p][lg][f].length});
      h+='<details class="lg" data-k="'+esc(kl)+'"'+(S.open[kl]?" open":"")+'><summary><span>'+esc(lg)+'</span><span class="ct">'+m+'</span></summary><div class="lgb">'+fx.map(function(f){return partidoHtml(P[p][lg][f])}).join("")+'</div></details>';
    });
    h+='</details>';
  });
  return qm(h);
}
(function(){
  var d0=deHist;
  deHist=function(r){
    var o=d0(r);
    o.l10=r.l10;
    return o;
  };
  var b0=cbody;
  cbody=function(c){
    var h=b0(c);
    if(c.l10)h=h.replace('<div class="st">','<div class="st"><span class="chip">Últimos 10 <b>'+esc(c.l10)+'</b></span>');
    return h;
  };
  radar=function(){
    var all=S.data;
    S.data=all.filter(okT);
    var h;
    try{h=radar19()}finally{S.data=all}
    return chips(TIPOS,FT,"sT")+h;
  };
})();
if(S.data.length)draw();
