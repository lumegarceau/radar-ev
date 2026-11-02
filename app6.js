var FF="system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif";
function cimg(u){
  return new Promise(function(ok){
    if(!u){ok(null);return}
    var i=new Image();
    i.crossOrigin="anonymous";
    i.onload=function(){ok(i)};
    i.onerror=function(){ok(null)};
    i.src=u;
  });
}
function rr(x,a,b,w,h,r){
  x.beginPath();
  x.moveTo(a+r,b);
  x.arcTo(a+w,b,a+w,b+h,r);
  x.arcTo(a+w,b+h,a,b+h,r);
  x.arcTo(a,b+h,a,b,r);
  x.arcTo(a,b,a+w,b,r);
  x.closePath();
}
function tx(x,t,a,b,sz,col,w,al,mw){
  var s=sz;
  x.font=(w||"600")+" "+s+"px "+FF;
  if(mw){
    while(x.measureText(t).width>mw&&s>14){
      s-=2;
      x.font=(w||"600")+" "+s+"px "+FF;
    }
  }
  x.fillStyle=col;
  x.textAlign=al||"left";
  x.textBaseline="alphabetic";
  x.fillText(t,a,b);
}
function pic(x,im,a,b,w,h){
  if(!im)return;
  var r=Math.min(w/im.width,h/im.height);
  var iw=im.width*r,ih=im.height*r;
  x.drawImage(im,a+(w-iw)/2,b+(h-ih)/2,iw,ih);
}
function dibuja(c){
  var d=datosFicha(c),J=d.J;
  var T=function(id){return id?IMG+"teams/"+id+".png":null};
  var lg=c.lid?IMG+"leagues/"+c.lid+".png":null;
  var fo=(J&&typeof FOTOS!=="undefined"&&FOTOS&&c.pid)?IMG+"players/"+c.pid+".png":null;
  return Promise.all([T(c.hid),T(c.aid),T(c.tid),lg,fo].map(cimg)).then(function(im){
    var W=1080,H=1400;
    var cv=document.createElement("canvas");
    cv.width=W;cv.height=H;
    var x=cv.getContext("2d");
    x.fillStyle="#f4f6f8";x.fillRect(0,0,W,H);
    x.fillStyle="#0f9d58";x.fillRect(0,0,W,16);
    tx(x,"Radar EV",60,100,52,"#18222d","800");
    tx(x,c.liga+" · "+c.hm+" (Madrid)",60,150,28,"#667585","600","left",800);
    pic(x,im[3],W-60-80,50,80,80);
    rr(x,40,190,1000,230,24);
    x.fillStyle="#ffffff";x.fill();
    x.strokeStyle="#e2e7ec";x.lineWidth=2;x.stroke();
    var cx=150,cy=305;
    if(J){
      x.save();
      x.beginPath();x.arc(cx,cy,70,0,Math.PI*2);x.closePath();
      x.fillStyle="#e7f6ee";x.fill();x.clip();
      if(im[4])x.drawImage(im[4],cx-70,cy-70,140,140);
      x.restore();
      if(!im[4])tx(x,ini(d.nombre),cx,cy+20,56,"#0f9d58","800","center");
      tx(x,d.nombre,250,290,56,"#18222d","800","left",760);
      pic(x,im[2],250,318,44,44);
      tx(x,c.equipo||"",306,352,32,"#667585","600","left",660);
    }else{
      if(im[2])pic(x,im[2],cx-70,cy-70,140,140);
      else tx(x,ini(d.nombre),cx,cy+20,56,"#0f9d58","800","center");
      tx(x,d.nombre,250,290,56,"#18222d","800","left",760);
      tx(x,"Juega como "+(c.condTxt||""),250,350,32,"#667585","600");
    }
    rr(x,40,450,1000,100,20);
    x.fillStyle="#eef1f4";x.fill();
    pic(x,im[0],60,470,60,60);
    tx(x,c.local,135,515,32,"#18222d","700","left",330);
    tx(x,"vs",540,515,28,"#667585","600","center");
    tx(x,c.visitante,945,515,32,"#18222d","700","right",330);
    pic(x,im[1],960,470,60,60);
    rr(x,40,580,1000,300,24);
    x.fillStyle="#e7f6ee";x.fill();
    x.fillStyle="#0f9d58";x.fillRect(40,610,10,240);
    tx(x,d.resto,80,660,46,"#18222d","800","left",920);
    tx(x,pc(c.prob),80,790,130,"#0f9d58","800");
    tx(x,"probabilidad estimada",420,775,30,"#667585","600");
    rr(x,80,815,920,16,8);
    x.fillStyle="#cfe5d8";x.fill();
    rr(x,80,815,Math.max(16,920*c.prob),16,8);
    x.fillStyle="#0f9d58";x.fill();
    if(d.ult.length)tx(x,"L10: "+d.h10+"/"+d.ult.length+" aciertos",80,866,32,"#18222d","700");
    var it=[];
    if(c.cond)it.push(["Como "+c.condTxt+" (L10)",c.cond]);
    if(c.l20)it.push(["Últimos 20",c.l20]);
    if(c.rival)it.push(["Rival permite (L20)",c.rival]);
    if(c.media!=null)it.push(["Media",fnum(c.media,2)]);
    if(c.minmed!=null)it.push(["Minutos medios",String(Math.round(c.minmed))]);
    if(c.por90!=null)it.push(["Por 90 min",fnum(c.por90,2)]);
    if(c.tit!=null)it.push(["Titular",c.tit+"%"]);
    it=it.slice(0,6);
    it.forEach(function(p,i){
      var x0=40+(i%3)*340,y0=910+Math.floor(i/3)*115;
      rr(x,x0,y0,320,100,16);
      x.fillStyle="#eef1f4";x.fill();
      tx(x,p[0],x0+20,y0+36,22,"#667585","600","left",280);
      tx(x,p[1],x0+20,y0+82,40,"#18222d","800","left",280);
    });
    if(d.ult.length){
      tx(x,"Últimos resultados (el más reciente, primero)",50,1175,26,"#18222d","700","left",980);
      d.ult.forEach(function(v,i){
        var x0=46+i*100,hit=d.hit(v);
        rr(x,x0,1190,88,60,10);
        x.fillStyle=hit?"#e7f6ee":"#ffffff";x.fill();
        x.strokeStyle=hit?"#0f9d58":"#e2e7ec";x.lineWidth=2;x.stroke();
        tx(x,String(v),x0+44,1232,34,hit?"#0f9d58":"#667585","800","center");
      });
    }
    x.fillStyle="#e2e7ec";x.fillRect(40,1285,1000,2);
    tx(x,SITIO,60,1338,42,"#0f9d58","800","left",960);
    tx(x,"+18 · Juega con responsabilidad · Información estadística, no recomendación de apuesta.",60,1370,22,"#667585","500","left",960);
    tx(x,"Las cuotas pueden cambiar. Comprueba el valor final en la casa de apuestas.",60,1394,22,"#667585","500","left",960);
    return new Promise(function(ok){
      try{cv.toBlob(function(b){ok(b)},"image/png")}catch(e){ok(null)}
    });
  });
}
function mmsg(t){
  var e=document.getElementById("mmsg");
  if(e)e.textContent=t||"";
}
function urlSel(c){
  return "https://"+SITIO+"/?s="+encodeURIComponent(c.k);
}
function bajar(b){
  var a=document.createElement("a");
  a.href=URL.createObjectURL(b);
  a.download="radar-ev.png";
  document.body.appendChild(a);
  a.click();
  a.remove();
}
function listo(){
  if(window._ib===undefined){mmsg("Preparando la imagen… vuelve a pulsar en un momento.");return null}
  if(window._ib===false){mmsg("No se pudo crear la imagen. Prueba a copiar el enlace.");return null}
  mmsg("");
  return window._ib;
}
function compartir(){
  var c=window._fc,b=listo();
  if(!c||!b)return;
  var f=null;
  try{f=new File([b],"radar-ev.png",{type:"image/png"})}catch(e){}
  var t=c.suceso+"\n"+urlSel(c);
  if(f&&navigator.canShare&&navigator.canShare({files:[f]})){
    navigator.share({files:[f],text:t}).catch(function(){});
  }else if(navigator.share){
    navigator.share({text:t}).catch(function(){});
    mmsg("Tu navegador no comparte la imagen: se envía solo el enlace. Usa Descargar imagen para guardarla.");
  }else{
    bajar(b);
    mmsg("Imagen descargada. Copia el enlace para compartirlo.");
  }
}
function descargar(){
  var b=listo();
  if(!b)return;
  bajar(b);
  mmsg("Imagen descargada.");
}
function copiarEnlace(){
  var c=window._fc;
  if(!c)return;
  var u=urlSel(c);
  if(navigator.clipboard&&navigator.clipboard.writeText){
    navigator.clipboard.writeText(u).then(function(){mmsg("Enlace copiado.")},function(){mmsg(u)});
  }else{
    mmsg(u);
  }
}
