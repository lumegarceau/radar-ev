TABS[2]=["bookies","Bonos"];
(function(){
  var I={
    radar:'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4.5"/><path d="M12 12l6-6"/>',
    errores:'<path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18v.5"/>',
    bookies:'<rect x="3" y="8" width="18" height="13" rx="2"/><path d="M12 8v13M3 13h18M12 8c-2-4-6-4-6-1.5S10 8 12 8zM12 8c2-4 6-4 6-1.5S14 8 12 8z"/>',
    resultados:'<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>'
  };
  var s=document.createElement("style");
  s.textContent=[
    "nav{gap:8px;padding:10px 12px;border-bottom:1px solid var(--line)}",
    "nav button{display:flex;align-items:center;gap:7px;border:1px solid var(--line);border-radius:999px;background:#fff;color:var(--tx);padding:9px 15px;font-weight:700;white-space:nowrap;box-shadow:0 1px 2px rgba(0,0,0,.05)}",
    "nav button *{pointer-events:none}",
    "nav button svg{width:17px;height:17px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;color:var(--mu)}",
    "nav button[aria-selected=\"true\"]{background:var(--ac);border-color:var(--ac);color:#fff}",
    "nav button[aria-selected=\"true\"] svg{color:#fff}",
    ".k2b.mn{height:44px;margin-top:16px}.k2b.mn .bc em{font-size:9px}.k2b.mn .thr span{font-size:9px;top:-8px}",
    ".k2t b{font-size:15px}"
  ].join("");
  document.head.appendChild(s);
  nav=function(){
    var n=document.getElementById("nav");
    n.innerHTML=TABS.map(function(t){
      return '<button role="tab" data-t="'+t[0]+'" aria-selected="'+(S.tab===t[0])+'"><svg viewBox="0 0 24 24">'+(I[t[0]]||"")+'</svg>'+t[1]+'</button>';
    }).join("");
    n.onclick=function(e){
      var b=e.target.closest?e.target.closest("button[data-t]"):null;
      if(b){S.tab=b.getAttribute("data-t");draw()}
    };
  };
  var bk0=bookies;
  bookies=function(){return bk0().replace("Bookies y bonos de bienvenida","Bonos de bienvenida")};
  var dh0=deHist;
  deHist=function(r){
    var o=dh0(r);
    o.serieL=r.serieL;
    o.serieV=r.serieV;
    o.nota=r.nota;
    o.arb=r.arb;
    return o;
  };
  function lv(c,v){
    if(c.tipo!=="total"||typeof v!=="string")return v;
    var m=v.match(/^(\d+\/\d+) y (\d+\/\d+)$/);
    return m?"L "+m[1]+" · V "+m[2]:v;
  }
  var t0=tiles;
  tiles=function(c){
    return t0(c).map(function(p){
      if(c.tipo!=="total")return p;
      var l=/^Como /.test(p[0])?"En casa / fuera L10":p[0];
      return [l,lv(c,p[1])];
    });
  };
  var cb0=cbody;
  cbody=function(c){
    var h=cb0(c);
    if(c.tipo!=="total")return h;
    return h.replace(/L (\d+\/\d+) · V (\d+\/\d+)/g,"L $1<br>V $2");
  };
  function serieT(c,w){
    var s=(w==="L"?c.serieL:c.serieV);
    return (s||[]).slice(0,10).reverse();
  }
  function hitT(c,v){return c.sentido==="under"?v<c.linea:v>c.linea}
  function mini(c,w){
    var u=serieT(c,w);
    if(!u.length)return "";
    var mx=Math.max.apply(null,u.concat([c.linea,1]))*1.15;
    var t=Math.round(c.linea/mx*100);
    var nom=w==="L"?c.local:c.visitante;
    var h='<div class="k2f" style="margin-top:6px"><b style="color:var(--tx)">'+esc(nom)+'</b> · total de sus últimos '+u.length+' partidos</div><div class="k2b mn">';
    u.forEach(function(v){
      var p=Math.round(v/mx*100);
      h+='<div class="bc"><em style="bottom:calc('+p+'% + 2px)">'+v+'</em><i class="'+(hitT(c,v)?"h":"")+'" style="height:'+p+'%"></i></div>';
    });
    return h+'<div class="thr" style="bottom:'+t+'%"><span>'+(c.sentido==="under"?"<":"+")+String(c.linea).replace(".",",")+'</span></div></div>';
  }
  var kc0=k2cuotas;
  k2cuotas=function(c){
    var h=kc0(c);
    if(c.nota)h='<div class="upd" style="margin-top:8px">'+esc(c.nota)+'</div>'+h;
    if(c.arb&&c.arb.l&&c.arb.l.length){
      h+='<div class="k2f" style="margin-top:10px"><b style="color:var(--tx)">Árbitro: '+esc(c.arb.nom)+'</b><br>'+c.arb.l.map(esc).join('<br>')+'</div>';
    }
    return h;
  };
  var b0=barras2;
  barras2=function(c,d){
    if(c.tipo==="total"&&(c.serieL||c.serieV))return mini(c,"L")+mini(c,"V");
    return b0(c,d);
  };
  var tx0=tx;
  tx=function(x,t,a,b,sz,col,w,al,mw){
    var c=window._cur;
    if(c&&c.tipo==="total"&&t===SITIO&&(c.serieL||c.serieV)){
      [["L",60,c.local],["V",560,c.visitante]].forEach(function(q){
        var u=serieT(c,q[0]);
        if(!u.length)return;
        var mx=Math.max.apply(null,u.concat([c.linea,1]))*1.15,hm=95,yb=1105,W=460,sl=W/u.length,bw=sl*0.62;
        tx0(x,String(q[2])+" · últimos "+u.length,q[1],940,22,"#18222d","700","left",W);
        u.forEach(function(v,i){
          var bh=Math.max(4,v/mx*hm),bx=q[1]+i*sl+(sl-bw)/2;
          rr(x,bx,yb-bh,bw,bh,5);
          x.fillStyle=hitT(c,v)?"#0f9d58":"#c9d2da";
          x.fill();
          tx0(x,String(v),bx+bw/2,yb-bh-8,18,"#18222d","800","center");
        });
        x.fillStyle="#e2e7ec";
        x.fillRect(q[1],yb,W,2);
        var ty=yb-c.linea/mx*hm;
        x.save();
        x.setLineDash([10,7]);
        x.strokeStyle="#d33a2c";
        x.lineWidth=2;
        x.beginPath();
        x.moveTo(q[1],ty);
        x.lineTo(q[1]+W,ty);
        x.stroke();
        x.restore();
      });
    }
    tx0(x,t,a,b,sz,col,w,al,mw);
  };
})();
function top5(L,key){return top5g(L,key)}
// fin
