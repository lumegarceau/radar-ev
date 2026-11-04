FOTOS=true;
(function(){
  var s=document.createElement("style");
  s.textContent=
  ".lw.sq{background:transparent;min-width:0;padding:0;height:auto;border-radius:8px}"+
  ".lw.sq img{width:32px;height:32px;max-width:none;max-height:none;border-radius:8px}"+
  ".k2wrap{position:relative}"+
  ".k2wrap .k2>.k2f:last-child{padding-right:86px;min-height:34px}"+
  ".k2act{position:absolute;right:10px;bottom:8px;display:flex;gap:6px}"+
  ".k2act button{width:34px;height:34px;border-radius:50%;border:1px solid var(--ac);background:#fff;color:var(--ac);display:flex;align-items:center;justify-content:center;padding:0;cursor:pointer}"+
  ".k2act svg{width:18px;height:18px}"+
  ".cs{margin-top:8px}.csb{margin-bottom:6px}"+
  ".k2cv{display:flex;justify-content:space-between;gap:8px;margin-top:6px;font-size:13px;color:var(--mu)}"+
  ".k2cv b{color:var(--tx)}.k2cv b.pos{color:var(--ac)}.k2cv b.neg{color:var(--rd)}"+
  ".k2ph{position:relative;width:88px;height:88px;flex:none}"+
  ".k2ph .k2s{position:absolute;left:0;top:0;width:100%;height:100%}"+
  ".k2ph img{position:absolute;left:0;top:0;width:100%;height:100%;border-radius:50%;object-fit:cover;background:#fff;border:2px solid var(--line);box-sizing:border-box}"+
  ".k2ph em{position:absolute;right:-2px;bottom:-2px;background:var(--ac);color:#fff;border-radius:10px;font-style:normal;font-weight:800;font-size:12px;padding:1px 7px}"+
  ".toast{position:fixed;left:50%;bottom:76px;transform:translateX(-50%);background:#18222d;color:#fff;padding:9px 14px;border-radius:8px;font-size:13px;z-index:99;max-width:86%;text-align:center}"+
  ".fres{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}.fres label{flex:1;min-width:120px;font-size:12px;color:var(--mu)}"+
  ".fres input{display:block;width:100%;box-sizing:border-box;margin-top:3px;padding:8px;border:1px solid var(--line);border-radius:6px;font:inherit;color:var(--tx);background:#fff}";
  document.head.appendChild(s);
})();
function lgOk(i){
  if(i.naturalWidth&&i.naturalWidth===i.naturalHeight)i.parentNode.className+=" sq";
}
function logo(n){
  var k=nk(n);
  return '<span class="lw"><img src="logos/'+k+'.png" data-k="'+k+'" alt="" title="'+esc(n)+'" onload="lgOk(this)" onerror="lgErr(this)"><span class="lt">'+esc(n)+'</span></span>';
}
function toast(t){
  var e=document.getElementById("toast");
  if(!e){e=document.createElement("div");e.id="toast";e.className="toast";document.body.appendChild(e)}
  e.textContent=t;
  e.style.display=t?"block":"none";
  clearTimeout(window._tt);
  window._tt=setTimeout(function(){e.style.display="none"},4000);
}
(function(){
  var m0=mmsg;
  mmsg=function(t){
    if(document.getElementById("mmsg"))return m0(t);
    if(t)toast(t);
  };
  var cs0=camisaSvg;
  camisaSvg=function(c,col,nombre){
    var sv=cs0(c,col,nombre);
    if(!FOTOS||c.tipo!=="jugador"||!c.pid)return sv;
    var h='<div class="k2ph">'+sv+'<img src="'+IMG+'players/'+c.pid+'.png" alt="" onerror="this.remove()">';
    if(c.num)h+='<em>'+esc(c.num)+'</em>';
    return h+'</div>';
  };
  var sh0=shirt;
  shirt=function(x,col,c,nombre,a,b,s){
    var im=window._ph&&c&&c.pid?window._ph[c.pid]:null;
    if(!FOTOS||!im){return sh0(x,col,c,nombre,a,b,s)}
    var r=s/2,cx=a+r,cy=b+r;
    x.save();
    x.beginPath();
    x.arc(cx,cy,r,0,Math.PI*2);
    x.clip();
    x.fillStyle="#fff";
    x.fillRect(a,b,s,s);
    var k=Math.max(s/im.width,s/im.height),w=im.width*k,h=im.height*k;
    x.drawImage(im,cx-w/2,cy-h/2,w,h);
    x.restore();
    x.beginPath();
    x.arc(cx,cy,r-1,0,Math.PI*2);
    x.lineWidth=3;
    x.strokeStyle="#e2e7ec";
    x.stroke();
    if(c.num){
      var t=String(c.num),bw=Math.max(44,t.length*26+20);
      x.fillStyle="#0f9d58";
      x.beginPath();
      if(x.roundRect)x.roundRect(a+s-bw+6,b+s-40,bw,40,20);else x.rect(a+s-bw+6,b+s-40,bw,40);
      x.fill();
      x.fillStyle="#fff";
      x.font="800 26px "+FF;
      x.textAlign="center";
      x.textBaseline="middle";
      x.fillText(t,a+s-bw/2+6,b+s-19);
      x.textBaseline="alphabetic";
      x.textAlign="left";
    }
  };
  var d0=dibuja;
  dibuja=function(c){
    if(FOTOS&&c.tipo==="jugador"&&c.pid){
      return cimg(IMG+"players/"+c.pid+".png").then(function(im){
        window._ph=window._ph||{};
        window._ph[c.pid]=im;
        return d0(c);
      });
    }
    return d0(c);
  };
})();
function tiles(c){
  var t=[];
  if(c.l10)t.push(["Últimos 10",c.l10]);
  if(c.l20)t.push(["Últimos 20",c.l20]);
  if(c.cond)t.push(["Como "+c.condTxt+" L10",c.cond]);
  if(c.rival)t.push(["Rival permite L20",c.rival]);
  if(c.media!=null)t.push(["Media",fnum(c.media,2)]);
  if(c.tit!=null)t.push(["Titular",c.tit+"%"]);
  return t.slice(0,4);
}
(function(){
  var t0=tx,d1=dibuja;
  tx=function(x,t,a,b,sz,col,w,al,mw){
    t0(x,t,a,b,sz,col,w,al,mw);
    var c=window._cur;
    if(c&&t==="probabilidad estimada"&&c.fair){
      t0(x,"Cuota estimada "+f2(c.fair),1000,632,26,"#667585","600","right");
      t0(x,"EV "+evt(c),1000,684,40,c.ev>=0?"#0f9d58":"#d33a2c","800","right");
    }
  };
  dibuja=function(c){
    window._cur=c;
    return d1(c);
  };
})();
var ICO_C='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 10.6l6.8-4M8.6 13.4l6.8 4"/></svg>';
var ICO_D='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v11M7 11l5 5 5-5M5 20h14"/></svg>';
function cardAct(k,m){
  var c=S.data.filter(function(x){return x.k===k})[0];
  if(!c)return;
  window._fc=c;
  window._ib=undefined;
  toast("Preparando la imagen…");
  dibuja(c).then(function(b){
    if(window._fc!==c)return;
    window._ib=b||false;
    toast("");
    if(m)compartir();else descargar();
  });
}
function cbody(c){
  var h="";
  if(c.empez){
    h+='<div class="upd" style="margin:2px 0 6px">Datos de la última lectura antes del inicio. En directo, las cuotas pueden ser muy distintas.</div>';
  }
  var kk=esc(c.k).replace(/'/g,"&#39;");
  var evc=c.ev>=0?"pos":"neg";
  var k=k2html(c);
  var cv='<div class="k2cv"><span>Cuota estimada <b>'+f2(c.fair)+'</b></span><span>EV <b class="'+evc+'">'+evt(c)+'</b></span></div>';
  k=k.replace("</u></div></div>","</u></div>"+cv+"</div>");
  h+='<div class="k2wrap">'+k+'<div class="k2act">';
  h+='<button type="button" aria-label="Descargar imagen" onclick="cardAct(this.getAttribute(\'data-k\'),0)" data-k="'+kk+'">'+ICO_D+'</button>';
  h+='<button type="button" aria-label="Compartir" onclick="cardAct(this.getAttribute(\'data-k\'),1)" data-k="'+kk+'">'+ICO_C+'</button></div></div>';
  return qm(h+k2cuotas(c));
}
function cardSel(c){
  var b=bd(c);
  if(c.valor!=null&&(c.estado==="ganada"||c.estado==="perdida"))b+='<span class="bd">Dato real '+esc(c.valor)+'</span>';
  return '<div class="cs">'+(b?'<div class="csb">'+b+'</div>':'')+cbody(c)+'</div>';
}
var LIN=1.83;
function kf(c){return String(c.fixture)+"|"+c.suceso}
function grp(c){
  var t=c.tipo||"equipo";
  var q=t==="jugador"?"p"+c.pid:(t==="total"?"tot":"e"+(c.tid||c.equipo));
  return [c.fixture,t,q,c.mercado,c.sentido||"over"].join("|");
}
function cuotaPub(c){
  if(c.best)return c.best.c;
  return ((c.ultima||c.max||{}).c)||0;
}
function pickRep(rows){
  var G={};
  rows.forEach(function(c){
    var k=grp(c),x=G[k];
    var d=Math.abs(cuotaPub(c)-LIN);
    if(!x||d<x.d-1e-9||(Math.abs(d-x.d)<1e-9&&c.prob>x.c.prob))G[k]={c:c,d:d};
  });
  var S2={};
  Object.keys(G).forEach(function(k){S2[kf(G[k].c)]=1});
  return S2;
}
function top5g(rows,key){
  var s=rows.slice().sort(function(a,b){return key(b)-key(a)}),seen={},out=[];
  for(var i=0;i<s.length;i++){
    var g=grp(s[i]);
    if(seen[g])continue;
    seen[g]=1;
    out.push(s[i]);
    if(out.length===5)break;
  }
  return out;
}
function pubSet(all){
  var pool=all.filter(function(r){return r.vigente!==false&&cuo(r)>0});
  var pub=pickRep(pool),D={};
  pool.forEach(function(r){(D[fmd(r)]=D[fmd(r)]||[]).push(r)});
  Object.keys(D).forEach(function(d){
    top5g(D[d],function(r){return r.prob}).forEach(function(r){pub[kf(r)]=1});
    top5g(D[d],function(r){return r.prob*cuo(r)}).forEach(function(r){pub[kf(r)]=1});
  });
  return pub;
}
function radar19(){
  var h=diasTabs();
  var all=S.data.filter(function(c){return c.dia===S.dia});
  h+="<h2>"+cap(fl(S.dia,{weekday:"long",day:"numeric",month:"long",year:"numeric"}))+"</h2>";
  if(!all.length)return h+'<div class="empty">No hay selecciones para este día.</div>';
  var rep=pickRep(all);
  var tp=top5g(all,function(c){return c.prob});
  var te=top5g(all,function(c){return c.ev});
  h+='<div class="tops">';
  h+=topBox("Top 5 probabilidad",tp,function(c){return '<span class="v">'+pc(c.prob)+'</span>'});
  h+=topBox("Top 5 EV",te,function(c){return '<span class="v '+(c.ev>=0?"pos":"neg")+'">'+evt(c)+'</span>'});
  h+='</div><div class="upd" style="margin-top:8px">En cada partido solo se muestra la línea con la cuota más cercana a 1,83. Las otras líneas pueden aparecer en los Top 5.</div><div class="filters">';
  h+='<label>EV mínimo (%)<input id="fe" type="number" inputmode="decimal" value="'+S.minEv+'"></label>';
  h+='<label>Probabilidad mínima (%)<input id="fp" type="number" inputmode="decimal" value="'+S.minP+'"></label>';
  h+='<label>Cuota mínima<input id="fc" type="number" inputmode="decimal" step="0.01" value="'+S.minC+'"></label>';
  h+='<label>Orden dentro de cada partido<select id="fo">'+sel("prob","Probabilidad (mayor)")+sel("ev","EV (mayor)")+sel("cuota","Cuota (mayor)")+sel("cuota_asc","Cuota (menor)")+'</select></label></div>';
  var l=all.filter(function(c){
    return rep[kf(c)]&&(S.minEv===""||c.ev*100>=+S.minEv)&&(S.minP===""||c.prob*100>=+S.minP)&&(S.minC===""||c.best.c>=+S.minC);
  });
  var key={prob:function(c){return -c.prob},ev:function(c){return -c.ev},cuota:function(c){return -c.best.c},cuota_asc:function(c){return c.best.c}}[S.ord];
  l.sort(function(a,b){
    var d=(a.fin||0)-(b.fin||0);
    if(d)return d;
    var fa=String(a.fixture),fb=String(b.fixture);
    if(fa!==fb)return fa<fb?-1:1;
    return key(a)-key(b);
  });
  var P={};
  l.forEach(function(c){
    var x=(P[c.pais]=P[c.pais]||{});
    var y=(x[c.liga]=x[c.liga]||{});
    (y[c.fixture]=y[c.fixture]||[]).push(c);
  });
  var ps=Object.keys(P).sort(function(a,b){var i=ORDER.indexOf(a),j=ORDER.indexOf(b);return (i<0?99:i)-(j<0?99:j)||a.localeCompare(b)});
  S.keys=[];
  if(!ps.length)return h+'<div class="empty">Ninguna selección cumple esos filtros.</div>';
  h+='<div class="chips"><button onclick="abre(1)">Abrir todo</button><button onclick="abre(0)">Cerrar todo</button></div>';
  ps.forEach(function(p){
    var ls=Object.keys(P[p]).sort(function(a,b){var i=LIGAS.indexOf(a),j=LIGAS.indexOf(b);return (i<0?99:i)-(j<0?99:j)});
    var n=0;
    ls.forEach(function(lg){Object.keys(P[p][lg]).forEach(function(f){n+=P[p][lg][f].length})});
    var kp="p|"+p;
    S.keys.push(kp);
    h+='<details class="pa" data-k="'+esc(kp)+'"'+(S.open[kp]?" open":"")+'><summary><span>'+(FLAG[p]||"🌍")+' '+esc(p)+'</span><span class="ct">'+n+'</span></summary>';
    ls.forEach(function(lg){
      var kl="l|"+p+"|"+lg;
      S.keys.push(kl);
      var fx=Object.keys(P[p][lg]).sort(function(a,b){
        return (P[p][lg][a][0].fin||0)-(P[p][lg][b][0].fin||0)||(a<b?-1:1);
      });
      var m=0;
      fx.forEach(function(f){m+=P[p][lg][f].length});
      h+='<details class="lg" data-k="'+esc(kl)+'"'+(S.open[kl]?" open":"")+'><summary><span>'+esc(lg)+'</span><span class="ct">'+m+'</span></summary><div class="lgb">'+fx.map(function(f){return partidoHtml(P[p][lg][f])}).join("")+'</div></details>';
    });
    h+='</details>';
  });
  return qm(h);
}
var RF={minP:"",minEv:""};
function rF(k,v){RF[k]=v;draw()}
function esErr(r){
  if(r.err)return true;
  var q=(r.cuotas||[]).map(function(o){return o.c}).sort(function(a,b){return b-a});
  return q.length>1&&q[0]/q[1]-1>0.25;
}
(function(){
  var r0=resultados;
  resultados=function(){
    if(R.data===null)return r0();
    var all=R.data;
    var pub=pubSet(all);
    var okF=function(r){
      var ev=(r.prob*cuo(r)-1)*100;
      return (RF.minP===""||r.prob*100>=+RF.minP)&&(RF.minEv===""||ev>=+RF.minEv);
    };
    R.data=all.filter(function(r){return pub[kf(r)]&&okF(r)});
    var h,lista;
    try{
      h=r0();
      lista=all.filter(function(r){return enPer(fmd(r))&&okF(r)});
    }finally{R.data=all}
    var f='<div class="fres"><label>Probabilidad mínima (%)<input type="number" inputmode="decimal" value="'+RF.minP+'" onchange="rF(\'minP\',this.value)"></label>';
    f+='<label>EV mínimo (%)<input type="number" inputmode="decimal" value="'+RF.minEv+'" onchange="rF(\'minEv\',this.value)"></label></div>';
    if(RF.minP!==""||RF.minEv!=="")f+='<div class="upd">Filtro activo: se cuentan solo las selecciones con esa probabilidad y ese EV (según la cuota elegida abajo).</div>';
    f+='<div class="upd">Se cuentan las líneas publicadas en los partidos (la más cercana a 1,83) y las que salieron en los Top 5 del día.</div>';
    var e=acc(),o=acc();
    lista.forEach(function(r){suma(esErr(r)?e:o,r)});
    var t='<h2>Errores de cuota</h2><div class="upd">Selecciones donde la mejor cuota superó en más de un 25 % a la segunda.</div>';
    function fila(n,a){
      var res=a.g+a.p;
      return [n,a.g,a.p,a.n,pct(a.g,res),bn(a.b),res?Math.round(a.b*100/res)+"%":"-"];
    }
    t+=tabla(["Grupo","G","P","N","Acierto","Benef.","ROI"],[fila("Con error de cuota",e),fila("Resto",o)]);
    t+='<div class="upd">'+e.pen+' pendientes con error de cuota. Con pocas resueltas, el dato aún no es fiable.</div>';
    return f+h+t;
  };
})();
if(S.data.length)draw();
