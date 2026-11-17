// Banners de bookies bajo la cabecera: 4 a la vez, rotan solos. Las casas "prioritarias"
// salen 3 veces mas que el resto. Solo se muestran en la pantalla Radar.
(function(){
  if(typeof AFF==="undefined")return;
  var PRIO=["William Hill","Betway","Betfair","Luckia","Speedybet","Casino Marbella","Kirolbet","888 Sports"];
  var PESO=3,N=4,MS=5000;
  // colores de cada casa: fondo (de, a), boton (fondo, texto) y texto principal
  var C={
    "1XBET":["#0a2a5a","#1b6fd1","#57b9f9","#072040","#fff"],
    "888 Sports":["#ff6a00","#ff9a2e","#fff","#d65500","#fff"],
    "Bet365":["#0f6b4e","#188260","#ffdf1b","#0b3b2c","#fff"],
    "Betfair":["#ffb818","#ffd15c","#111","#ffb818","#111"],
    "Betsson":["#ff6801","#ff8f3d","#fff","#d95700","#fff"],
    "Betway":["#0b0b0b","#262626","#23c552","#06210f","#fff"],
    "Bwin":["#000","#1d1d1d","#ffd400","#000","#fff"],
    "Gran Casino Madrid":["#2b0d12","#5a1620","#fff","#5a1620","#fff"],
    "Casino Marbella":["#1a1a1a","#3a3226","#d4af6a","#1a1a1a","#fff"],
    "Casumo":["#0a3f45","#0b6b70","#0cd0ce","#043437","#fff"],
    "Codere":["#334049","#4a5a65","#75b809","#0f1a05","#fff"],
    "Daznbet":["#050505","#1f1f1f","#f3f963","#050505","#fff"],
    "Goldenbull":["#1a1710","#3b3320","#c9a24a","#1a1710","#fff"],
    "Interwetten":["#f4d33a","#ffe566","#111","#f4d33a","#111"],
    "Kirolbet":["#2e2e2e","#464646","#fe9121","#1a1008","#fff"],
    "Luckia":["#5a1a0a","#d44113","#fff","#b0340e","#fff"],
    "Marcaapuestas":["#7a0f1a","#c8102e","#fff","#7a0f1a","#fff"],
    "Paf":["#0b3a2f","#12624d","#ea5429","#fff","#fff"],
    "Retabet":["#111","#2b2b2b","#c6cc4f","#111","#fff"],
    "Speedybet":["#12384f","#1f6a8f","#7fd3ff","#08293d","#fff"],
    "Sportium":["#b82025","#e0373d","#fff","#b82025","#fff"],
    "Versus":["#000","#102a26","#53ffd8","#002b24","#fff"],
    "William Hill":["#00143c","#0a2a66","#f2c94c","#00143c","#fff"],
    "Winamax":["#b30012","#e50914","#fff","#b30012","#fff"],
    "Yosports":["#162308","#2f4a0d","#a4fb18","#162308","#fff"]
  };
  var NOMBRE={"1XBET":"1xBet","888 Sports":"888sport","Gran Casino Madrid":"Gran Casino Madrid"};
  var st=document.createElement("style");
  st.textContent=
    "#bnr{margin-top:12px}#bnr:empty{display:none}"+
    ".bn-t{font-size:11px;letter-spacing:.14em;text-transform:uppercase;font-weight:800;color:var(--mu);margin:0 0 8px 2px}"+
    ".bn-tr{display:flex;gap:10px;overflow-x:auto;scroll-snap-type:x mandatory;scrollbar-width:none;-webkit-overflow-scrolling:touch;margin:0;padding:0}"+
    ".bn-tr::-webkit-scrollbar{display:none}"+
    ".bn{position:relative;flex:0 0 90%;scroll-snap-align:start;border-radius:20px;padding:16px 14px 14px;display:flex;align-items:center;gap:12px;min-height:112px;overflow:hidden;text-decoration:none}"+
    ".bn::after{content:'';position:absolute;right:-40px;top:-40px;width:150px;height:150px;border-radius:50%;background:rgba(255,255,255,.08);pointer-events:none}"+
    ".bn-lg{flex:none;width:96px;height:48px;border-radius:12px;background:#fff;display:flex;align-items:center;justify-content:center;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.22)}"+
    ".bn-lg img{width:100%;height:100%;object-fit:contain;display:block}"+
    ".bn-x{flex:1;min-width:0;position:relative;z-index:1}"+
    ".bn-n{font-size:11px;letter-spacing:.16em;text-transform:uppercase;font-weight:800;opacity:.85}"+
    ".bn-h{font:900 22px/1.02 'Arial Narrow','Roboto Condensed','Helvetica Neue',Arial,sans-serif;text-transform:uppercase;margin:4px 0 9px;letter-spacing:.01em}"+
    ".bn-b{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:8px 14px;font-weight:800;font-size:13px}"+
    ".bn-p{position:absolute;right:10px;top:8px;font-size:9px;letter-spacing:.08em;text-transform:uppercase;font-weight:800;opacity:.6;z-index:1}"+
    ".bn-d{display:flex;justify-content:center;gap:6px;margin:9px 0 4px}"+
    ".bn-d i{width:7px;height:7px;border-radius:50%;background:var(--line,#cbd5e1);transition:width .25s,background .25s}"+
    ".bn-d i.on{width:22px;border-radius:4px;background:var(--ac,#0e9f4f)}"+
    ".bn-f{font-size:11px;color:var(--mu);text-align:center;margin:2px 0 0}";
  document.head.appendChild(st);

  function pesada(sin){
    var ks=Object.keys(AFF).filter(function(k){return sin.indexOf(k)<0&&C[k]});
    var out=[];
    while(out.length<N&&ks.length){
      var tot=0,w=ks.map(function(k){var p=PRIO.indexOf(k)>=0?PESO:1;tot+=p;return p});
      var r=Math.random()*tot,i=0;
      while(i<ks.length-1&&r>=w[i]){r-=w[i];i++}
      out.push(ks.splice(i,1)[0]);
    }
    return out;
  }
  var prev=[],cur=[],idx=0,timer=null,pausa=0;
  function slide(k){
    var c=C[k],u=link(k);
    return '<a class="bn" href="'+esc(u)+'" target="_blank" rel="sponsored noopener" style="background:linear-gradient(135deg,'+c[0]+','+c[1]+');color:'+c[4]+'">'+
      '<span class="bn-p">Publicidad</span>'+
      '<span class="bn-lg"><img src="logos/'+nk(k)+'.png" alt="" onerror="this.style.display=\'none\'"></span>'+
      '<span class="bn-x"><span class="bn-n">'+esc(NOMBRE[k]||k)+'</span><span class="bn-h" style="display:block">Oferta de bienvenida</span>'+
      '<span class="bn-b" style="background:'+c[2]+';color:'+c[3]+'">Ver bono <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg></span></span></a>';
  }
  function pinta(){
    var el=document.getElementById("bnr");if(!el)return;
    cur=pesada(prev);if(cur.length<N)cur=pesada([]);
    el.innerHTML='<div class="bn-t">Ofertas destacadas</div><div class="bn-tr" id="bntr">'+cur.map(slide).join("")+'</div>'+
      '<div class="bn-d" id="bnd">'+cur.map(function(_,i){return '<i'+(i===0?' class="on"':'')+'></i>'}).join("")+'</div>'+
      '<div class="bn-f">+18 · Publicidad. Condiciones en la web de cada casa. Juega con responsabilidad.</div>';
    idx=0;
    var tr=document.getElementById("bntr");
    tr.addEventListener("scroll",function(){
      var s=tr.children[0];if(!s)return;
      var w=s.offsetWidth+10,i=Math.max(0,Math.min(cur.length-1,Math.round(tr.scrollLeft/w)));
      if(i!==idx){idx=i;marca()}
    },{passive:true});
    ["touchstart","mousedown","wheel"].forEach(function(e){tr.addEventListener(e,function(){pausa=Date.now()+12000},{passive:true})});
  }
  function marca(){
    var d=document.getElementById("bnd");if(!d)return;
    [].forEach.call(d.children,function(x,i){x.className=i===idx?"on":""});
  }
  function paso(){
    var el=document.getElementById("bnr");
    if(!el||el.style.display==="none"||document.hidden||Date.now()<pausa)return;
    var tr=document.getElementById("bntr");if(!tr)return;
    if(idx>=cur.length-1){prev=cur.slice();pinta();return}
    idx++;marca();
    var s=tr.children[idx];
    tr.scrollTo({left:s.offsetLeft-tr.offsetLeft,behavior:"smooth"});
  }
  function visible(){
    var el=document.getElementById("bnr");if(!el)return;
    el.style.display=(typeof S!=="undefined"&&S.tab==="radar")?"":"none";
  }
  function init(){
    if(!document.getElementById("bnr"))return;
    pinta();visible();
    if(!(window.matchMedia&&matchMedia("(prefers-reduced-motion: reduce)").matches))timer=setInterval(paso,MS);
    if(typeof draw==="function"){
      var d0=draw;
      draw=function(){var r=d0.apply(this,arguments);visible();return r};
    }
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init();
})();
// fin
