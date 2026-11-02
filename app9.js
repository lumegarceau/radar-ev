var SHIRT="M20 8L8 16l6 12 6-3v31h24V25l6 3 6-12-12-8c-2 2-7 3-12 3s-10-1-12-3z";
var BASE_COL="rgb(51,65,85)";
var TCOL={};
var GK=["rgb(255,106,0)","rgb(255,45,149)","rgb(57,255,20)","rgb(10,92,255)"];
var WEB={"LeoVegas":"https://www.leovegas.es/","EnRacha":"https://www.enracha.es/","TonyBet":"https://tonybet.es/"};
var WEBN={};
Object.keys(WEB).forEach(function(k){WEBN[nk(k)]=WEB[k]});
link=function(b){return AFFN[nk(b)]||WEBN[nk(b)]||"#"};
(function(){
  var s=document.createElement("style");
  s.textContent=[
  ".mbox.k2box{padding:10px 10px 12px}",
  ".mtop2{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;font-size:15px}",
  ".mtop2 .mx{width:34px;height:34px}",
  ".k2{border:1px solid var(--line);border-radius:12px;padding:10px 12px;background:#fff}",
  ".k2h{display:flex;justify-content:space-between;align-items:center;font-size:12px;color:var(--mu)}",
  ".k2h span{display:flex;align-items:center;gap:6px}",
  ".k2p{position:relative;display:flex;align-items:center;gap:10px;margin:6px 0;overflow:hidden}",
  ".k2s{width:88px;height:88px;flex:none}",
  ".k2n{position:relative}",
  ".k2n h3{margin:0;font-size:19px;line-height:1.15}",
  ".k2n small{display:flex;align-items:center;flex-wrap:wrap;gap:4px;font-size:12px;color:var(--mu);margin-top:3px}",
  ".k2m{display:flex;align-items:center;justify-content:space-between;gap:6px;background:var(--bg);border-radius:8px;padding:6px 8px;font-weight:700;font-size:13px}",
  ".k2m span{display:flex;align-items:center}",
  ".k2l{border-left:4px solid var(--ac);background:var(--acbg);border-radius:8px;padding:8px 10px;margin:8px 0}",
  ".k2l b{font-size:14px}",
  ".k2pr{display:flex;align-items:baseline;gap:8px;margin-top:2px}",
  ".k2pr i{font-style:normal;font-size:30px;font-weight:800;color:var(--ac);line-height:1}",
  ".k2pr span{font-size:12px;color:var(--mu)}",
  ".k2t{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}",
  ".k2t div{background:var(--bg);border-radius:8px;padding:6px 4px;text-align:center}",
  ".k2t span{display:block;font-size:10px;color:var(--mu);line-height:1.1}",
  ".k2t b{font-size:14px}",
  ".k2b{position:relative;display:flex;align-items:flex-end;gap:4px;height:64px;margin-top:22px;border-bottom:1px solid var(--line)}",
  ".k2f{font-size:10px;color:var(--mu);margin-top:8px;line-height:1.3}",
  ".k2f strong{display:block;color:var(--ac);font-size:12px}"
  ].join("");
  document.head.appendChild(s);
})();
function rgbN(col){
  var m=String(col).match(/\d+/g)||[15,157,88];
  return [+m[0],+m[1],+m[2]];
}
function txtCol(col){
  var v=rgbN(col);
  var l=0.299*v[0]+0.587*v[1]+0.114*v[2];
  return l>165?"#18222d":"#ffffff";
}
function apellido(n){
  var t=String(n||"").trim().split(/\s+/);
  return (t[t.length-1]||"").toUpperCase();
}
function esPortero(c){
  return c.tipo==="jugador"&&(c.mercado==="saves"||c.pos==="G");
}
function tcol(id){
  if(!id)return Promise.resolve(BASE_COL);
  if(TCOL[id])return Promise.resolve(TCOL[id]);
  return cimg(IMG+"teams/"+id+".png").then(function(im){
    var col=null;
    if(im){
      try{
        var cv=document.createElement("canvas");
        cv.width=32;
        cv.height=32;
        var x=cv.getContext("2d");
        x.drawImage(im,0,0,32,32);
        var d=x.getImageData(0,0,32,32).data,b={};
        for(var i=0;i<d.length;i+=4){
          var r=d[i],g=d[i+1],bl=d[i+2];
          if(d[i+3]<200)continue;
          var mx=Math.max(r,g,bl),mn=Math.min(r,g,bl);
          if(mx-mn<35||mx<50)continue;
          var k=(r>>6)+","+(g>>6)+","+(bl>>6);
          var e=b[k]||(b[k]={n:0,r:0,g:0,b:0});
          e.n++;
          e.r+=r;
          e.g+=g;
          e.b+=bl;
        }
        var best=null;
        Object.keys(b).forEach(function(k2){
          if(!best||b[k2].n>best.n)best=b[k2];
        });
        if(best){
          col="rgb("+Math.round(best.r/best.n)+","+Math.round(best.g/best.n)+","+Math.round(best.b/best.n)+")";
        }
      }catch(err){}
    }
    TCOL[id]=col||BASE_COL;
    return TCOL[id];
  });
}
function camisaCol(c){
  if(esPortero(c))return Promise.resolve(GK[(Number(c.pid)||0)%4]);
  return tcol(c.tid);
}
function camisaSvg(c,col,nombre){
  var ap=apellido(nombre),n=c.num;
  var fs=Math.max(3.2,Math.min(5.2,22/(Math.max(ap.length,1)*0.66)));
  var h='<svg class="k2s" viewBox="0 0 64 64" aria-hidden="true">';
  h+='<path id="shp" d="'+SHIRT+'" fill="'+col+'" stroke="rgba(0,0,0,.2)" stroke-width="1"/>';
  h+='<g id="sht" fill="'+txtCol(col)+'" font-family="system-ui,Arial,sans-serif" font-weight="800" text-anchor="middle">';
  if(n){
    h+='<text x="32" y="24" font-size="'+fs+'">'+esc(ap)+'</text>';
    h+='<text x="32" y="46" font-size="'+(String(n).length>1?20:25)+'">'+esc(n)+'</text>';
  }else{
    h+='<text x="32" y="38" font-size="16">'+esc(ini(nombre))+'</text>';
  }
  return h+'</g></svg>';
}
function tiles(c){
  var t=[];
  if(c.cond)t.push(["Como "+c.condTxt+" L10",c.cond]);
  if(c.l20)t.push(["Últimos 20",c.l20]);
  if(c.rival)t.push(["Rival permite L20",c.rival]);
  if(c.media!=null)t.push(["Media",fnum(c.media,2)]);
  if(c.tit!=null)t.push(["Titular",c.tit+"%"]);
  if(c.por90!=null)t.push(["Por 90 min",fnum(c.por90,2)]);
  if(c.minmed!=null)t.push(["Minutos",String(Math.round(c.minmed))]);
  return t.slice(0,4);
}
function barras2(c,d){
  if(!d.ult.length)return "";
  var L=limites(c,d);
  var h='<div class="k2f" style="margin-top:8px"><b style="color:var(--tx)">Últimos '+L.u.length+' partidos</b> · de más antiguo a más reciente</div><div class="k2b">';
  L.u.forEach(function(v){
    var p=Math.round(v/L.mx*100);
    h+='<div class="bc"><em style="bottom:calc('+p+'% + 2px)">'+v+'</em><i class="'+(d.hit(v)?"h":"")+'" style="height:'+p+'%"></i></div>';
  });
  var t=Math.round(L.thr/L.mx*100);
  h+='<div class="thr" style="bottom:'+t+'%"><span>'+etq(c,d)+'</span></div></div>';
  return h;
}
function k2html(c){
  var d=datosFicha(c),J=d.J,av;
  if(J||!c.tid)av=camisaSvg(c,BASE_COL,d.nombre);
  else av=cr(c.tid,"g");
  var mk=MKN[c.mercado]?MKN[c.mercado]:"";
  var sub;
  if(J){
    sub=cr(c.tid)+esc(c.equipo||"")+(mk?" · "+mk:"")+" · Como "+esc(c.condTxt||"");
  }else{
    sub=(mk?mk+" · ":"")+"Juega como "+esc(c.condTxt||"");
  }
  var lg="";
  if(c.lid){
    lg='<img class="cr" src="'+IMG+'leagues/'+c.lid+'.png" alt="" onerror="this.style.visibility=\'hidden\'">';
  }
  var h='<div class="k2"><div class="k2h"><span>'+lg+esc(c.liga)+'</span><b>'+esc(c.hm)+' (Madrid)</b></div>';
  h+='<div class="k2p">'+(c.tid?cr(c.tid,"wmk"):"")+av+'<div class="k2n"><h3>'+esc(d.nombre)+'</h3><small>'+sub+'</small></div></div>';
  h+='<div class="k2m"><span>'+cr(c.hid)+esc(c.local)+'</span><span>vs</span><span>'+esc(c.visitante)+cr(c.aid)+'</span></div>';
  h+='<div class="k2l"><b>'+esc(d.resto)+'</b><div class="k2pr"><i>'+pc(c.prob)+'</i><span>probabilidad estimada';
  if(d.ult.length)h+=' · L10 '+d.h10+'/'+d.ult.length;
  h+='</span></div><div class="bar"><u style="width:'+Math.round(c.prob*100)+'%"></u></div></div>';
  var it=tiles(c);
  if(it.length){
    h+='<div class="k2t">'+it.map(function(p){return '<div><span>'+esc(p[0])+'</span><b>'+esc(p[1])+'</b></div>'}).join("")+'</div>';
  }
  h+=barras2(c,d);
  h+='<div class="k2f"><strong>'+esc(SITIO)+'</strong>+18 · Juega con responsabilidad. Información estadística, no recomendación de apuesta. Las cuotas pueden cambiar.</div></div>';
  return h;
}
fichaHtml=k2html;
function k2cuotas(c){
  var h='<a class="best" style="margin-top:10px" href="'+esc(c.best.u)+'" target="_blank" rel="sponsored noopener">'+logo(c.best.b)+'<span>'+f2(c.best.c)+'</span></a>';
  if(c.q.length>1){
    h+='<details class="mo"><summary>Más cuotas ('+(c.q.length-1)+')</summary>';
    c.q.slice(1).forEach(function(o){
      h+='<a class="bkb" href="'+esc(o.u)+'" target="_blank" rel="sponsored noopener">'+logo(o.b)+'<b>'+f2(o.c)+'</b></a>';
    });
    h+='</details>';
  }
  return h+'<div class="k2f">Las cuotas pueden cambiar. Comprueba el valor final en la casa de apuestas.</div>';
}
function fitTx(x,t,cx,y,mw,sz,col,min){
  var s=sz;
  x.font="800 "+s+"px "+FF;
  while(x.measureText(t).width>mw&&s>min){
    s-=1;
    x.font="800 "+s+"px "+FF;
  }
  x.fillStyle=col;
  x.textAlign="center";
  x.textBaseline="alphabetic";
  x.fillText(t,cx,y);
}
function shirt(x,col,c,nombre,a,b,s){
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
    fitTx(x,ini(nombre),cx,b+38*k,22*k,16*k,tc,8);
  }
}
ficha=function(k){
  var c=S.data.filter(function(x){return x.k===k})[0];
  if(!c){
    var e=document.getElementById("err");
    e.style.display="block";
    e.textContent="Ficha no encontrada. Recarga la página.";
    return;
  }
  window._fc=c;
  window._ib=undefined;
  var o=document.getElementById("mdl");
  if(!o){
    o=document.createElement("div");
    o.id="mdl";
    o.addEventListener("click",function(ev){if(ev.target===o)cerrar()});
    document.body.appendChild(o);
  }
  var m='<div class="mbox k2box"><div class="mtop2"><b>Ficha</b><button class="mx" onclick="cerrar()">✕</button></div>';
  m+=k2html(c);
  m+='<div class="macts"><button class="pr" onclick="compartir()">Compartir</button><button onclick="descargar()">Imagen</button><button onclick="copiarEnlace()">Enlace</button></div>';
  m+='<div class="mmsg" id="mmsg"></div>';
  m+=k2cuotas(c)+'</div>';
  o.innerHTML=m;
  o.className="on";
  document.body.style.overflow="hidden";
  camisaCol(c).then(function(col){
    var p=document.getElementById("shp"),t=document.getElementById("sht");
    if(p)p.setAttribute("fill",col);
    if(t)t.setAttribute("fill",txtCol(col));
  });
  dibuja(c).then(function(b){
    if(window._fc===c)window._ib=b||false;
  });
};
