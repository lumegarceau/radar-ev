// Errores de cuota de TODOS los mercados (subpestaña). No toca la lista de siempre.
var ER={sub:"sel",data:null,cargando:false,f:{mk:"",casa:"",solo:"act",ord:"gap",pct:"",vent:"10"}};
(function(){
  var s=document.createElement("style");
  s.textContent=".erc{border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin:8px 0;background:#fff}"+
  ".erc h4{margin:0 0 2px;font-size:15px}.erc .pt{font-size:12px;color:var(--mu)}"+
  ".erc .ch{display:flex;flex-wrap:wrap;gap:4px;margin:6px 0}"+
  ".erc .ch span{font-size:12px;border:1px solid var(--line);border-radius:12px;padding:2px 8px;color:var(--mu)}"+
  ".erc .ch span.b{background:var(--ac);color:#fff;border-color:var(--ac)}"+
  ".erc .est{font-size:12px;margin-top:4px}.erc .est.ok{color:#0a7a2f;font-weight:600}.erc .est.no{color:var(--mu)}"+
  ".erf{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0}.erf label{font-size:12px;color:var(--mu)}"+
  ".erf select{display:block;width:100%;margin-top:3px;padding:8px;border:1px solid var(--line);border-radius:6px;font:inherit;color:var(--tx);background:#fff}";
  document.head.appendChild(s);
  var MK={corners:"córners",cards:"tarjetas",fouls:"faltas",shots:"remates",sot:"remates a puerta",goals:"goles",offsides:"fueras de juego",drawn:"faltas recibidas",saves:"paradas",tk:"entradas"};
  
  function f2(x){return Number(x).toFixed(2).replace(".",",")}
  function T(s){var d=Date.parse(s);return isNaN(d)?null:d}
  function hace(ms){
    if(ms==null)return "";
    var m=Math.round(ms/60000);
    if(m<2)return "hace un momento";
    if(m<90)return "hace "+m+" min";
    var h=Math.round(m/60);
    if(h<36)return "hace "+h+" h";
    return "hace "+Math.round(h/24)+" días";
  }
  function dur(ms){
    var m=Math.round(ms/60000);
    if(m<2)return "menos de 2 min";
    if(m<90)return m+" min";
    return (Math.round(m/6)/10).toString().replace(".",",")+" h";
  }
  function hm(s){return String(s||"").slice(11,16)}
  function dm(s){return String(s||"").slice(8,10)+"/"+String(s||"").slice(5,7)}
  function ok(x){if(x.c>5&&x.ref>=2.5)return false;return x.c<=3?x.gap>=0.30:x.gap>=0.70}
  function cred(r,soloUlt){
    if(soloUlt)return ok(r.ultima);
    return (r.serie||[]).some(ok)||ok(r.primera);
  }
  function kn(s){var m=/^(\d+)\/(\d+)$/.exec(s||"");return m?[+m[1],+m[2]]:null}
  // % de veces que se cumplio el suceso en los ultimos 10 o 20 partidos (en totales, el peor de los dos equipos)
  function tasaR(r,vent){
    var q=r.hist;if(!q)return null;
    var key=vent==="20"?"l20":"l10";
    var ps=(q.eq||q.jug)?[q.eq||q.jug]:[q.loc,q.vis],out=[];
    for(var i=0;i<ps.length;i++){
      if(!ps[i])return null;
      var x=kn(ps[i][key]);
      if(!x||x[1]<5)return null;
      out.push(x[0]/x[1]);
    }
    return Math.min.apply(null,out);
  }
  function listar(){
    var d=ER.data&&ER.data.sel||{},now=Date.now(),f=ER.f;
    return Object.keys(d).map(function(k){var r=d[k];r._k=k;return r}).filter(function(r){
      if(!cred(r,f.solo==="act"))return false;
      if(f.mk&&r.mercado!==f.mk)return false;
      if(f.casa&&!((r.primera.casas||[]).concat(r.ultima.casas||[])).some(function(b){return b===f.casa}))return false;
      if(f.solo==="act"&&!(r.activo&&T(r.inicio)>now))return false;
      if(f.pct){var t=tasaR(r,f.vent);if(t==null||t*100<Number(f.pct)-0.001)return false}
      return true;
    }).sort(function(a,b){
      if(f.ord==="rec"||f.ord==="ant"){var d=(T(b.primera.t)||0)-(T(a.primera.t)||0);return f.ord==="rec"?d:-d}
      var ga=a.ultima.c>3?1:0,gb=b.ultima.c>3?1:0;return ga!==gb?ga-gb:b.ultima.gap-a.ultima.gap});
  }
  function card(r){
    var now=Date.now(),ini=T(r.inicio),p=r.primera,u=r.ultima;
    var tp=T(p.t),tu=T(u.t);
    var vivo=r.activo&&ini>now;
    var estado;
    if(vivo)estado='<div class="est ok">Apostable ahora · visto '+hace(now-tu)+'</div>';
    else if(ini<=now)estado='<div class="est no">Partido empezado</div>';
    else estado='<div class="est no">Ya no está disponible · desapareció '+hace(now-(T(r.cerrado)||tu))+'</div>';
    var chips=(u.cuotas||[]).map(function(x,i){
      var mejor=(u.casas||[]).indexOf(x.b)>=0;
      return '<span class="'+(mejor?'b':'')+'">'+esc(x.b)+' '+f2(x.c)+'</span>';
    }).join("");
    var h='<div class="erc"><h4>'+esc(r.suceso)+'</h4>';
    h+='<div class="pt">'+esc(r.local)+' - '+esc(r.visitante)+' · '+esc(r.liga)+' · '+dm(r.inicio)+' '+hm(r.inicio)+'</div>';
    h+='<div class="ch">'+chips+'</div>';
    h+='<div class="pt">Mejor cuota <b>'+f2(u.c)+'</b> en '+esc((u.casas||[]).join(", "))+' · la siguiente es '+f2(u.ref)+' · '+Math.round(u.gap*100)+' % más · '+u.n+' casas independientes</div>';
    h+='<div class="pt">Primera vez: '+dm(p.t)+' '+hm(p.t)+' ('+hace(now-tp)+') · visible durante '+dur((tu||tp)-tp)+' · '+(r.vistas||1)+' lecturas'+(r.max&&r.max.gap>u.gap+0.01?' · máximo '+Math.round(r.max.gap*100)+' %':'')+'</div>';
    h+=refTxt(r);
    return h+estado+'</div>';
  }
  function seg(x){return x?('L20 <b>'+esc(x.l20)+'</b> · L10 <b>'+esc(x.l10)+'</b> · Como '+esc(x.condTxt)+' L10 <b>'+esc(x.cond)+'</b>'):''}
  function refTxt(r){
    var q=r.hist;if(!q)return '';
    if(q.eq||q.jug){var s=seg(q.eq||q.jug);return s?'<div class="pt">Referencia: '+s+'</div>':''}
    var a=seg(q.loc),b=seg(q.vis);if(!a&&!b)return '';
    return '<div class="pt">Referencia · '+esc(r.local)+' (total del partido): '+(a||'sin datos')+'</div><div class="pt">Referencia · '+esc(r.visitante)+' (total del partido): '+(b||'sin datos')+'</div>';
  }
  function sel(id,t,ops,v){
    return '<div><label>'+t+'</label><select onchange="erF(\''+id+'\',this.value)">'+ops.map(function(o){return '<option value="'+esc(o[0])+'"'+(String(o[0])===String(v)?' selected':'')+'>'+esc(o[1])+'</option>'}).join("")+'</select></div>';
  }
  function todos(){
    var h='<h2>Errores de cuota en todos los mercados</h2>';
    if(!ER.data){
      if(!ER.cargando){
        ER.cargando=true;
        fetch("errores.json?t="+Date.now()).then(function(r){return r.json()}).catch(function(){return {sel:{}}}).then(function(j){ER.data=j;ER.cargando=false;if(S.tab==="errores")draw()});
      }
      return h+'<div class="empty">Cargando...</div>';
    }
    h+='<p class="upd">Aquí entran todos los mercados del radar, no solo los seleccionados. Solo salen los que cumplen: cuota hasta 3,00 y al menos un 30 % por encima de la segunda, o cuota mayor de 3,00 y al menos un 70 % (si pasa de 5,00, la segunda cuota tiene que ser menor de 2,50). Primero van las de cuota hasta 3,00 y luego las de más de 3,00, cada grupo de mayor a menor diferencia. Actualizado: '+esc(String(ER.data.actualizado||"").slice(0,16).replace("T"," "))+'</p>';
    var all=ER.data.sel||{},mks={},casas={};
    Object.keys(all).forEach(function(k){var r=all[k];mks[r.mercado]=1;(r.ultima.casas||[]).forEach(function(b){casas[b]=1})});
    var omk=[["","Todos"]].concat(Object.keys(mks).sort().map(function(m){return [m,MK[m]||m]}));
    var oca=[["","Todas"]].concat(Object.keys(casas).sort().map(function(b){return [b,b]}));
    h+='<div class="erf">'+sel("solo","Mostrar",[["act","Apostables ahora"],["todo","Todos (también pasados)"]],ER.f.solo)+sel("mk","Mercado",omk,ER.f.mk)+sel("casa","Casa con la mejor cuota",oca,ER.f.casa)+sel("ord","Ordenar por",[["gap","Mayor diferencia"],["rec","Más recientes publicados"],["ant","Más antiguos publicados"]],ER.f.ord)+sel("pct","Acierto mínimo",[["","Sin filtro"],["30","30 % o más"],["40","40 % o más"],["50","50 % o más"],["60","60 % o más"],["70","70 % o más"],["80","80 % o más"]],ER.f.pct)+(ER.f.pct?sel("vent","Acierto en los últimos",[["10","10 partidos"],["20","20 partidos"]],ER.f.vent):'')+'</div>'+(ER.f.pct?'<p class="upd">Acierto = veces que se cumplió el suceso en esos partidos. En los totales del partido deben cumplirlo los dos equipos. Los errores sin datos de referencia (los registrados antes de esta actualización o con menos de 5 partidos) no salen con este filtro.</p>':'');
    var l=listar();
    h+='<div class="upd">'+l.length+' resultado'+(l.length===1?'':'s')+'</div>';
    return h+(l.length?l.slice(0,80).map(card).join(""):'<div class="empty">Ahora mismo no hay ninguno con estos filtros.</div>');
  }
  window.erS=function(s){ER.sub=s;if(s==="todos")ER.data=null;draw()};
  window.erF=function(k,v){ER.f[k]=v;draw()};
  var e0=errores;
  errores=function(){
    var h='<div class="chips"><button class="'+(ER.sub==="sel"?"on":"")+'" onclick="erS(\'sel\')">Selecciones</button><button class="'+(ER.sub==="todos"?"on":"")+'" onclick="erS(\'todos\')">Todos los mercados</button></div>';
    return h+(ER.sub==="todos"?todos():e0());
  };
})();
