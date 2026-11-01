var S={tab:"radar",data:[],demo:true,minEv:"",minP:"",minC:"",ord:"prob"};
function esc(t){return String(t==null?"":t).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
function f2(n){return n.toLocaleString("es-ES",{minimumFractionDigits:2,maximumFractionDigits:2})}
function pc(n){return Math.round(n*100)+"%"}
function prep(c){
  var q=c.cuotas.map(function(o){return{b:o.b,c:o.c,u:link(o.b)}}).sort(function(a,b){return b.c-a.c});
  c.q=q;c.best=q[0];c.fair=1/c.prob;c.ev=c.prob*q[0].c-1;
  c.gap=q.length>1?q[0].c/q[1].c-1:0;
  return c;
}
function load(){
  fetch("radar-data.json?"+Date.now()).then(function(r){return r.json()}).then(function(j){
    var days=(j&&j.days)||[],d=days[days.length-1],list=(d&&d.candidatos)||[];
    list=list.filter(function(c){return c&&c.prob&&c.cuotas&&c.cuotas.length});
    if(list.length){S.data=list;S.demo=false}
    if(j&&j.updated_at)document.getElementById("upd").textContent="Act. "+j.updated_at.slice(11,16);
  }).catch(function(){}).then(function(){
    if(!S.data.length)S.data=DEMO;
    S.data=S.data.map(prep).filter(function(c){return c.best.c>=1.4});
    draw();
  });
}
function nav(){
  var n=document.getElementById("nav");
  n.innerHTML=TABS.map(function(t){return '<button role="tab" data-t="'+t[0]+'" aria-selected="'+(S.tab===t[0])+'">'+t[1]+'</button>'}).join("");
  n.onclick=function(e){var t=e.target.getAttribute("data-t");if(t){S.tab=t;draw()}};
}
function evt(c){return (c.ev>=0?"+":"")+(c.ev*100).toFixed(1).replace(".",",")+"%"}
function cbody(c){
  var evc=c.ev>=0?"pos":"neg",h="";
  h+='<div class="st"><span class="chip">L20 <b>'+esc(c.l20)+'</b></span>';
  h+='<span class="chip">L10 '+esc(c.condTxt)+' <b>'+esc(c.cond)+'</b></span>';
  if(c.rival)h+='<span class="chip">L20 permitido por el rival <b>'+esc(c.rival)+'</b></span>';
  h+='</div><div class="met"><div><span>Probabilidad</span><b>'+pc(c.prob)+'</b></div>';
  h+='<div><span>Cuota estimada</span><b>'+f2(c.fair)+'</b></div>';
  h+='<div class="ev '+evc+'"><span>EV</span><b class="'+evc+'">'+evt(c)+'</b></div></div>';
  h+='<div class="act"><a class="best" href="'+esc(c.best.u)+'" target="_blank" rel="sponsored noopener"><span>'+esc(c.best.b)+'</span><span>'+f2(c.best.c)+'</span></a></div>';
  if(c.q.length>1){
    h+='<details class="mo"><summary>Más cuotas ('+(c.q.length-1)+')</summary>';
    h+=c.q.slice(1).map(function(o){return '<div class="od"><span>'+esc(o.b)+'</span><a href="'+esc(o.u)+'" target="_blank" rel="sponsored noopener">'+f2(o.c)+'</a></div>'}).join("");
    h+='</details>';
  }
  return h;
}
function topBox(title,arr,fn){
  var h='<div class="box"><h3>'+title+'</h3>';
  arr.forEach(function(c,i){
    h+='<details class="tr"><summary class="row"><span class="n">'+(i+1)+'</span>';
    h+='<div class="g">'+esc(c.suceso)+'<small>'+esc(c.local)+' v '+esc(c.visitante)+' · '+esc(c.hora)+' (Madrid)</small></div>';
    h+=fn(c)+'<span class="ar">▾</span></summary><div class="tb">'+cbody(c)+'</div></details>';
  });
  return h+'</div>';
}
function card(c){
  return '<article class="card"><div class="mt"><b>'+esc(c.local)+' v '+esc(c.visitante)+'</b><span>'+esc(c.hora)+' (Madrid)</span></div><div class="desc">'+esc(c.suceso)+'</div>'+cbody(c)+'</article>';
}
