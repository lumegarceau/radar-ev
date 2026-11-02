MKN.tk="Entradas";
(function(){
  var s0=shirt;
  shirt=function(x,col,c,nombre,a,b,s){
    if(c.tipo==="total"){
      x.save();
      x.beginPath();
      x.arc(a+s/2,b+s/2,s*0.42,0,Math.PI*2);
      x.fillStyle="#e7f6ee";
      x.fill();
      x.restore();
      fitTx(x,"TOTAL",a+s/2,b+s/2+s*0.07,s*0.64,s*0.2,"#0f9d58",8);
      return;
    }
    s0(x,col,c,nombre,a,b,s);
  };
})();
if(S.data.length)draw();
