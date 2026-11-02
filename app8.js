var SIL='<svg viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="24" r="11" fill="#0f9d58"/><path d="M8 64c2-16 12-22 24-22s22 6 24 22z" fill="#0f9d58"/></svg>';
var MKN={shots:"Remates",sot:"Remates a puerta",fouls:"Faltas cometidas",drawn:"Faltas recibidas",saves:"Paradas",corners:"Córners",cards:"Tarjetas",goals:"Goles"};
(function(){
  var s=document.createElement("style");
  s.textContent=[
  ".hero{position:relative;overflow:hidden;border:1px solid var(--line);border-radius:12px;padding:10px 12px 12px;margin:10px 0;background:#fff}",
  ".hero .fs{margin:4px 0 0;position:relative}",
  ".wmk{position:absolute;right:-20px;top:-8px;width:170px;height:170px;opacity:.08;object-fit:contain;margin:0}",
  ".tg{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;position:relative}",
  ".tg span{background:var(--acbg);color:var(--ac);border-radius:12px;padding:3px 10px;font-size:12px;font-weight:700}",
  ".av{position:relative}",
  ".av svg{width:100%;height:100%;display:block}",
  ".av img{position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover}",
  ".bch{position:relative;display:flex;align-items:flex-end;gap:4px;height:150px;margin-top:24px;border-bottom:1px solid var(--line)}",
  ".bc{position:relative;flex:1;height:100%}",
  ".bc i{position:absolute;left:10%;right:10%;bottom:0;border-radius:4px 4px 0 0;background:#c9d2da}",
  ".bc i.h{background:var(--ac)}",
  ".bc em{position:absolute;left:0;right:0;text-align:center;font-style:normal;font-size:12px;font-weight:800}",
  ".thr{position:absolute;left:0;right:0;border-top:2px dashed var(--rd);pointer-events:none}",
  ".thr span{position:absolute;right:0;top:-18px;font-size:11px;font-weight:800;color:var(--rd);background:#fff;padding:0 4px}"
  ].join("");
  document.head.appendChild(s);
})();
function etq(c,d){
  if(d.J)return c.linea+"+";
  return "+"+String(c.linea).replace(".",",");
}
function limites(c,d){
  var u=d.ult.slice().reverse();
  var thr=d.J?c.linea-0.5:c.linea;
  var mx=Math.max.apply(null,u.concat([thr,1]))*1.15;
  return {u:u,thr:thr,mx:mx};
}
function barrasHtml(c,d){
  if(!d.ult.length)return "";
  var L=limites(c,d);
  var h='<div class="fh" style="margin-top:14px"><b>Últimos '+L.u.length+' partidos</b><span>De más antiguo a más reciente</span></div>';
  h+='<div class="bch">';
  L.u.forEach(function(v){
    var p=Math.round(v/L.mx*100);
    h+='<div class="bc"><em style="bottom:calc('+p+'% + 3px)">'+v+'</em>';
    h+='<i class="'+(d.hit(v)?"h":"")+'" style="height:'+p+'%"></i></div>';
  });
  var t=Math.round(L.thr/L.mx*100);
  h+='<div class="thr" style="bottom:'+t+'%"><span>'+etq(c,d)+'</span></div></div>';
  return h;
}
fichaHtml=function(c){
  var d=datosFicha(c),J=d.J,av;
  if(J){
    var foto="";
    if(typeof FOTOS!=="undefined"&&FOTOS&&c.pid){
      foto='<img src="'+IMG+'players/'+c.pid+'.png" alt="" onerror="this.style.display=\'none\'">';
    }
    av='<div class="av">'+SIL+foto+'</div>';
  }else if(c.tid){
    av=cr(c.tid,"g");
  }else{
    av='<div class="av">'+esc(ini(d.nombre))+'</div>';
  }
  var sub=J?cr(c.tid)+esc(c.equipo||""):"Juega como "+esc(c.condTxt||"");
  var lg="";
  if(c.lid){
    lg='<img class="cr" src="'+IMG+'leagues/'+c.lid+'.png" alt="" onerror="this.style.visibility=\'hidden\'">';
  }
  var h='<div class="fk"><div class="fh"><span>'+lg+esc(c.liga)+'</span><b>'+esc(c.hm)+' (Madrid)</b></div>';
  h+='<div class="hero">'+(c.tid?cr(c.tid,"wmk"):"");
  h+='<div class="fs">'+av+'<div><h3>'+esc(d.nombre)+'</h3><small>'+sub+'</small></div></div>';
  h+='<div class="tg">';
  if(MKN[c.mercado])h+='<span>'+MKN[c.mercado]+'</span>';
  if(c.condTxt)h+='<span>Como '+esc(c.condTxt)+'</span>';
  h+='</div></div>';
  h+='<div class="fm"><span>'+cr(c.hid)+esc(c.local)+'</span><span>vs</span><span>'+esc(c.visitante)+cr(c.aid)+'</span></div>';
  h+='<div class="fl"><b>'+esc(d.resto)+'</b><div class="fp"><i>'+pc(c.prob)+'</i><span>probabilidad estimada</span></div>';
  h+='<div class="bar"><u style="width:'+Math.round(c.prob*100)+'%"></u></div>';
  if(d.ult.length)h+='<div class="fp"><span><b>L10: '+d.h10+'/'+d.ult.length+' aciertos</b></span></div>';
  h+='</div>';
  var g="";
  if(c.cond)g+='<div><span>Como '+esc(c.condTxt)+' (L10)</span><b>'+esc(c.cond)+'</b></div>';
  if(c.l20)g+='<div><span>Últimos 20</span><b>'+esc(c.l20)+'</b></div>';
  if(c.rival)g+='<div><span>Permitido por el rival (L20)</span><b>'+esc(c.rival)+'</b></div>';
  if(g)h+='<div class="fg">'+g+'</div>';
  var f4="";
  if(c.media!=null)f4+='<div><span>Media</span><b>'+fnum(c.media,2)+'</b></div>';
  if(c.minmed!=null)f4+='<div><span>Minutos</span><b>'+Math.round(c.minmed)+'</b></div>';
  if(c.por90!=null)f4+='<div><span>Por 90 min</span><b>'+fnum(c.por90,2)+'</b></div>';
  if(c.tit!=null)f4+='<div><span>Titular</span><b>'+c.tit+'%</b></div>';
  if(f4)h+='<div class="f4">'+f4+'</div>';
  h+=barrasHtml(c,d);
  h+='<div class="fw"><strong>'+esc(SITIO)+'</strong>+18 · Juega con responsabilidad. Información estadística, no recomendación de apuesta. Las cuotas pueden cambiar.</div></div>';
  return h;
};
function chipc(x,t,a,b){
  x.font="700 24px "+FF;
  var w=x.measureText(t).width+32;
  rr(x,a,b,w,40,20);
  x.fillStyle="#e7f6ee";
  x.fill();
  tx(x,t,a+16,b+28,24,"#0f9d58","700");
  return w+10;
}
function silc(x,cx,cy,r){
  x.save();
  x.beginPath();
  x.arc(cx,cy,r,0,Math.PI*2);
  x.closePath();
  x.fillStyle="#e7f6ee";
  x.fill();
  x.clip();
  x.fillStyle="#0f9d58";
  x.beginPath();
  x.arc(cx,cy-r*0.25,r*0.34,0,Math.PI*2);
  x.fill();
  x.beginPath();
  x.arc(cx,cy+r,r*0.72,Math.PI,0);
  x.fill();
  x.restore();
}
dibuja=function(c){
  var d=datosFicha(c),J=d.J;
  var T=function(id){return id?IMG+"teams/"+id+".png":null};
  var lg=c.lid?IMG+"leagues/"+c.lid+".png":null;
  var fo=null;
  if(J&&typeof FOTOS!=="undefined"&&FOTOS&&c.pid)fo=IMG+"players/"+c.pid+".png";
  return Promise.all([T(c.hid),T(c.aid),T(c.tid),lg,fo].map(cimg)).then(function(im){
    var W=1080,H=1470;
    var cv=document.createElement("canvas");
    cv.width=W;
    cv.height=H;
    var x=cv.getContext("2d");
    x.fillStyle="#f4f6f8";
    x.fillRect(0,0,W,H);
    x.fillStyle="#0f9d58";
    x.fillRect(0,0,W,16);
    tx(x,"Radar EV",60,100,52,"#18222d","800");
    tx(x,c.liga+" · "+c.hm+" (Madrid)",60,150,28,"#667585","600","left",800);
    pic(x,im[3],W-140,50,80,80);
    rr(x,40,190,1000,260,24);
    x.fillStyle="#ffffff";
    x.fill();
    x.strokeStyle="#e2e7ec";
    x.lineWidth=2;
    x.stroke();
    if(im[2]){
      x.save();
      rr(x,40,190,1000,260,24);
      x.clip();
      x.globalAlpha=0.08;
      pic(x,im[2],690,170,380,380);
      x.restore();
    }
    var cx=150,cy=320;
    if(J){
      if(im[4]){
        x.save();
        x.beginPath();
        x.arc(cx,cy,70,0,Math.PI*2);
        x.closePath();
        x.clip();
        x.drawImage(im[4],cx-70,cy-70,140,140);
        x.restore();
      }else{
        silc(x,cx,cy,70);
      }
      tx(x,d.nombre,250,300,56,"#18222d","800","left",760);
      pic(x,im[2],250,322,44,44);
      tx(x,c.equipo||"",306,356,32,"#667585","600","left",660);
    }else{
      if(im[2])pic(x,im[2],cx-70,cy-70,140,140);
      else silc(x,cx,cy,70);
      tx(x,d.nombre,250,300,56,"#18222d","800","left",760);
      tx(x,"Juega como "+(c.condTxt||""),250,356,32,"#667585","600");
    }
    var xt=250;
    if(MKN[c.mercado])xt+=chipc(x,MKN[c.mercado],xt,392);
    if(c.condTxt)chipc(x,"Como "+c.condTxt,xt,392);
    rr(x,40,475,1000,90,20);
    x.fillStyle="#eef1f4";
    x.fill();
    pic(x,im[0],60,490,60,60);
    tx(x,c.local,135,540,32,"#18222d","700","left",330);
    tx(x,"vs",540,540,28,"#667585","600","center");
    tx(x,c.visitante,945,540,32,"#18222d","700","right",330);
    pic(x,im[1],960,490,60,60);
    rr(x,40,590,1000,270,24);
    x.fillStyle="#e7f6ee";
    x.fill();
    x.fillStyle="#0f9d58";
    x.fillRect(40,620,10,210);
    tx(x,d.resto,80,665,46,"#18222d","800","left",920);
    tx(x,pc(c.prob),80,775,120,"#0f9d58","800");
    tx(x,"probabilidad estimada",430,760,30,"#667585","600");
    rr(x,80,795,920,16,8);
    x.fillStyle="#cfe5d8";
    x.fill();
    rr(x,80,795,Math.max(16,920*c.prob),16,8);
    x.fillStyle="#0f9d58";
    x.fill();
    if(d.ult.length)tx(x,"L10: "+d.h10+"/"+d.ult.length+" aciertos",80,846,30,"#18222d","700");
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
      var x0=40+(i%3)*340,y0=885+Math.floor(i/3)*100;
      rr(x,x0,y0,320,88,16);
      x.fillStyle="#eef1f4";
      x.fill();
      tx(x,p[0],x0+20,y0+32,22,"#667585","600","left",280);
      tx(x,p[1],x0+20,y0+72,36,"#18222d","800","left",280);
    });
    if(d.ult.length){
      var L=limites(c,d),n=L.u.length;
      tx(x,"Últimos "+n+" partidos (de más antiguo a más reciente)",50,1112,26,"#18222d","700","left",980);
      var yb=1285,hm=150,sl=940/n,bw=sl*0.62;
      L.u.forEach(function(v,i){
        var bh=Math.max(4,v/L.mx*hm);
        var bx=70+i*sl+(sl-bw)/2;
        rr(x,bx,yb-bh,bw,bh,6);
        x.fillStyle=d.hit(v)?"#0f9d58":"#c9d2da";
        x.fill();
        tx(x,String(v),bx+bw/2,yb-bh-10,26,"#18222d","800","center");
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
    x.fillRect(40,1335,1000,2);
    tx(x,SITIO,60,1390,42,"#0f9d58","800","left",960);
    tx(x,"+18 · Juega con responsabilidad · Información estadística, no recomendación de apuesta.",60,1424,22,"#667585","500","left",960);
    tx(x,"Las cuotas pueden cambiar. Comprueba el valor final en la casa de apuestas.",60,1448,22,"#667585","500","left",960);
    return new Promise(function(ok){
      try{cv.toBlob(function(b){ok(b)},"image/png")}catch(e){ok(null)}
    });
  });
};
