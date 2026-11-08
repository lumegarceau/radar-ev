var RV={f:{ev:"",p:"",c:"",liga:"",mk:"",tipo:"",ver:""},t5:5,dn:10};
(function(){
  var s=document.createElement("style");
  s.textContent=".rf{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0}"+
  ".rf label{font-size:12px;color:var(--mu)}"+
  ".rf select{display:block;width:100%;margin-top:3px;padding:8px;border:1px solid var(--line);border-radius:6px;font:inherit;color:var(--tx);background:#fff}"+
  ".h3r{margin:14px 0 6px;font-size:14px}";
  document.head.appendChild(s);
  var MK={corners:"córners",cards:"tarjetas",fouls:"faltas",shots:"remates",sot:"remates a puerta",goals:"goles",drawn:"faltas recibidas",saves:"paradas",tk:"entradas"};
  var TN={eq_over:"Equipo +",eq_under:"Equipo -",total_over:"Total +",total_under:"Total -",jugador:"Jugador"};
  var RNG={
    ev:{lt10:[-1e9,10],"10_20":[10,20],"20_30":[20,30],"30_50":[30,50],gt50:[50,1e9],ge20:[20,1e9],ge30:[30,1e9]},
    p:{lt65:[0,65],"65_70":[65,70],"70_75":[70,75],"75_80":[75,80],"80_85":[80,85],ge85:[85,101],ge80:[80,101]},
    c:{lt150:[0,1.5],"150_170":[1.5,1.7],"170_200":[1.7,2],ge200:[2,1e9]}
  };
  var OEV=[["","Todos"],["lt10","Menos del 10 %"],["10_20","10 a 20 %"],["20_30","20 a 30 %"],["30_50","30 a 50 %"],["gt50","Más del 50 %"],["ge20","20 % o más"],["ge30","30 % o más"]];
  var OP=[["","Todas"],["lt65","Menos del 65 %"],["65_70","65 a 70 %"],["70_75","70 a 75 %"],["75_80","75 a 80 %"],["80_85","80 a 85 %"],["ge85","85 % o más"],["ge80","80 % o más"]];
  var OC=[["","Todas"],["lt150","Menos de 1,50"],["150_170","1,50 a 1,70"],["170_200","1,70 a 2,00"],["ge200","2,00 o más"]];
  function ver(r){return r.regla||"v0"}
  function okVer(r){return RV.f.ver===""||ver(r)===RV.f.ver}
  function evR(r){return (r.prob*cuo(r)-1)*100}
  function dentro(v,rg){return v>=rg[0]&&v<rg[1]}
  function okF(r){
    var f=RV.f;
    if(f.ev!==""&&!dentro(evR(r),RNG.ev[f.ev]))return false;
    if(f.p!==""&&!dentro(r.prob*100,RNG.p[f.p]))return false;
    if(f.c!==""&&!dentro(cuo(r),RNG.c[f.c]))return false;
    if(f.liga!==""&&r.liga!==f.liga)return false;
    if(f.mk!==""&&r.mercado!==f.mk)return false;
    if(f.tipo!==""&&tkey(r)!==f.tipo)return false;
    return true;
  }
  function hayF(){var f=RV.f;return f.ev!==""||f.p!==""||f.c!==""||f.liga!==""||f.mk!==""||f.tipo!==""}
  function selH(k,tit,ops){
    return '<label>'+tit+'<select onchange="r24f(\''+k+'\',this.value)">'+ops.map(function(o){
      return '<option value="'+esc(o[0])+'"'+(RV.f[k]===o[0]?" selected":"")+'>'+esc(o[1])+'</option>';
    }).join("")+'</select></label>';
  }
  function distintos(arr,fn){
    var m={};
    arr.forEach(function(r){var k=fn(r);if(k!=null&&k!=="")m[k]=1});
    return Object.keys(m).sort();
  }
  function fila(n,a){
    var res=a.g+a.p;
    var cls=res<30?' style="color:var(--mu)"':"";
    return ['<span'+cls+'>'+esc(n)+'</span>',res,a.g,a.p,pct(a.g,res),bn(a.b),res?Math.round(a.b*100/res)+"%":"-"];
  }
  function grupo(lista,fn,orden){
    var G={};
    lista.forEach(function(r){
      if(r.estado!=="ganada"&&r.estado!=="perdida")return;
      var k=fn(r);
      if(k==null)return;
      var a=G[k]=G[k]||acc();
      suma(a,r);
    });
    var ks=orden||Object.keys(G).sort(function(x,y){return (G[y].g+G[y].p)-(G[x].g+G[x].p)});
    return ks.filter(function(k){return G[k]}).map(function(k){return fila(k,G[k])});
  }
  function tramo(v,cortes,nombres){
    for(var i=0;i<cortes.length;i++)if(v<cortes[i])return nombres[i];
    return nombres[cortes.length];
  }
  function ln5(nom,a){
    var res=a.g+a.p;
    return [nom,a.g,a.p,a.n,a.pen+a.rev,pct(a.g,res),bn(a.b),res?Math.round(a.b*100/res)+"%":"-"];
  }
  function bnz(a){
    if(a.g+a.p===0)return '<span class="gr">–</span>';
    return bn(a.b);
  }
  function mas(cur,fn,vals){
    var l=vals.map(function(v){return [String(v),v>=999?"Todos":"Últimos "+v]});
    return chips(l,String(cur),fn);
  }
  function top5Html(allV){
    var hoy=hoyS();
    var rows=allV.filter(function(r){return r.vigente!==false&&enPer(fmd(r))&&fmd(r)<=hoy&&cuo(r)>0});
    var D={};
    rows.forEach(function(r){(D[fmd(r)]=D[fmd(r)]||[]).push(r)});
    var dias=Object.keys(D).sort().reverse();
    if(!dias.length)return '<h2>Rendimiento de los Top 5</h2><div class="empty">Todavía no hay selecciones en este periodo.</div>';
    var A={p:acc(),e:acc(),g:acc()},fl=[];
    dias.forEach(function(d){
      var L=D[d];
      var tp=top5g(L,function(r){return r.prob});
      var te=top5g(L,function(r){return r.prob*cuo(r)-1});
      var a1=acc(),a2=acc();
      tp.forEach(function(r){suma(a1,r);suma(A.p,r);suma(A.g,r)});
      te.forEach(function(r){suma(a2,r);suma(A.e,r);suma(A.g,r)});
      fl.push([d.slice(8)+"/"+d.slice(5,7),'<span class="t5c">'+tp.map(sg5).join("")+'</span>',bnz(a1),'<span class="t5c">'+te.map(sg5).join("")+'</span>',bnz(a2)]);
    });
    var h="<h2>Rendimiento de los Top 5</h2>";
    h+=tabla(["Lista","G","P","N","Pte.","Acierto","Benef.","ROI"],[ln5("Top 5 prob.",A.p),ln5("Top 5 EV",A.e),ln5("Global (prob. + EV)",A.g)]);
    h+='<p class="upd">Global = las dos listas juntas: 10 selecciones por día. Pte. = pendientes de jugar o a revisar. El día de hoy es provisional: el Top 5 se recalcula con cada pasada. Estos datos no dependen de los filtros de abajo.</p>';
    h+='<h3 class="h3r">Top 5 por día</h3>'+tabla(["Día","Prob.","Benef.","EV","Benef."],fl.slice(0,RV.t5));
    if(fl.length>5)h+=mas(RV.t5,"r24t",[5,10,20,999]);
    return h;
  }
  window.r24f=function(k,v){RV.f[k]=v;draw()};
  window.r24t=function(v){RV.t5=+v;draw()};
  window.r24d=function(v){RV.dn=+v;draw()};
  window.r24x=function(){
    var v=RV.f.ver;
    RV.f={ev:"",p:"",c:"",liga:"",mk:"",tipo:"",ver:v};
    draw();
  };
  resultados=function(){
    if(R.data===null){
      if(!R.cargando){
        R.cargando=true;
        fetch("historial.json?"+Date.now())
          .then(function(r){return r.json()})
          .then(function(j){R.data=Object.values((j&&j.sel)||{})})
          .catch(function(){R.data=[]})
          .then(function(){if(S.tab==="resultados")draw()});
      }
      return '<h2>Resultados</h2><div class="empty">Cargando…</div>';
    }
    var all=R.data;
    var allV=all.filter(okVer);
    var pub=pubSet(allV);
    var base=allV.filter(function(r){return pub[kf(r)]&&enPer(fmd(r))&&cuo(r)>0});
    var L=base.filter(okF);
    var h="<h2>Resultados</h2>"+chips(PERS,R.per,"rP");
    h+='<div class="upd">Cuota usada en el balance</div>'+chips(BASES,R.base,"rB");
    var vs=distintos(all,ver);
    var oligas=[["","Todas"]].concat(distintos(base,function(r){return r.liga}).map(function(x){return [x,x]}));
    var omk=[["","Todos"]].concat(distintos(base,function(r){return r.mercado}).map(function(x){return [x,MK[x]||x]}));
    var otipo=[["","Todos"]].concat(TIPOS.filter(function(t){return t[0]!=="todo"}));
    h+='<div class="rf">'+selH("ev","EV",OEV)+selH("p","Probabilidad",OP)+selH("c","Cuota",OC)+selH("liga","Liga",oligas)+selH("mk","Mercado",omk)+selH("tipo","Tipo",otipo);
    if(vs.length>1)h+=selH("ver","Versión de la regla",[["","Todas"]].concat(vs.map(function(x){return [x,x]})));
    h+='</div>';
    if(hayF())h+='<div class="chips"><button onclick="r24x()">Quitar filtros</button></div>';
    h+='<div class="upd">Los filtros cambian el resumen, ligas, valor, errores de cuota y días. Se cuentan las líneas publicadas en los partidos (la más cercana a 1,83) y las que salieron en los Top 5.</div>';
    var A=acc();
    L.forEach(function(r){suma(A,r)});
    var res=A.g+A.p;
    h+='<div class="sum"><div><span>Acierto</span><b>'+pct(A.g,res)+'</b></div><div><span>Beneficio</span>'+bn(A.b)+'</div><div><span>ROI</span><b>'+(res?Math.round(A.b*100/res)+"%":"-")+'</b></div></div>';
    h+='<div class="upd">'+A.g+" ganadas · "+A.p+" perdidas · "+A.n+" nulas · "+A.pen+" pendientes"+(A.rev?" · "+A.rev+" a revisar":"")+'</div>';
    h+=top5Html(allV);
    h+="<h2>Calibración (todas las resueltas)</h2>";
    R.data=allV;
    try{h+=calib()}finally{R.data=all}
    var cab=["","Sel.","G","P","Acierto","Benef.","ROI"];
    h+='<h2>Por liga</h2><div class="upd">En gris, menos de 30 resueltas: aún no es fiable.</div>'+tabla(cab,grupo(L,function(r){return r.liga}));
    h+='<h2>Dónde está el valor</h2><div class="upd">Solo selecciones resueltas. En gris, menos de 30 resueltas.</div>';
    h+='<h3 class="h3r">Por tramo de EV</h3>';
    var N1=["menos del 10 %","10 a 20 %","20 a 30 %","30 a 50 %","más del 50 %"];
    h+=tabla(cab,grupo(L,function(r){return tramo(evR(r),[10,20,30,50],N1)},N1));
    h+='<h3 class="h3r">Por tramo de probabilidad</h3>';
    var N3=["menos del 65 %","65 a 70 %","70 a 75 %","75 a 80 %","80 a 85 %","85 % o más"];
    h+=tabla(cab,grupo(L,function(r){return tramo(r.prob*100,[65,70,75,80,85],N3)},N3));
    h+='<h3 class="h3r">Por tramo de cuota</h3>';
    var N2=["menos de 1,50","1,50 a 1,70","1,70 a 2,00","2,00 o más"];
    h+=tabla(cab,grupo(L,function(r){return tramo(cuo(r),[1.5,1.7,2],N2)},N2));
    h+='<h3 class="h3r">Por tipo</h3>'+tabla(cab,grupo(L,function(r){return TN[tkey(r)]||tkey(r)}));
    h+='<h3 class="h3r">Por mercado</h3>'+tabla(cab,grupo(L,function(r){return (TN[tkey(r)]||"")+" · "+(MK[r.mercado]||r.mercado)}));
    var e=acc(),o=acc();
    L.forEach(function(r){suma(esErr(r)?e:o,r)});
    function f2(n,a){var rs=a.g+a.p;return [n,a.g,a.p,a.n,pct(a.g,rs),bn(a.b),rs?Math.round(a.b*100/rs)+"%":"-"]}
    h+='<h2>Errores de cuota</h2><div class="upd">Selecciones donde la mejor cuota superó en más de un 25 % a la segunda.</div>';
    h+=tabla(["Grupo","G","P","N","Acierto","Benef.","ROI"],[f2("Con error de cuota",e),f2("Resto",o)]);
    h+='<div class="upd">'+e.pen+' pendientes con error de cuota. Con pocas resueltas, el dato aún no es fiable.</div>';
    var D={};
    L.forEach(function(r){var f=fmd(r);suma(D[f]=D[f]||acc(),r)});
    var kd=Object.keys(D).sort().reverse();
    if(kd.length&&R.per!=="hoy"&&R.per!=="ayer"){
      h+='<h2>Por día</h2>'+tabla(["Día","G","P","N","Acierto","Benef."],kd.slice(0,RV.dn).map(function(k){
        var a=D[k];
        return [k.slice(8)+"/"+k.slice(5,7),a.g,a.p,a.n,pct(a.g,a.g+a.p),bn(a.b)];
      }));
      if(kd.length>10)h+=mas(RV.dn,"r24d",[10,20,999]);
    }
    return h;
  };
})();
if(S.tab==="resultados")draw();
// fin
