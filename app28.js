// Errores de cuota de TODOS los mercados (subpestaña). No toca la lista de siempre.
var ER={sub:"sel",data:null,cargando:false,f:{mk:"",casa:"",solo:"act",ord:"gap",pct:"",vent:"10",rev:"pend"},fs:"pub",fp:"fut",limpio:false,s:{casa:"",cmin:"",cmax:"",emin:"",dmin:"",ord:"gap"},p:{casa:"",cmin:"",cmax:"",dmin:"",ord:"pub"}};
(function(){
  var s=document.createElement("style");
  s.textContent=".erc{border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin:8px 0;background:#fff}"+
  ".erc h4{margin:0 0 2px;font-size:15px}.erc .pt{font-size:12px;color:var(--mu)}"+
  ".erc .ch{display:flex;flex-wrap:wrap;gap:4px;margin:6px 0}"+
  ".erc .ch span{font-size:12px;border:1px solid var(--line);border-radius:12px;padding:2px 8px;color:var(--mu)}"+
  ".erc .ch span.b{background:var(--ac);color:#fff;border-color:var(--ac)}"+
  ".erc .est{font-size:12px;margin-top:4px}.erc .est.ok{color:#0a7a2f;font-weight:600}.erc .est.no{color:var(--mu)}"+
  ".erf{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0}.erf label{font-size:12px;color:var(--mu)}"+
  ".erb{display:flex;gap:8px;margin-top:8px;align-items:center}.erb button{flex:1;padding:9px;border-radius:8px;border:1px solid var(--line);font:inherit;font-weight:700;background:#fff;color:var(--tx)}"+
  ".erb button.y{background:#0a7a2f;border-color:#0a7a2f;color:#fff}.erb button.n{color:#b42318;border-color:#e4b4b0}.erb .erp{font-size:12px;font-weight:700;color:#0a7a2f}.erb .erp.no{color:#b42318}"+
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
  function adm(){return !!(window.CUENTA&&CUENTA.admin)}
  function cur(){return (window.CUENTA&&CUENTA.cur)||{ok:{},no:{}}}
  // seleccion: manual (Firebase) + automatica (la decide el detector). Lo manual manda sobre lo automatico.
  var DESDE_MANUAL=Date.parse("2026-11-21T00:30:00+01:00");
  window.DESDE_MANUAL=DESDE_MANUAL;
  window.efPub=function(r){var c=cur();if(c.no[r._k])return false;if(c.ok[r._k])return true;return !!(r.auto&&r.auto.ok)};
  window.pubTs=function(r){var c=cur();if(c.ok[r._k])return c.ok[r._k];return (r.auto&&T(r.auto.t))||0};
  function curLista(){var C=window.CUENTA;return !C||!C.ok||(C.cur&&C.cur.cargado)}
  function cargarER(){
    if(ER.cargando)return;
    ER.cargando=true;
    fetch("errores.json?t="+Date.now()).then(function(r){return r.json()}).catch(function(){return {sel:{}}}).then(function(j){ER.data=j;ER.cargando=false;if(S.tab==="errores")draw()});
  }
  function botones(r,modo){
    if(!adm())return '';
    var k=encodeURIComponent(r._k).replace(/'/g,"%27"),c=cur();
    function b(t,e,cl){return '<button type="button" class="'+cl+'" onclick="erM(decodeURIComponent(\''+k+'\'),\''+e+'\')">'+t+'</button>'}
    function hh(t){var d=new Date(t);return isNaN(d)?'':' '+('0'+d.getDate()).slice(-2)+'/'+('0'+(d.getMonth()+1)).slice(-2)+' '+('0'+d.getHours()).slice(-2)+':'+('0'+d.getMinutes()).slice(-2)}
    function etq(){
      if(c.ok[r._k])return '<span class="erp">Publicado'+hh(c.ok[r._k])+'</span>';
      if(c.no[r._k])return '<span class="erp no">Descartado'+hh(c.no[r._k])+'</span>';
      var a=r.auto;if(!a)return '';
      var ev=a.ev!=null?' · EV '+(a.ev>=0?'+':'')+Math.round(a.ev*100)+'%':'';
      return a.ok?'<span class="erp">Automático: publicado'+ev+'</span>':'<span class="erp no">Automático: descartado ('+esc(a.m||'')+ev+')</span>';
    }
    if(modo==="todos")return '<div class="erb">'+etq()+b('✓ Es error','ok','y')+b('✗ Descartar','no','n')+'</div>';
    if(modo==="pub")return '<div class="erb">'+etq()+b('Quitar y descartar','no','n')+'</div>';
    if(modo==="desc")return '<div class="erb">'+etq()+b('✓ Publicar','ok','y')+'</div>';
    return '';
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
  // al menos 10 partidos como titular de referencia (el L10 solo cuenta partidos de titular con 45+ min)
  function titOk(r){
    var q=r.hist;if(!q)return false;
    var ps=(q.eq||q.jug)?[q.eq||q.jug]:[q.loc,q.vis];
    for(var i=0;i<ps.length;i++){
      if(!ps[i])return false;
      var a=kn(ps[i].l10);
      if(!a||a[1]<10)return false;
    }
    return true;
  }
  function listar(){
    var d=ER.data&&ER.data.sel||{},now=Date.now(),f=ER.f;
    return Object.keys(d).map(function(k){var r=d[k];r._k=k;return r}).filter(function(r){
      if(!cred(r,f.solo==="act"))return false;
      if(!titOk(r))return false;
      if(f.mk&&r.mercado!==f.mk)return false;
      if(f.casa&&!((r.primera.casas||[]).concat(r.ultima.casas||[])).some(function(b){return b===f.casa}))return false;
      if(f.solo==="act"&&!(r.activo&&T(r.inicio)>now))return false;
      if(f.rev==="pend"&&(cur().ok[r._k]||cur().no[r._k]))return false;
      if(f.pct){var t=tasaR(r,f.vent);if(t==null||t*100<Number(f.pct)-0.001)return false}
      return true;
    }).sort(function(a,b){
      if(f.ord==="rec"||f.ord==="ant"){var d=(T(b.primera.t)||0)-(T(a.primera.t)||0);return f.ord==="rec"?d:-d}
      var ga=a.ultima.c>3?1:0,gb=b.ultima.c>3?1:0;return ga!==gb?ga-gb:b.ultima.gap-a.ultima.gap});
  }
  function card(r,modo){
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
    return h+estado+botones(r,modo)+'</div>';
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
  function selG(g,id,t,ops,v){
    return '<div><label>'+t+'</label><select onchange="erG(\''+g+'\',\''+id+'\',this.value)">'+ops.map(function(o){return '<option value="'+esc(o[0])+'"'+(String(o[0])===String(v)?' selected':'')+'>'+esc(o[1])+'</option>'}).join("")+'</select></div>';
  }
  function todos(){
    var h='<h2>Errores de cuota en todos los mercados</h2>';
    if(!ER.data){cargarER();return h+'<div class="empty">Cargando...</div>'}
    if(!curLista()){CUENTA.curCargar();return h+'<div class="empty">Cargando...</div>'}
    h+='<p class="upd">Aquí entran todos los mercados del radar, no solo los seleccionados. Solo salen los que cumplen: cuota hasta 3,00 y al menos un 30 % por encima de la segunda, o cuota mayor de 3,00 y al menos un 70 % (si pasa de 5,00, la segunda cuota tiene que ser menor de 2,50). Primero van las de cuota hasta 3,00 y luego las de más de 3,00, cada grupo de mayor a menor diferencia. Actualizado: '+esc(String(ER.data.actualizado||"").slice(0,16).replace("T"," "))+'</p>';
    var all=ER.data.sel||{},mks={},casas={};
    Object.keys(all).forEach(function(k){var r=all[k];mks[r.mercado]=1;(r.ultima.casas||[]).forEach(function(b){casas[b]=1})});
    var omk=[["","Todos"]].concat(Object.keys(mks).sort().map(function(m){return [m,MK[m]||m]}));
    var oca=[["","Todas"]].concat(Object.keys(casas).sort().map(function(b){return [b,b]}));
    h+='<div class="erf">'+sel("solo","Mostrar",[["act","Apostables ahora"],["todo","Todos (también pasados)"]],ER.f.solo)+sel("rev","Revisión",[["pend","Pendientes de revisar"],["todo","Todos (también ya revisados)"]],ER.f.rev)+sel("mk","Mercado",omk,ER.f.mk)+sel("casa","Casa con la mejor cuota",oca,ER.f.casa)+sel("ord","Ordenar por",[["gap","Mayor diferencia"],["rec","Más recientes publicados"],["ant","Más antiguos publicados"]],ER.f.ord)+sel("pct","Acierto mínimo",[["","Sin filtro"],["30","30 % o más"],["40","40 % o más"],["50","50 % o más"],["60","60 % o más"],["70","70 % o más"],["80","80 % o más"]],ER.f.pct)+(ER.f.pct?sel("vent","Acierto en los últimos",[["10","10 partidos"],["20","20 partidos"]],ER.f.vent):'')+'</div>'+(ER.f.pct?'<p class="upd">Acierto = veces que se cumplió el suceso en esos partidos. En los totales del partido deben cumplirlo los dos equipos. Los errores sin datos de referencia (los registrados antes de esta actualización o con menos de 5 partidos) no salen con este filtro.</p>':'');
    var l=listar();
    h+='<div class="upd">'+l.length+' resultado'+(l.length===1?'':'s')+'</div>';
    return h+(l.length?l.slice(0,80).map(function(r){return card(r,"todos")}).join(""):'<div class="empty">Ahora mismo no hay ninguno con estos filtros.</div>');
  }
  function numG(g,id,t,v){
    return '<div><label>'+t+'</label><input type="number" inputmode="decimal" step="0.01" value="'+esc(v)+'" onchange="erG(\''+g+'\',\''+id+'\',this.value)" style="display:block;width:100%;box-sizing:border-box;margin-top:3px;padding:8px;border:1px solid var(--line);border-radius:6px;font:inherit;color:var(--tx);background:#fff"></div>';
  }
  function num(x){x=String(x==null?"":x).replace(",",".").trim();if(x==="")return null;var n=Number(x);return isNaN(n)?null:n}
  // casas = casas con la mejor cuota; cuota; ev (fraccion o null); gap (fraccion)
  function pasa(f,casas,cuota,ev,gap){
    if(f.casa&&casas.indexOf(f.casa)<0)return false;
    var a=num(f.cmin),b=num(f.cmax),e=num(f.emin),dm=num(f.dmin);
    if(a!=null&&cuota<a-1e-9)return false;
    if(b!=null&&cuota>b+1e-9)return false;
    if(e!=null&&(ev==null||ev*100<e-1e-9))return false;
    if(dm!=null&&(gap==null||gap*100<dm-1e-9))return false;
    return true;
  }
  function ordenar(l,ord,fc,fe,fi,fg){
    var k={ev:function(x){return -(fe(x)==null?-1e9:fe(x))},gap:function(x){return -(fg(x)||0)},cu:function(x){return -fc(x)},cd:function(x){return fc(x)},hi:function(x){return fi(x)||1e18},hl:function(x){return -(fi(x)||0)}}[ord];
    if(k)l.sort(function(a,b){return k(a)-k(b)});
    return l;
  }
  var ORD_S=[["gap","Mayor diferencia de cuota"],["ev","EV (mayor)"],["cu","Cuota (mayor)"],["cd","Cuota (menor)"],["hi","Hora de inicio (más próxima)"],["hl","Hora de inicio (más lejana)"]];
  var ORD_P=[["pub","Más recientes publicados"],["gap","Mayor diferencia de cuota"],["cu","Cuota (mayor)"],["cd","Cuota (menor)"],["hi","Hora de inicio (más próxima)"],["hl","Hora de inicio (más lejana)"]];
  function formG(g,f,casas,ords,conEv){
    var oc=[["","Todas"]].concat(casas.sort().map(function(b){return [b,b]}));
    return '<div class="erf">'+selG(g,"casa","Casa con la mejor cuota",oc,f.casa)+selG(g,"ord","Ordenar por",ords,f.ord)+numG(g,"cmin","Cuota mínima",f.cmin)+numG(g,"cmax","Cuota máxima",f.cmax)+numG(g,"dmin","Diferencia mínima (%)",f.dmin)+(conEv?numG(g,"emin","EV mínimo (%)",f.emin):'')+'</div>';
  }
  function selec(){
    var f=ER.s,h='<h2>Posibles errores de cuota</h2><p class="upd">Selecciones donde la mejor cuota supera en más de un 25 % a la segunda. Puede que una casa haya calculado mal la probabilidad. La diferencia es sobre la segunda cuota; el EV es el del modelo con la mejor cuota.</p>';
    var base=S.data.filter(function(c){return c.gap>0.25&&!c.empez});
    var casas={};base.forEach(function(c){casas[c.best.b]=1});
    h+=formG("s",f,Object.keys(casas),ORD_S,true);
    var l=base.filter(function(c){return pasa(f,[c.best.b],c.best.c,c.ev,c.gap)});
    ordenar(l,f.ord,function(c){return c.best.c},function(c){return c.ev},function(c){return c.fin},function(c){return c.gap});
    h+='<div class="upd">'+l.length+' resultado'+(l.length===1?'':'s')+'</div>';
    return h+(l.length?l.map(window.card).join(""):'<div class="empty">Ahora mismo no hay ninguno con estos filtros.</div>');
  }
  function fuera(){
    var h='<h2>Errores fuera del radar</h2>';
    if(!ER.data){cargarER();return h+'<div class="empty">Cargando...</div>'}
    if(!curLista()){CUENTA.curCargar();return h+'<div class="empty">Cargando...</div>'}
    var C=window.CUENTA,c=cur(),d=ER.data.sel||{},now=Date.now();
    if(C&&C.cur&&C.cur.fallo&&!Object.keys(c.ok).length)return h+'<div class="empty">No se han podido cargar ahora. Vuelve a intentarlo en un rato.</div>';
    if(adm()&&!ER.limpio){
      ER.limpio=true;
      var bor=Object.keys(c.no).filter(function(k){return !d[k]||T(d[k].inicio)<=now});
      if(bor.length)C.curBorrarNo(bor);
    }
    Object.keys(d).forEach(function(k){d[k]._k=k});
    var nd=Object.keys(d).filter(function(k){var r=d[k];if(T(r.inicio)<=now)return false;if(c.no[k])return true;if(c.ok[k])return false;return !!(r.auto&&!r.auto.ok&&r.activo)});
    var pk=Object.keys(d).filter(function(k){return efPub(d[k])});
    if(ER.fs==="desc"&&!adm())ER.fs="pub";
    if(adm())h+='<div class="chips"><button class="'+(ER.fs==="pub"?"on":"")+'" onclick="erSS(\'pub\')">Publicados</button><button class="'+(ER.fs==="desc"?"on":"")+'" onclick="erSS(\'desc\')">Descartes ('+nd.length+')</button></div>';
    if(adm())h+='<div class="erf"><div><label>Reiniciar revisión</label><button type="button" class="n" style="display:block;width:100%;margin-top:3px;padding:9px;border-radius:8px;border:1px solid #e4b4b0;background:#fff;color:#b42318;font:inherit;font-weight:700" onclick="erReset()">Quitar publicados y descartados de partidos sin empezar</button></div></div>';
    var l;
    if(ER.fs==="desc"){
      h+='<p class="upd">Solo lo ves tú. Los descartados se borran solos cuando empieza el partido.</p>';
      h+='<div class="erf">'+selG("d","vent","Devolver a Publicados los descartados en",[["","Elige..."],["15","los últimos 15 minutos"],["60","la última hora"],["180","las últimas 3 horas"],["360","las últimas 6 horas"],["1440","las últimas 24 horas"]],"")+'</div>';
      l=nd.map(function(k){return d[k]}).sort(function(a,b){return (c.no[b._k]||T((b.auto||{}).t)||0)-(c.no[a._k]||T((a.auto||{}).t)||0)});
      h+='<div class="upd">'+l.length+' descartado'+(l.length===1?'':'s')+'</div>';
      return h+(l.length?l.map(function(r){return card(r,"desc")}).join(""):'<div class="empty">No hay descartes pendientes.</div>');
    }
    h+='<p class="upd">Errores de cuota que el radar ha detectado y que pasan un filtro automático: se descartan los que pagan claramente menos de lo que ocurre según los últimos partidos (solo se publican los de EV positivo; si el EV es negativo se descartan) y los de jugadores o equipos con menos de 10 partidos de titular. Son los que cuentan en las estadísticas. Un error de cuota no garantiza ganar dinero: las casas pueden limitar la apuesta, anularla o corregir la cuota.</p>';
    h+='<div class="erf">'+sel("fp","Mostrar",[["fut","Partido sin empezar (también corregidos)"],["act","Apostables ahora"],["todo","Todos (también pasados)"]],ER.fp)+'</div>';
    var casasP={};
    pk.forEach(function(k){var r=d[k];if(r&&r.ultima)(r.ultima.casas||[]).forEach(function(b){casasP[b]=1})});
    h+=formG("p",ER.p,Object.keys(casasP),ORD_P,false);
    l=pk.map(function(k){return d[k]}).filter(function(r){
      return (ER.fp==="todo"||(ER.fp==="fut"?T(r.inicio)>now:(r.activo&&T(r.inicio)>now)))&&pasa(ER.p,r.ultima.casas||[],r.ultima.c,null,r.ultima.gap);
    });
    if(ER.p.ord==="pub")l.sort(function(a,b){return pubTs(b)-pubTs(a)});
    else ordenar(l,ER.p.ord,function(r){return r.ultima.c},null,function(r){return T(r.inicio)},function(r){return r.ultima.gap});
    h+='<div class="upd">'+l.length+' resultado'+(l.length===1?'':'s')+'</div>';
    return h+(l.length?l.slice(0,80).map(function(r){return card(r,"pub")}).join(""):'<div class="empty">Ahora mismo no hay ninguno publicado.</div>');
  }
  window.erM=function(k,e){
    if(!adm())return;
    if(e==="no"&&!confirm("¿Descartar este error?"))return;
    CUENTA.curSet(k,e).then(function(){draw()}).catch(function(){alert("No se ha podido guardar. Comprueba que has entrado con tu cuenta y que las reglas de Firebase están puestas.");draw()});
    draw();
  };
  window.erSS=function(s){ER.fs=s;draw()};
  window.erReset=function(){
    if(!adm())return;
    var c=cur(),d=(ER.data&&ER.data.sel)||{},now=Date.now();
    var ks=Object.keys(c.ok).concat(Object.keys(c.no)).filter(function(k,i,a){return a.indexOf(k)===i&&(!d[k]||T(d[k].inicio)>now)});
    if(!ks.length){alert("No hay nada que reiniciar.");return}
    if(!confirm("Se van a quitar "+ks.length+" errores de Publicados y Descartes (solo de partidos sin empezar) para que vuelvas a revisarlos desde cero. Los de partidos ya jugados no se tocan. ¿Seguro?"))return;
    CUENTA.curVaciar(ks).then(function(){alert("Hecho. Vuelven a salir en Todos los mercados, pendientes de revisar.");draw()}).catch(function(){alert("No se ha podido guardar. Inténtalo otra vez.");draw()});
  };
  window.curCambio=function(){if(S.tab==="errores"||S.tab==="resultados")draw()};
  window.erS=function(s){ER.sub=s;if(s==="todos"||s==="fuera")ER.data=null;if(s==="fuera"&&window.CUENTA)CUENTA.curCargar(true);draw()};
  window.erF=function(k,v){ER.f[k]=v;draw()};
  window.erG=function(g,k,v){
    if(g!=="d"){ER[g][k]=v;draw();return}
    if(!v||!adm())return;
    var c=cur(),d=(ER.data&&ER.data.sel)||{},lim=Date.now()-Number(v)*60000,now=Date.now();
    var ks=Object.keys(c.no).filter(function(k){return d[k]&&T(d[k].inicio)>now&&c.no[k]>=lim});
    if(!ks.length){alert("No hay descartados en ese periodo.");draw();return}
    if(!confirm("Se van a devolver "+ks.length+" errores a Publicados. ¿Seguro?")){draw();return}
    var p=Promise.resolve();
    ks.forEach(function(k){p=p.then(function(){return CUENTA.curSet(k,"ok")})});
    p.then(function(){alert("Hecho: "+ks.length+" errores devueltos a Publicados.");draw()}).catch(function(){alert("No se ha podido guardar todo. Vuelve a intentarlo.");draw()});
  };
  var e0=errores;
  errores=function(){
    if(ER.sub==="todos"&&!adm())ER.sub="sel";
    var h='<div class="chips"><button class="'+(ER.sub==="sel"?"on":"")+'" onclick="erS(\'sel\')">Selecciones</button>'+(adm()?'<button class="'+(ER.sub==="todos"?"on":"")+'" onclick="erS(\'todos\')">Todos los mercados</button>':'')+'<button class="'+(ER.sub==="fuera"?"on":"")+'" onclick="erS(\'fuera\')">Errores fuera radar</button></div>';
    return h+(ER.sub==="todos"?todos():ER.sub==="fuera"?fuera():selec());
  };
})();
