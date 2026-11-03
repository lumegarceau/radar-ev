var DPI=null;
(function(){
  var s=document.createElement("style");
  s.textContent="#appbtn{border:1px solid var(--ac);background:#fff;color:var(--ac);border-radius:16px;padding:5px 10px;font:700 12px system-ui,sans-serif;cursor:pointer}"+
  "#amdl{display:none;position:fixed;inset:0;background:rgba(16,22,28,.62);z-index:60;overflow-y:auto;padding:12px}"+
  "#amdl.on{display:block}"+
  ".pas{counter-reset:p;list-style:none;padding:0;margin:12px 0 0}"+
  ".pas li{counter-increment:p;display:flex;gap:10px;align-items:flex-start;padding:8px 0;border-bottom:1px solid var(--line);font-size:14px}"+
  ".pas li:before{content:counter(p);flex:none;width:24px;height:24px;border-radius:50%;background:var(--acbg);color:var(--ac);font-weight:800;display:flex;align-items:center;justify-content:center;font-size:13px}";
  document.head.appendChild(s);
})();
window.addEventListener("beforeinstallprompt",function(e){
  e.preventDefault();
  DPI=e;
});
window.addEventListener("appinstalled",function(){
  DPI=null;
  var b=document.getElementById("appbtn");
  if(b)b.style.display="none";
});
if("serviceWorker" in navigator){
  window.addEventListener("load",function(){
    navigator.serviceWorker.register("sw.js").catch(function(){});
  });
}
function esApp(){
  var m=window.matchMedia&&window.matchMedia("(display-mode: standalone)").matches;
  return m||navigator.standalone===true;
}
function plat(){
  var u=navigator.userAgent||"";
  if(/iPhone|iPad|iPod/i.test(u))return "ios";
  if(/Macintosh/.test(u)&&navigator.maxTouchPoints>1)return "ios";
  return "android";
}
function abrirApp(){
  var o=document.getElementById("amdl");
  if(!o){
    o=document.createElement("div");
    o.id="amdl";
    o.addEventListener("click",function(e){if(e.target===o)cerrarApp()});
    document.body.appendChild(o);
  }
  var h='<div class="mbox k2box"><div class="mtop2"><b>Descargar la app</b>';
  h+='<button class="mx" onclick="cerrarApp()">✕</button></div>';
  h+='<div class="upd">Elige tu móvil. Se instala en la pantalla de inicio, gratis y sin tienda.</div>';
  h+='<div class="macts"><button id="bA" onclick="selApp(\'android\')">Android</button>';
  h+='<button id="bI" onclick="selApp(\'ios\')">iPhone (iOS)</button></div>';
  h+='<div id="apc"></div></div>';
  o.innerHTML=h;
  o.className="on";
  document.body.style.overflow="hidden";
  selApp(plat());
}
function selApp(w){
  document.getElementById("bA").className=w==="android"?"pr":"";
  document.getElementById("bI").className=w==="ios"?"pr":"";
  var h="";
  if(w==="android"){
    if(DPI)h+='<button class="fbtn" style="margin-top:12px" onclick="instalar()">Instalar ahora</button>';
    h+='<ol class="pas"><li>Abre esta página en <b>Chrome</b>.</li>';
    h+='<li>Pulsa el menú <b>⋮</b> (arriba a la derecha).</li>';
    h+='<li>Elige <b>Instalar aplicación</b> o <b>Añadir a pantalla de inicio</b>.</li>';
    h+='<li>Confirma con <b>Instalar</b>.</li></ol>';
  }else{
    h+='<ol class="pas"><li>Abre esta página en <b>Safari</b>.</li>';
    h+='<li>Pulsa el botón <b>Compartir</b> (el cuadrado con una flecha hacia arriba).</li>';
    h+='<li>Desliza y elige <b>Añadir a pantalla de inicio</b>.</li>';
    h+='<li>Pulsa <b>Añadir</b>.</li></ol>';
  }
  h+='<div class="k2f">Es la web instalada como app: se actualiza sola. No pasa por Google Play ni por App Store.</div>';
  document.getElementById("apc").innerHTML=h;
}
function instalar(){
  if(!DPI)return;
  DPI.prompt();
  DPI.userChoice.then(function(){
    DPI=null;
    cerrarApp();
  }).catch(function(){});
}
function cerrarApp(){
  var o=document.getElementById("amdl");
  if(o)o.className="";
  document.body.style.overflow="";
}
(function(){
  if(esApp()){
    var b=document.getElementById("appbtn");
    if(b)b.style.display="none";
  }
})();
if(S.data.length)draw();
