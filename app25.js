var TOP_MIN_PARTIDOS=3;
var TOP_MIN_SEL=5;
(function(){
  var t0=top5g;
  function evOf(r){
    if(typeof r.ev==="number")return r.ev;
    return r.prob*cuo(r)-1;
  }
  top5g=function(rows,key){
    var fx={};
    rows.forEach(function(r){fx[r.fixture]=1});
    if(Object.keys(fx).length<TOP_MIN_PARTIDOS)return [];
    var pos=rows.filter(function(r){return evOf(r)>0});
    var out=t0(pos,key);
    return out.length<TOP_MIN_SEL?[]:out;
  };
  var b0=topBox;
  topBox=function(t,a,fn){
    if(a&&a.length)return b0(t,a,fn);
    return '<div class="box"><h3>'+t+'</h3><div class="upd" style="padding:8px 0">Sin Top 5: este día hay pocos partidos o no hay suficientes selecciones con EV positivo.</div></div>';
  };
  var r0=resultados;
  resultados=function(){
    var h=r0();
    return h.replace(/<tr><td>[^<]*<\/td><td><span class="t5c"><\/span><\/td><td><span class="gr">–<\/span><\/td><td><span class="t5c"><\/span><\/td><td><span class="gr">–<\/span><\/td><\/tr>/g,"");
  };
})();
if(S.tab==="resultados"||S.tab==="radar")draw();
// fin
