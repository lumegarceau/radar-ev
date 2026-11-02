var R={per:"hoy",base:"max",data:null,cargando:false};
var PERS=[["hoy","Hoy"],["ayer","Ayer"],["semana","Semana"],["mes","Mes"],["anio","Año"],["todo","Todo"]];
var BASES=[["max","Máxima"],["primera","Primera"],["ultima","Última"]];
(function(){
  var s=document.createElement("style");
  s.textContent=".tbl{width:100%;border-collapse:collapse;font-size:13px;background:var(--card)}"+
  ".tbl th,.tbl td{padding:7px 6px;border-bottom:1px solid var(--line);text-align:right}"+
  ".tbl th:first-child,.tbl td:first-child{text-align:left}"+
  ".tbl th{color:var(--mu);font-weight:600;font-size:12px}"+
  ".chips{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0}"+
  ".chips button{border:1px solid var(--line);background:#fff;border-radius:16px;padding:6px 12px;font:inherit;font-size:13px;color:var(--mu);cursor:pointer}"+
  ".chips button.on{background:var(--ac);color:#fff;border-color:var(--ac)}"+
  ".sum{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin:8px 0}"+
  ".sum div{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px;text-align:center}"+
  ".sum span{display:block;font-size:11px;color:var(--mu)}"+
  ".sum b{font-size:17px}"+
  ".scr{overflow-x:auto}.gr{color:var(--mu)}";
  document.head.appendChild(s);
})();
function rP(x){R.per=x;draw()}
function rB(x){R.base=x;draw()}
function hoyS(){
  return new Date().toLocaleDateString("sv-SE",{timeZone:"Europe/Madrid"});
}
function fmd(r){
  return new Date(r.inicio).toLocaleDateString("sv-SE",{timeZone:"Europe/Madrid"});
}
function addd(s,n){
  var d=new Date(s+"T12:00:00Z");
  d.setUTCDate(d.getUTCDate()+n);
  return d.toISOString().slice(0,10);
}
function enPer(f){
  var t=hoyS();
  if(R.per==="hoy")return f===t;
  if(R.per==="ayer")return f===addd(t,-1);
  if(R.per==="semana"){
    var dw=(new Date(t+"T12:00:00Z").getUTCDay()+6)%7;
    var l=addd(t,-dw);
    return f>=l&&f<=addd(l,6);
  }
  if(R.per==="mes")return f.slice(0,7)===t.slice(0,7);
  if(R.per==="anio")return f.slice(0,4)===t.slice(0,4);
  return true;
}
function cuo(r){return (r[R.base]||r.max||{}).c||0}
function acc(){return{g:0,p:0,n:0,pen:0,rev:0,b:0}}
function suma(a,r){
  if(r.estado==="ganada"){a.g++;a.b+=cuo(r)-1}
  else if(r.estado==="perdida"){a.p++;a.b-=1}
  else if(r.estado==="nula")a.n++;
  else if(r.estado==="pendiente")a.pen++;
  else a.rev++;
}
function pct(a,b){return b>0?Math.round(a*100/b)+"%":"-"}
function ben(x){
  return (x>=0?"+":"")+x.toFixed(2).replace(".",",")+" u";
}
function bn(x){
  var c=x>=0?"pos":"neg";
  return '<b class="'+c+'">'+ben(x)+"</b>";
}
function chips(lista,cur,fn){
  return '<div class="chips">'+lista.map(function(x){
    var on=cur===x[0]?"on":"";
    return '<button class="'+on+'" onclick="'+fn+"('"+x[0]+"')"+'">'+x[1]+"</button>";
  }).join("")+"</div>";
}
function tabla(cab,filas){
  var h='<div class="scr"><table class="tbl"><tr>';
  h+=cab.map(function(c){return "<th>"+c+"</th>"}).join("")+"</tr>";
  filas.forEach(function(f){
    h+="<tr>"+f.map(function(c){return "<td>"+c+"</td>"}).join("")+"</tr>";
  });
  return h+"</table></div>";
}
function calib(){
  var B={};
  R.data.forEach(function(r){
    if(["ganada","perdida","nula"].indexOf(r.estado)<0)return;
    var b=Math.floor(r.prob*20)*5;
    if(b<50)b=45;
    if(b>95)b=95;
    var x=B[b]=B[b]||{a:acc(),s:0,n:0};
    suma(x.a,r);
    x.s+=r.prob;
    x.n++;
  });
  var ks=Object.keys(B).map(Number).sort(function(a,b){return a-b});
  if(!ks.length){
    return '<div class="empty">Todavía no hay selecciones resueltas.</div>';
  }
  var filas=ks.map(function(b){
    var x=B[b],a=x.a,res=a.g+a.p;
    var et=b===45?"&lt;50%":b+"-"+(b+5)+"%";
    var est=Math.round(x.s*100/x.n);
    var real="-";
    if(res){
      var rv=Math.round(a.g*100/res);
      var c=res<10?"gr":(rv>=est?"pos":"neg");
      real='<b class="'+c+'">'+rv+"%</b>";
    }
    return [et,x.n,est+"%",real,a.g,a.p,a.n];
  });
  var h=tabla(["Tramo","Sel.","Estimado","Real","Ganadas","Perdidas","Nulas"],filas);
  h+='<p class="upd">Real = ganadas / (ganadas + perdidas). Con menos de 10 resueltas en un tramo el dato aún no es fiable (sale en gris).</p>';
  return h;
}
function resultados(){
  if(R.data===null){
    if(!R.cargando){
      R.cargando=true;
      fetch("historial.json?"+Date.now())
        .then(function(r){return r.json()})
        .then(function(j){R.data=Object.values((j&&j.sel)||{})})
        .catch(function(){R.data=[]})
        .then(function(){if(S.tab==="resultados")draw()});
    }
    return '<h2>Resultados</h2><div class="empty">Cargando…</div>';
  }
  var lista=R.data.filter(function(r){return enPer(fmd(r))});
  var A=acc();
  lista.forEach(function(r){suma(A,r)});
  var res=A.g+A.p;
  var h="<h2>Resultados</h2>"+chips(PERS,R.per,"rP");
  h+='<div class="upd">Cuota usada en el balance</div>'+chips(BASES,R.base,"rB");
  h+='<div class="sum">';
  h+="<div><span>Acierto</span><b>"+pct(A.g,res)+"</b></div>";
  h+="<div><span>Beneficio</span>"+bn(A.b)+"</div>";
  var roi=res?Math.round(A.b*100/res)+"%":"-";
  h+="<div><span>ROI</span><b>"+roi+"</b></div></div>";
  var rv=A.rev?" · "+A.rev+" a revisar":"";
  h+='<div class="upd">'+A.g+" ganadas · "+A.p+" perdidas · "+A.n+" nulas · "+A.pen+" pendientes"+rv+"</div>";
  h+="<h2>Calibración (todas las resueltas)</h2>"+calib();
  var L={};
  lista.forEach(function(r){
    var x=L[r.liga]=L[r.liga]||acc();
    suma(x,r);
  });
  var kl=Object.keys(L).sort(function(a,b){return L[b].b-L[a].b});
  if(kl.length){
    h+="<h2>Por liga</h2>"+tabla(["Liga","G","P","N","Acierto","Benef."],
      kl.map(function(k){
        var a=L[k];
        return [esc(k),a.g,a.p,a.n,pct(a.g,a.g+a.p),bn(a.b)];
      }));
  }
  if(R.per!=="hoy"&&R.per!=="ayer"){
    var D={};
    lista.forEach(function(r){
      var f=fmd(r);
      var x=D[f]=D[f]||acc();
      suma(x,r);
    });
    var kd=Object.keys(D).sort().reverse().slice(0,31);
    if(kd.length){
      h+="<h2>Por día</h2>"+tabla(["Día","G","P","N","Benef."],
        kd.map(function(k){
          var a=D[k];
          return [k.slice(8)+"/"+k.slice(5,7),a.g,a.p,a.n,bn(a.b)];
        }));
    }
  }
  return h;
                                        }
