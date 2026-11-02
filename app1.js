var S={tab:"radar",data:[],demo:true,minEv:"",minP:"",minC:"",ord:"prob",dia:null,open:{},keys:[]};
function esc(t){return String(t==null?"":t).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
function f2(n){return n.toLocaleString("es-ES",{minimumFractionDigits:2,maximumFractionDigits:2})}
function pc(n){return Math.round(n*100)+"%"}
function hoyS(){return new Date().toLocaleDateString("sv-SE",{timeZone:"Europe/Madrid"})}
function addd(s,n){var d=new Date(s+"T12:00:00Z");d.setUTCDate(d.getUTCDate()+n);return d.toISOString().slice(0,10)}
(function(){
  var s=document.createElement("style");
  s.textContent=".lw{display:flex;align-items:center;justify-content:center;background:#fff;border-radius:5px;padding:2px 8px;min-width:78px;height:30px;font-weight:800;font-size:13px;color:#18222d}"+
  ".lw img{max-height:22px;max-width:92px;display:block}"+
  ".lw .lt{display:none;font-size:12px}"+
  ".bkb{display:flex;justify-content:space-between;align-items:center;gap:10px;text-decoration:none;background:#fff;border:1px solid var(--line);border-radius:6px;padding:6px 10px;margin-top:6px}"+
  ".bkb .lw{padding:0;min-width:0;justify-content:flex-start}"+
  ".bkb b{color:var(--ac);font-size:15px}"+
  ".bd{display:inline-block;font-size:12px;font-weight:700;border-radius:6px;padding:2px 8px;margin-left:6px;background:var(--bg);color:var(--mu);vertical-align:middle}"+
  ".bd.g{background:var(--acbg);color:var(--ac)}.bd.p{background:var(--rdbg);color:var(--rd)}"+
  ".bs{font-size:14px;font-weight:800;margin-left:4px}.bs.g{color:var(--ac)}.bs.p{color:var(--rd)}.bs.n{color:var(--mu)}";
  document.head.appendChild(s);
})();
function lgErr(i){i.style.display="none";i.nextSibling.style.display="inline"}
function logo(n){
  var k=nk(n);
  return '<span class="lw"><img src="logos/'+k+'.png" alt="" title="'+esc(n)+'" onerror="lgErr(this)"><span class="lt">'+esc(n)+'</span></span>';
}
function deHist(r){
  var m=r.max||r.ultima||{b:"",c:0};
  var cu=(r.cuotas&&r.cuotas.length)?r.cuotas:[{b:m.b,c:m.c}];
  return{pais:r.pais,liga:r.liga,local:r.local,visitante:r.visitante,
    hm:String(r.inicio).slice(11,16),dia:r.dia||String(r.inicio).slice(0,10),
    fin:Date.parse(r.inicio),suceso:r.suceso,l20:r.l20,cond:r.cond,
    condTxt:r.condTxt,rival:r.rival,prob:r.prob,cuotas:cu,fixture:r.fixture,
    estado:r.estado,valor:r.valor,motivo:r.motivo,vigente:r.vigente!==false};
}
function prep(c){
  var q=c.cuotas.map(function(o){return{b:o.b,c:o.c,u:link(o.b)}}).sort(function(a,b){return b.c-a.c});
  c.q=q;c.best=q[0];c.fair=1/c.prob;c.ev=c.prob*q[0].c-1;
  c.gap=q.length>1?q[0].c/q[1].c-1:0;
  c.empez=!!(c.fin&&Date.now()>=c.fin);
  return c;
}
function jget(u){
  return fetch(u+"?"+Date.now()).then(function(r){return r.json()}).catch(function(){return null});
}
function load(){
  Promise.all([jget("historial.json"),jget("radar-data.json")]).then(function(v){
    var h=v[0],rd=v[1],list=[];
    if(h&&h.sel){list=Object.values(h.sel).map(deHist)}
    if(!list.length&&rd&&rd.days&&rd.days.length){
      var d=rd.days[rd.days.length-1];
      list=(d.candidatos||[]).map(function(c){
        return Object.assign({},c,{dia:hoyS(),hm:String(c.hora).slice(-5),estado:"pendiente",vigente:true});
      });
    }
    list=list.filter(function(c){return c&&c.prob&&c.cuotas&&c.cuotas.length&&c.vigente});
    if(list.length)S.demo=false;
    if(rd&&rd.updated_at)document.getElementById("upd").textContent="Act. "+rd.updated_at.slice(11,16);
    if(!list.length){
      list=DEMO.map(function(c){return Object.assign({},c,{dia:hoyS(),hm:c.hora,estado:"pendiente"})});
    }
    S.data=list.map(prep).filter(function(c){return c.best.c>=1.4});
    if(!S.dia)S.dia=hoyS();
    draw();
  });
}
function nav(){
  var n=document.getElementById("nav");
  n.innerHTML=TABS.map(function(t){return '<button role="tab" data-t="'+t[0]+'" aria-selected="'+(S.tab===t[0])+'">'+t[1]+'</button>'}).join("");
  n.onclick=function(e){var t=e.target.getAttribute("data-t");if(t){S.tab=t;draw()}};
}
function evt(c){return (c.ev>=0?"+":"")+(c.ev*100).toFixed(1).replace(".",",")+"%"}
function bd(c){
  var e=c.estado;
  if(e==="ganada")return '<span class="bd g">✓ Ganada</span>';
  if(e==="perdida")return '<span class="bd p">✗ Perdida</span>';
  if(e==="nula")return '<span class="bd">Nula'+(c.motivo?" · "+esc(c.motivo):"")+'</span>';
  if(e==="revisar")return '<span class="bd">A revisar</span>';
  if(c.empez)return '<span class="bd">En juego o sin corregir</span>';
  return "";
}
function bs(c){
  if(c.estado==="ganada")return '<span class="bs g">✓</span>';
  if(c.estado==="perdida")return '<span class="bs p">✗</span>';
  if(c.estado==="nula")return '<span class="bs n">–</span>';
  return "";
}
function cbody(c){
  var evc=c.ev>=0?"pos":"neg",h="";
  h+='<div class="st">';
  if(c.l20)h+='<span class="chip">L20 <b>'+esc(c.l20)+'</b></span>';
  if(c.cond)h+='<span class="chip">L10 '+esc(c.condTxt)+' <b>'+esc(c.cond)+'</b></span>';
  if(c.rival)h+='<span class="chip">L20 permitido por el rival <b>'+esc(c.rival)+'</b></span>';
  if(c.valor!=null&&(c.estado==="ganada"||c.estado==="perdida"))h+='<span class="chip">Dato real <b>'+esc(c.valor)+'</b></span>';
  h+='</div><div class="met"><div><span>Probabilidad</span><b>'+pc(c.prob)+'</b></div>';
  h+='<div><span>Cuota estimada</span><b>'+f2(c.fair)+'</b></div>';
  h+='<div class="ev '+evc+'"><span>EV</span><b class="'+evc+'">'+evt(c)+'</b></div></div>';
  h+='<div class="act"><a class="best" href="'+esc(c.best.u)+'" target="_blank" rel="sponsored noopener">'+logo(c.best.b)+'<span>'+f2(c.best.c)+'</span></a></div>';
  if(c.q.length>1){
    h+='<details class="mo"><summary>Más cuotas ('+(c.q.length-1)+')</summary>';
    h+=c.q.slice(1).map(function(o){return '<a class="bkb" href="'+esc(o.u)+'" target="_blank" rel="sponsored noopener">'+logo(o.b)+'<b>'+f2(o.c)+'</b></a>'}).join("");
    h+='</details>';
  }
  return h;
}
function topBox(title,arr,fn){
  var h='<div class="box"><h3>'+title+'</h3>';
  arr.forEach(function(c,i){
    h+='<details class="tr"><summary class="row"><span class="n">'+(i+1)+'</span>';
    h+='<div class="g">'+esc(c.suceso)+'<small>'+esc(c.local)+' v '+esc(c.visitante)+' · '+esc(c.hm)+' (Madrid)</small></div>';
    h+=fn(c)+bs(c)+'<span class="ar">▾</span></summary><div class="tb">'+bd(c)+cbody(c)+'</div></details>';
  });
  return h+'</div>';
}
function card(c){
  return '<article class="card"><div class="mt"><b>'+esc(c.local)+' v '+esc(c.visitante)+'</b><span>'+esc(c.hm)+' (Madrid)</span></div><div class="desc">'+esc(c.suceso)+bd(c)+'</div>'+cbody(c)+'</article>';
}
