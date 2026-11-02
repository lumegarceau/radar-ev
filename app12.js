(function(){
  var d0=deHist;
  deHist=function(r){
    var o=d0(r);
    o.num=r.num;
    o.pos=r.pos;
    return o;
  };
})();
barras2=function(c,d){
  if(!d.ult.length)return "";
  var L=limites(c,d);
  var t=Math.round(L.thr/L.mx*100);
  var h='<div class="k2f" style="margin-top:8px"><b style="color:var(--tx)">Últimos '+L.u.length+' partidos</b> · de más antiguo a más reciente</div><div class="k2b">';
  L.u.forEach(function(v){
    var p=Math.round(v/L.mx*100);
    var lb=d.hit(v)?p:Math.max(p,t+4);
    h+='<div class="bc"><em style="bottom:calc('+lb+'% + 2px)">'+v+'</em><i class="'+(d.hit(v)?"h":"")+'" style="height:'+p+'%"></i></div>';
  });
  h+='<div class="thr" style="bottom:'+t+'%"><span>'+etq(c,d)+'</span></div></div>';
  return h;
};
load();
