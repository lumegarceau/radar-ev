(function(){
  var s=document.createElement("style");
  s.textContent=".t5c{white-space:nowrap}.t5c b{margin:0 2px;font-size:15px}";
  document.head.appendChild(s);
  var d0=deHist;
  deHist=function(r){
    var o=d0(r);
    o.duda=r.duda;
    return o;
  };
  var b0=bd;
  bd=function(c){
    var h=b0(c);
    if(c.duda&&c.estado==="pendiente"&&!c.empez){
      h+='<span class="bd">Duda: '+esc(c.duda)+'</span>';
    }
    return h;
  };
  var r0=resultados;
  resultados=function(){
    var h=r0();
    if(R.data===null)return h;
    var sec=t5Html();
    var i=h.indexOf("<h2>Calibración");
    if(i<0)return h+sec;
    return h.slice(0,i)+sec+h.slice(i);
  };
})();
function sg5(r){
  if(r.estado==="ganada")return '<b class="pos">✓</b>';
  if(r.estado==="perdida")return '<b class="neg">✗</b>';
  if(r.estado==="nula")return '<b class="gr">–</b>';
  return '<b class="gr">·</b>';
}
function top5(L,key){
  return L.slice().sort(function(a,b){return key(b)-key(a)}).slice(0,5);
}
function ln5(nom,a){
  var res=a.g+a.p;
  var roi=res?Math.round(a.b*100/res)+"%":"-";
  return [nom,a.g,a.p,a.n,pct(a.g,res),bn(a.b),roi];
}
function t5Html(){
  var rows=R.data.filter(function(r){
    return okT(r)&&r.vigente!==false&&enPer(fmd(r))&&cuo(r)>0;
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
  var A={p:acc(),e:acc(),t:acc()},fila=[];
  dias.forEach(function(d){
    var L=D[d];
    var tp=top5(L,function(r){return r.prob});
    var te=top5(L,function(r){return r.prob*cuo(r)-1});
    var a1=acc(),a2=acc();
    tp.forEach(function(r){suma(a1,r);suma(A.p,r)});
    te.forEach(function(r){suma(a2,r);suma(A.e,r)});
    L.forEach(function(r){suma(A.t,r)});
    fila.push([
      d.slice(8)+"/"+d.slice(5,7),
      '<span class="t5c">'+tp.map(sg5).join("")+'</span>',
      bn(a1.b),
      '<span class="t5c">'+te.map(sg5).join("")+'</span>',
      bn(a2.b)
    ]);
  });
  var h="<h2>Rendimiento de los Top 5</h2>";
  h+=tabla(["Lista","G","P","N","Acierto","Benef.","ROI"],[ln5("Top 5 prob.",A.p),ln5("Top 5 EV",A.e),ln5("Todas",A.t)]);
  h+='<p class="upd">Cada Top 5 se calcula al cierre del día con los datos finales y la cuota elegida arriba (Máxima, Primera o Última). Puede diferir de lo que se veía en la web a una hora concreta. Con pocos días el dato no es fiable.</p>';
  h+="<h2>Top 5 por día</h2>"+tabla(["Día","Prob.","Benef.","EV","Benef."],fila.slice(0,31));
  return h;
}
load();
