(function(){
  var MK={corners:"córners",cards:"tarjetas",fouls:"faltas",shots:"remates",sot:"remates a puerta",goals:"goles",drawn:"faltas recibidas",saves:"paradas",tk:"entradas"};
  var TN={eq_over:"Equipo +",eq_under:"Equipo -",total_over:"Total +",total_under:"Total -",jugador:"Jugador"};
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
  function evR(r){return (r.prob*cuo(r)-1)*100}
  function tramo(v,cortes,nombres){
    for(var i=0;i<cortes.length;i++)if(v<cortes[i])return nombres[i];
    return nombres[cortes.length];
  }
  var r0=resultados;
  resultados=function(){
    var h=r0();
    if(R.data===null)return h;
    var all=R.data;
    var pub=pickRep(all.filter(function(r){return r.vigente!==false&&cuo(r)>0}));
    var D={};
    all.filter(function(r){return r.vigente!==false&&cuo(r)>0}).forEach(function(r){(D[fmd(r)]=D[fmd(r)]||[]).push(r)});
    Object.keys(D).forEach(function(d){
      var a=D[d];
      a.slice().sort(function(x,y){return y.prob-x.prob}).slice(0,5).forEach(function(r){pub[kf(r)]=1});
      a.slice().sort(function(x,y){return (y.prob*cuo(y))-(x.prob*cuo(x))}).slice(0,5).forEach(function(r){pub[kf(r)]=1});
    });
    var L=all.filter(function(r){
      if(!pub[kf(r)]||!enPer(fmd(r))||cuo(r)<=0)return false;
      return (RF.minP===""||r.prob*100>=+RF.minP)&&(RF.minEv===""||evR(r)>=+RF.minEv);
    });
    var cab=["","Sel.","G","P","Acierto","Benef.","ROI"];
    var t='<h2>Dónde está el valor</h2><div class="upd">Solo selecciones resueltas. En gris, menos de 30 resueltas: aún no es fiable.</div>';
    t+='<h3 style="margin:14px 0 6px;font-size:14px">Por tramo de EV</h3>';
    var N1=["menos del 10 %","10 a 20 %","20 a 30 %","30 a 50 %","más del 50 %"];
    t+=tabla(cab,grupo(L,function(r){return tramo(evR(r),[10,20,30,50],N1)},N1));
    t+='<h3 style="margin:14px 0 6px;font-size:14px">Por tramo de cuota</h3>';
    var N2=["menos de 1,50","1,50 a 1,70","1,70 a 2,00","2,00 o más"];
    t+=tabla(cab,grupo(L,function(r){return tramo(cuo(r),[1.5,1.7,2],N2)},N2));
    t+='<h3 style="margin:14px 0 6px;font-size:14px">Por tipo</h3>';
    t+=tabla(cab,grupo(L,function(r){return TN[tkey(r)]||tkey(r)}));
    t+='<h3 style="margin:14px 0 6px;font-size:14px">Por mercado</h3>';
    t+=tabla(cab,grupo(L,function(r){return (TN[tkey(r)]||"")+" · "+(MK[r.mercado]||r.mercado)}));
    return h+t;
  };
})();
if(S.data.length)draw();
