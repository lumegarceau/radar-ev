var FT="todo";
var TIPOS=[["todo","Todo"],["eq_over","Equipos +"],["eq_under","Equipos -"],["total_over","Totales +"],["total_under","Totales -"],["jugador","Jugadores"]];
(function(){
  var s=document.createElement("style");
  s.textContent=".dual{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px}.dual .cr{width:38px;height:38px;margin:0}";
  document.head.appendChild(s);
})();
function tkey(c){
  var t=c.tipo||"equipo";
  if(t==="jugador")return "jugador";
  var u=c.sentido==="under"?"_under":"_over";
  return (t==="total"?"total":"eq")+u;
}
function okT(c){return FT==="todo"||tkey(c)===FT}
function sT(x){FT=x;draw()}
(function(){
  var d1=deHist;
  deHist=function(r){
    var o=d1(r);
    o.sentido=r.sentido;
    return o;
  };
  var r0=radar;
  radar=function(){
    var all=S.data;
    S.data=all.filter(okT);
    var h;
    try{h=r0()}finally{S.data=all}
    return chips(TIPOS,FT,"sT")+h;
  };
  var s0=resultados;
  resultados=function(){
    if(R.data===null)return s0();
    var all=R.data;
    R.data=all.filter(okT);
    var h;
    try{h=s0()}finally{R.data=all}
    return chips(TIPOS,FT,"sT")+h;
  };
  var f0=datosFicha;
  datosFicha=function(c){
    var d=f0(c);
    if(c.sentido==="under"&&!d.J){
      d.hit=function(v){return v<c.linea};
      d.h10=d.ult.filter(d.hit).length;
    }
    return d;
  };
  etq=function(c,d){
    if(d.J)return c.linea+"+";
    return (c.sentido==="under"?"<":"+")+String(c.linea).replace(".",",");
  };
  var cs0=camisaSvg;
  camisaSvg=function(c,col,nombre){
    if(c.tipo==="total")return '<div class="k2s dual">'+cr(c.hid)+cr(c.aid)+'</div>';
    return cs0(c,col,nombre);
  };
})();
load();
