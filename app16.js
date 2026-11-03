function qm(h){return String(h).replace(/ \(Madrid\)/g,"")}
(function(){
  var tb=topBox,cd=card,k0=k2html,t0=tx;
  topBox=function(){return qm(tb.apply(null,arguments))};
  card=function(c){return qm(cd(c))};
  k2html=function(c){return qm(k0(c))};
  fichaHtml=k2html;
  tx=function(x,t,a,b,sz,col,w,al,mw){
    return t0(x,qm(t),a,b,sz,col,w,al,mw);
  };
})();
