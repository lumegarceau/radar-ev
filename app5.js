var IMG="https://media.api-sports.io/football/";
function cr(id,cl){
  if(!id)return "";
  return '<img class="cr '+(cl||"")+'" src="'+IMG+'teams/'+id+'.png" alt="" loading="lazy" onerror="this.style.visibility=\'hidden\'">';
}
(function(){
  var dh=deHist,pp=prep,cb=cbody;
  var KS=["tid","hid","aid","lid","pid","serie","media","minmed","por90","tit","linea","mercado","tipo","equipo"];
  deHist=function(r){
    var o=dh(r);
    KS.forEach(function(k){o[k]=r[k]});
    return o;
  };
  prep=function(c){
    c=pp(c);
    c.k=String(c.fixture)+"|"+c.suceso;
    return c;
  };
  cbody=function(c){
    return cb(c)+'<button class="fbtn" data-ficha="'+esc(c.k)+'">Ver ficha y compartir</button>';
  };
  var d0=draw;
  draw=function(){
    d0();
    if(!window._ab&&S.data.length){
      window._ab=1;
      var p=new URLSearchParams(location.search).get("s");
      if(p)ficha(p);
    }
  };
})();
card=function(c){
  return '<article class="card"><div class="mt"><b>'+cr(c.hid)+esc(c.local)+' v '+cr(c.aid)+esc(c.visitante)+'</b><span>'+esc(c.hm)+' (Madrid)</span></div><div class="desc">'+esc(c.suceso)+bd(c)+'</div>'+cbody(c)+'</article>';
};
document.addEventListener("click",function(e){
  var b=e.target.closest&&e.target.closest("[data-ficha]");
  if(b){
    e.preventDefault();
    ficha(b.getAttribute("data-ficha"));
  }
});
function ini(n){
  var t=String(n||"").trim().split(/\s+/);
  if(!t[0])return "?";
  var a=t[0].charAt(0);
  var b=t.length>1?t[t.length-1].charAt(0):"";
  return (a+b).toUpperCase();
}
function fnum(x,d){
  if(x==null)return "-";
  return Number(x).toLocaleString("es-ES",{minimumFractionDigits:d,maximumFractionDigits:d});
}
function datosFicha(c){
  var J=c.tipo==="jugador";
  var nombre=J?String(c.suceso).split(" "+c.linea+"+ ")[0]:(c.equipo||c.local);
  var resto=String(c.suceso).slice(nombre.length).trim();
  var ult=(c.serie||[]).slice(0,10);
  var hit=function(v){return J?v>=c.linea:v>c.linea};
  return {J:J,nombre:nombre,resto:resto,ult:ult,hit:hit,h10:ult.filter(hit).length};
}
function fichaHtml(c){
  var d=datosFicha(c),J=d.J,av,cl;
  if(J){
    var foto=(typeof FOTOS!=="undefined"&&FOTOS&&c.pid)?'<img src="'+IMG+'players/'+c.pid+'.png" alt="" onerror="this.remove()">':"";
    av='<div class="av">'+foto+esc(ini(d.nombre))+'</div>';
    cl='<small>'+cr(c.tid)+esc(c.equipo||"")+'</small>';
  }else{
    av=c.tid?cr(c.tid,"g"):'<div class="av">'+esc(ini(d.nombre))+'</div>';
    cl='<small>Juega como '+esc(c.condTxt||"")+'</small>';
  }
  var lg=c.lid?'<img class="cr" src="'+IMG+'leagues/'+c.lid+'.png" alt="" onerror="this.style.visibility=\'hidden\'">':"";
  var h='<div class="fk"><div class="fh"><span>'+lg+esc(c.liga)+'</span><b>'+esc(c.hm)+' (Madrid)</b></div>';
  h+='<div class="fs">'+av+'<div><h3>'+esc(d.nombre)+'</h3>'+cl+'</div></div>';
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
  if(d.ult.length){
    h+='<div class="fh" style="margin-top:12px"><b>Últimos resultados</b><span>El más reciente, primero</span></div><div class="ur">';
    h+=d.ult.map(function(v){return '<b class="'+(d.hit(v)?"h":"")+'">'+v+'</b>'}).join("");
    h+='</div>';
  }
  h+='<div class="fw"><strong>'+esc(SITIO)+'</strong>+18 · Juega con responsabilidad. Información estadística, no recomendación de apuesta. Las cuotas pueden cambiar.</div></div>';
  return h;
}
function cuotasFicha(c){
  var h='<h2 style="margin-top:14px">Cuotas</h2>';
  h+='<a class="best" href="'+esc(c.best.u)+'" target="_blank" rel="sponsored noopener">'+logo(c.best.b)+'<span>'+f2(c.best.c)+'</span></a>';
  c.q.slice(1).forEach(function(o){
    h+='<a class="bkb" href="'+esc(o.u)+'" target="_blank" rel="sponsored noopener">'+logo(o.b)+'<b>'+f2(o.c)+'</b></a>';
  });
  return h+'<div class="fw">Las cuotas pueden cambiar. Comprueba el valor final en la casa de apuestas.</div>';
}
function ficha(k){
  var c=S.data.filter(function(x){return x.k===k})[0];
  if(!c)return;
  window._fc=c;
  window._ib=undefined;
  var o=document.getElementById("mdl");
  if(!o){
    o=document.createElement("div");
    o.id="mdl";
    o.addEventListener("click",function(e){if(e.target===o)cerrar()});
    document.body.appendChild(o);
  }
  var m='<div class="mbox"><div class="mtop"><button class="mx" onclick="cerrar()">✕</button></div>';
  m+=fichaHtml(c);
  m+='<div class="macts"><button class="pr" onclick="compartir()">Compartir</button><button onclick="descargar()">Descargar imagen</button></div>';
  m+='<div class="mmsg" id="mmsg"></div>';
  m+='<button class="fbtn" onclick="copiarEnlace()">Copiar enlace</button>';
  m+=cuotasFicha(c)+'</div>';
  o.innerHTML=m;
  o.className="on";
  document.body.style.overflow="hidden";
  dibuja(c).then(function(b){if(window._fc===c)window._ib=b||false});
}
function cerrar(){
  var o=document.getElementById("mdl");
  if(o)o.className="";
  document.body.style.overflow="";
}
