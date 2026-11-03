function ln5(nom,a){
  var res=a.g+a.p;
  var roi=res?Math.round(a.b*100/res)+"%":"-";
  return [nom,a.g,a.p,a.n,a.pen+a.rev,pct(a.g,res),bn(a.b),roi];
}
function bnz(a){
  if(a.g+a.p===0)return '<span class="gr">–</span>';
  return bn(a.b);
}
function t5Html(){
  var hoy=hoyS();
  var rows=R.data.filter(function(r){
    return okT(r)&&r.vigente!==false&&enPer(fmd(r))&&fmd(r)<=hoy&&cuo(r)>0;
  });
  var D={};
  rows.forEach(function(r){
    var f=fmd(r);
    (D[f]=D[f]||[]).push(r);
  });
  var dias=Object.keys(D).sort().reverse();
  if(!dias.length){
    return '<h2>Rendimiento de los Top 5</h2><div class="empty">Todavía no hay selecciones en este periodo.</div>';
  }
  var A={p:acc(),e:acc(),g:acc(),t:acc()},fila=[];
  dias.forEach(function(d){
    var L=D[d];
    var tp=top5(L,function(r){return r.prob});
    var te=top5(L,function(r){return r.prob*cuo(r)-1});
    var a1=acc(),a2=acc();
    tp.forEach(function(r){suma(a1,r);suma(A.p,r);suma(A.g,r)});
    te.forEach(function(r){suma(a2,r);suma(A.e,r);suma(A.g,r)});
    L.forEach(function(r){suma(A.t,r)});
    fila.push([
      d.slice(8)+"/"+d.slice(5,7),
      '<span class="t5c">'+tp.map(sg5).join("")+'</span>',
      bnz(a1),
      '<span class="t5c">'+te.map(sg5).join("")+'</span>',
      bnz(a2)
    ]);
  });
  var T=A.t;
  var h="<h2>Rendimiento de los Top 5</h2>";
  h+=tabla(["Lista","G","P","N","Pte.","Acierto","Benef.","ROI"],[
    ln5("Top 5 prob.",A.p),
    ln5("Top 5 EV",A.e),
    ln5("Global (prob. + EV)",A.g)
  ]);
  h+='<p class="upd">Global = las dos listas juntas: 10 selecciones por día (una selección que esté en las dos cuenta dos veces). Pte. = pendientes de jugar o a revisar. El día de hoy es provisional: el Top 5 se recalcula con cada pasada.</p>';
  h+='<p class="upd">Referencia, todas las selecciones del periodo hasta hoy: '+T.g+' ganadas · '+T.p+' perdidas · '+T.n+' nulas · '+(T.pen+T.rev)+' pendientes · beneficio '+bn(T.b)+'.</p>';
  h+="<h2>Top 5 por día</h2>"+tabla(["Día","Prob.","Benef.","EV","Benef."],fila.slice(0,31));
  return h;
}
if(S.tab==="resultados")draw();
