(function(){
  var s=document.createElement("style");
  s.textContent=".k2b{padding-right:34px;box-sizing:border-box}.k2b .thr span{right:2px;top:-9px;background:#fff}";
  document.head.appendChild(s);
})();
camisaSvg=function(c,col,nombre){
  var ap=apellido(nombre),n=c.num;
  var fs=Math.max(3.2,Math.min(5.2,22/(Math.max(ap.length,1)*0.66)));
  var h='<svg class="k2s" viewBox="0 0 64 64" aria-hidden="true">';
  h+='<path id="shp" d="'+SHIRT+'" fill="'+col+'" stroke="rgba(0,0,0,.2)" stroke-width="1"/>';
  h+='<g id="sht" fill="'+txtCol(col)+'" font-family="system-ui,Arial,sans-serif" font-weight="800" text-anchor="middle">';
  if(n){
    h+='<text x="32" y="24" font-size="'+fs+'">'+esc(ap)+'</text>';
    h+='<text x="32" y="46" font-size="'+(String(n).length>1?20:25)+'">'+esc(n)+'</text>';
  }else{
    var fz=Math.max(3.4,Math.min(7,22/(Math.max(ap.length,1)*0.66)));
    h+='<text x="32" y="38" font-size="'+fz+'">'+esc(ap)+'</text>';
  }
  return h+'</g></svg>';
};
shirt=function(x,col,c,nombre,a,b,s){
  var p=new Path2D(SHIRT);
  x.save();
  x.translate(a,b);
  x.scale(s/64,s/64);
  x.fillStyle=col;
  x.fill(p);
  x.strokeStyle="rgba(0,0,0,.2)";
  x.lineWidth=1.2;
  x.stroke(p);
  x.restore();
  var tc=txtCol(col),k=s/64,cx=a+32*k;
  if(c.num){
    fitTx(x,apellido(nombre),cx,b+24*k,22*k,5.2*k,tc,3*k);
    fitTx(x,String(c.num),cx,b+46*k,22*k,(String(c.num).length>1?20:25)*k,tc,8);
  }else{
    fitTx(x,apellido(nombre),cx,b+38*k,22*k,7*k,tc,3*k);
  }
};
if(S.data.length)draw();
