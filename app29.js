// Estadísticas: sección independiente de errores de cuota (con clasificación y subpestaña por casa)
// y clasificación por casas de las selecciones. No cambia ninguna cifra existente.
var ES={sec:"sel",casa:""};
(function(){
  var MKE={corners:"córners",cards:"tarjetas",fouls:"faltas",shots:"remates",sot:"remates a puerta",goals:"goles",drawn:"faltas recibidas",saves:"paradas",tk:"entradas"};
  var TPE={jugador:"Jugador",equipo:"Equipo",total:"Total del partido"};
  function okE(x){if(x.c>5&&x.ref>=2.5)return false;return x.c<=3?x.gap>=0.30:x.gap>=0.70}
  function credE(r){return (r.serie||[]).some(okE)||okE(r.primera)}
  function casaDe(r,fb){var s=r[R.base]||r.primera||{};return (s.casas&&s.casas[0])||"—"}
  function fila(n,a,extra){
    var res=a.g+a.p;
    var cls=res<30?' style="color:var(--mu)"':"";
    return ['<span'+cls+'>'+esc(n)+'</span>',a.g+a.p+a.n+a.pen+a.rev,a.g,a.p,a.n,a.pen+a.rev,pct(a.g,res),bn(a.b),res?Math.round(a.b*100/res)+"%":"-"];
  }
  var CAB=["","Total","G","P","N","Pte.","Acierto","Benef.","ROI"];
  function grupos(L,fn,orden){
    var G={};
    L.forEach(function(r){var k=fn(r);if(k==null)return;suma(G[k]=G[k]||acc(),r)});
    var ks=orden||Object.keys(G).sort(function(a,b){
      var A=G[a],B=G[b];return (B.g+B.p+B.n+B.pen+B.rev)-(A.g+A.p+A.n+A.pen+A.rev)});
    return ks.filter(function(k){return G[k]}).map(function(k){return fila(k,G[k])});
  }
  function cargaE(){
    if(ER.data||ER.cargando)return;
    ER.cargando=true;
    fetch("errores.json?t="+Date.now()).then(function(r){return r.json()}).catch(function(){return {sel:{}}}).then(function(j){ER.data=j;ER.cargando=false;if(S.tab==="resultados")draw()});
  }
  function errStats(){
    var h='<h2>Errores de cuota</h2><p class="upd">Estadísticas de los errores de todos los mercados que cumplen el filtro de la app (cuota hasta 3,00 con 30 % o más; más de 3,00 con 70 % o más). Aparte de las estadísticas de selecciones y de los Top 5. Se cuenta 1 unidad por error a la cuota elegida abajo.</p>';
    h+=chips(PERS,R.per,"rP");
    h+='<div class="upd">Cuota usada en el balance</div>'+chips(BASES,R.base,"rB");
    if(!ER.data){cargaE();return h+'<div class="empty">Cargando...</div>'}
    var all=Object.keys(ER.data.sel||{}).map(function(k){return ER.data.sel[k]});
    var base=all.filter(function(r){return credE(r)&&enPer(fmd(r))&&cuo(r)>0});
    var casas={};base.forEach(function(r){casas[casaDe(r)]=1});
    var lc=[["","Todas"]].concat(Object.keys(casas).sort().map(function(c){return [c,c]}));
    if(ES.casa&&!casas[ES.casa])ES.casa="";
    h+='<div class="upd">Casa</div>'+chips(lc,ES.casa,"esC");
    var L=ES.casa?base.filter(function(r){return casaDe(r)===ES.casa}):base;
    var A=acc();L.forEach(function(r){suma(A,r)});
    var res=A.g+A.p;
    h+='<div class="sum"><div><span>Acierto</span><b>'+pct(A.g,res)+'</b></div><div><span>Beneficio</span>'+bn(A.b)+'</div><div><span>ROI</span><b>'+(res?Math.round(A.b*100/res)+"%":"-")+'</b></div></div>';
    h+='<div class="upd">'+L.length+' detectados · '+A.g+' ganados · '+A.p+' perdidos · '+A.n+' nulos (suplente o suspendido) · '+(A.pen+A.rev)+' pendientes. Se resuelven unas 3 horas después del partido.</div>';
    if(!ES.casa){
      h+='<h3 class="h3r">Clasificación por casas (quién da la cuota más alta)</h3><div class="upd">En gris, menos de 30 resueltas: aún no es fiable.</div>';
      h+=tabla(CAB,grupos(L,function(r){return casaDe(r)}));
    }
    h+='<h3 class="h3r">Por tramo de cuota</h3>';
    var N=["hasta 2,00","2,00 a 3,00","3,00 a 5,00","más de 5,00"];
    h+=tabla(CAB,grupos(L,function(r){var c=cuo(r);return c<=2?N[0]:c<=3?N[1]:c<=5?N[2]:N[3]},N));
    h+='<h3 class="h3r">Por mercado</h3>'+tabla(CAB,grupos(L,function(r){return (TPE[r.tipo]||r.tipo)+" · "+(MKE[r.mercado]||r.mercado)}));
    h+='<h3 class="h3r">Por tipo</h3>'+tabla(CAB,grupos(L,function(r){return TPE[r.tipo]||r.tipo}));
    var D=L.slice().sort(function(a,b){return String(b.primera.t).localeCompare(String(a.primera.t))}).slice(0,30);
    if(D.length){
      var ic={ganada:"✓ ganada",perdida:"✗ perdida",nula:"nula",pendiente:"pendiente",revisar:"a revisar"};
      h+='<h3 class="h3r">Últimos errores'+(ES.casa?' de '+esc(ES.casa):'')+'</h3>';
      h+=tabla(["Día","Suceso","Cuota","Casa","Resultado"],D.map(function(r){
        return [String(r.inicio).slice(8,10)+"/"+String(r.inicio).slice(5,7),esc(r.suceso),String(cuo(r).toFixed(2)).replace(".",","),esc(casaDe(r)),ic[r.estado]||r.estado];
      }));
    }
    h+='<p class="upd">Ojo: con pocos datos no se puede sacar conclusiones. Un error de cuota no garantiza ganar dinero: las casas pueden limitar la apuesta, anularla o corregir la cuota.</p>';
    return h;
  }
  function rankSel(){
    if(!R.data||!R.data.length)return "";
    var all=R.data.filter(function(r){return RV.f.ver===""||(r.regla||"v0")===RV.f.ver});
    var pub=pubSet(all);
    var L=all.filter(function(r){return pub[kf(r)]&&enPer(fmd(r))&&cuo(r)>0});
    var rows=grupos(L,function(r){var b=(r[R.base]||{}).b;return b||null});
    if(!rows.length)return "";
    return '<h2>Clasificación por casas</h2><div class="upd">Casa que daba la mejor cuota en cada selección publicada. Sigue el periodo y la cuota de arriba. En gris, menos de 30 resueltas.</div>'+tabla(CAB,rows);
  }
  window.esS=function(s){ES.sec=s;draw();window.scrollTo(0,0)};
  window.esC=function(c){ES.casa=c;draw()};
  var r1=resultados;
  resultados=function(){
    var sw='<div class="chips"><button class="'+(ES.sec==="sel"?"on":"")+'" onclick="esS(\'sel\')">Selecciones</button><button class="'+(ES.sec==="err"?"on":"")+'" onclick="esS(\'err\')">Errores de cuota</button></div>';
    if(ES.sec==="err")return sw+errStats();
    var h=r1();
    var rk="";
    try{rk=rankSel()}catch(e){}
    return sw+h+rk;
  };
})();
