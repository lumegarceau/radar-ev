dibuja=function(c){
  var d=datosFicha(c),J=d.J;
  var T=function(id){return id?IMG+"teams/"+id+".png":null};
  var lgu=c.lid?IMG+"leagues/"+c.lid+".png":null;
  var pr=[T(c.hid),T(c.aid),T(c.tid),lgu].map(cimg);
  pr.push(camisaCol(c));
  return Promise.all(pr).then(function(im){
    var col=im[4];
    var W=1080,H=1350;
    var cv=document.createElement("canvas");
    cv.width=W;
    cv.height=H;
    var x=cv.getContext("2d");
    x.fillStyle="#f4f6f8";
    x.fillRect(0,0,W,H);
    x.fillStyle="#0f9d58";
    x.fillRect(0,0,W,14);
    tx(x,"Radar EV",60,92,48,"#18222d","800");
    tx(x,c.liga+" · "+c.hm+" (Madrid)",60,138,26,"#667585","600","left",780);
    pic(x,im[3],W-140,36,80,80);
    rr(x,40,165,1000,230,24);
    x.fillStyle="#ffffff";
    x.fill();
    x.strokeStyle="#e2e7ec";
    x.lineWidth=2;
    x.stroke();
    if(im[2]){
      x.save();
      rr(x,40,165,1000,230,24);
      x.clip();
      x.globalAlpha=0.07;
      pic(x,im[2],700,145,360,360);
      x.restore();
    }
    if(J||!im[2])shirt(x,col,c,d.nombre,70,180,205);
    else pic(x,im[2],70,205,170,170);
    tx(x,d.nombre,300,262,52,"#18222d","800","left",720);
    if(J){
      pic(x,im[2],300,282,40,40);
      tx(x,c.equipo||"",350,314,30,"#667585","600","left",640);
    }else{
      tx(x,"Juega como "+(c.condTxt||""),300,314,30,"#667585","600");
    }
    var xt=300;
    if(MKN[c.mercado])xt+=chipc(x,MKN[c.mercado],xt,335);
    if(c.condTxt)chipc(x,"Como "+c.condTxt,xt,335);
    rr(x,40,415,1000,80,20);
    x.fillStyle="#eef1f4";
    x.fill();
    pic(x,im[0],60,425,60,60);
    tx(x,c.local,135,466,30,"#18222d","700","left",330);
    tx(x,"vs",540,466,26,"#667585","600","center");
    tx(x,c.visitante,945,466,30,"#18222d","700","right",330);
    pic(x,im[1],960,425,60,60);
    rr(x,40,515,1000,260,24);
    x.fillStyle="#e7f6ee";
    x.fill();
    x.fillStyle="#0f9d58";
    x.fillRect(40,545,10,200);
    tx(x,d.resto,80,585,44,"#18222d","800","left",920);
    tx(x,pc(c.prob),80,695,110,"#0f9d58","800");
    tx(x,"probabilidad estimada",430,680,28,"#667585","600");
    rr(x,80,715,920,14,7);
    x.fillStyle="#cfe5d8";
    x.fill();
    rr(x,80,715,Math.max(14,920*c.prob),14,7);
    x.fillStyle="#0f9d58";
    x.fill();
    if(d.ult.length){
      tx(x,"L10: "+d.h10+"/"+d.ult.length+" aciertos",80,760,28,"#18222d","700");
    }
    tiles(c).forEach(function(p,i){
      var x0=40+i*255;
      rr(x,x0,795,235,90,16);
      x.fillStyle="#eef1f4";
      x.fill();
      tx(x,p[0],x0+18,827,20,"#667585","600","left",200);
      tx(x,p[1],x0+18,871,36,"#18222d","800","left",200);
    });
    if(d.ult.length){
      var L=limites(c,d),nn=L.u.length;
      tx(x,"Últimos "+nn+" partidos (de más antiguo a más reciente)",50,935,24,"#18222d","700","left",980);
      var yb=1105,hm=125,sl=940/nn,bw=sl*0.62;
      L.u.forEach(function(v,i){
        var bh=Math.max(4,v/L.mx*hm);
        var bx=70+i*sl+(sl-bw)/2;
        rr(x,bx,yb-bh,bw,bh,6);
        x.fillStyle=d.hit(v)?"#0f9d58":"#c9d2da";
        x.fill();
        tx(x,String(v),bx+bw/2,yb-bh-10,24,"#18222d","800","center");
      });
      x.fillStyle="#e2e7ec";
      x.fillRect(60,yb,960,2);
      var ty=yb-L.thr/L.mx*hm;
      x.save();
      x.setLineDash([12,8]);
      x.strokeStyle="#d33a2c";
      x.lineWidth=3;
      x.beginPath();
      x.moveTo(60,ty);
      x.lineTo(1020,ty);
      x.stroke();
      x.restore();
      tx(x,etq(c,d),1020,ty-8,24,"#d33a2c","800","right");
    }
    x.fillStyle="#e2e7ec";
    x.fillRect(40,1150,1000,2);
    tx(x,SITIO,60,1215,44,"#0f9d58","800","left",960);
    tx(x,"+18 · Juega con responsabilidad · Información estadística, no recomendación de apuesta.",60,1260,22,"#667585","500","left",960);
    tx(x,"Las cuotas pueden cambiar. Comprueba el valor final en la casa de apuestas.",60,1292,22,"#667585","500","left",960);
    return new Promise(function(ok){
      try{
        cv.toBlob(function(b){ok(b)},"image/png");
      }catch(e){
        ok(null);
      }
    });
  });
};
if(S.data.length&&S.data[0].k===undefined)load();
else if(S.data.length)draw();
