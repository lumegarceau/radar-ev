// Radar EV · diseño nuevo: barra inferior, Top 5, tarjeta, favoritos y ajustes
TABS=[["radar","Radar"],["errores","Errores de cuota"],["bookies","Bonos"]];
(function(){
  var SV={
    bars:'<svg viewBox="0 0 24 24"><path d="M5 20V10M12 20V4M19 20v-7"/></svg>',
    trend:'<svg viewBox="0 0 24 24"><path d="M3 17l6-6 4 4 8-8M15 7h6v6"/></svg>',
    target:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.4" fill="currentColor"/></svg>',
    home:'<svg viewBox="0 0 24 24"><path d="M3 11l9-8 9 8v10h-6v-6H9v6H3z"/></svg>',
    star:'<svg viewBox="0 0 24 24"><path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"/></svg>',
    gear:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/></svg>',
    chev:'<svg viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg>'
  };
  window.SV=SV;
  // ---------- favoritos ----------
  var FK="rev_fav",FAV={};
  try{FAV=JSON.parse(localStorage.getItem(FK)||"{}")||{}}catch(e){FAV={}}
  function guardaFav(sync){
    try{localStorage.setItem(FK,JSON.stringify(FAV))}catch(e){}
    if(sync!==false&&window.CUENTA&&CUENTA.user&&CUENTA.guardar)CUENTA.guardar(FAV);
  }
  window.FAVS=function(){return FAV};
  function starB(c){
    var on=!!FAV[c.k];
    return '<button type="button" class="st27'+(on?' on':'')+'" data-fk="'+esc(c.k)+'" aria-label="Favorito">'+SV.star+'</button>';
  }
  window.starB=starB;
  function pintaStars(k){
    var q=document.querySelectorAll('.st27[data-fk]');
    for(var i=0;i<q.length;i++){
      if(q[i].getAttribute('data-fk')===k)q[i].classList.toggle('on',!!FAV[k]);
    }
  }
  document.addEventListener('click',function(e){
    var b=e.target.closest&&e.target.closest('.st27[data-fk]');
    if(!b)return;
    e.preventDefault();e.stopPropagation();
    var k=b.getAttribute('data-fk'),c=S.data.filter(function(x){return x.k===k})[0];
    if(FAV[k])delete FAV[k];
    else FAV[k]={t:Date.now(),c:c?c.best.c:null,b:c?c.best.b:null,d:c?c.dia:null};
    guardaFav();pintaStars(k);
    if(S.tab==='favoritos')draw();
    else if(FAV[k])invita();
  },true);
  function invita(){
    if(!window.CUENTA||!CUENTA.ok||CUENTA.user)return;
    var v=null;try{v=localStorage.getItem('rev_inv')}catch(e){}
    if(v)return;
    try{localStorage.setItem('rev_inv','1')}catch(e){}
    modalCuenta('Guarda tus favoritos en tu cuenta para verlos en cualquier dispositivo.');
  }
  // ---------- cuenta (modal) ----------
  function modalCuenta(msg){
    var m=document.getElementById('am');
    if(!m){m=document.createElement('div');m.id='am';document.body.appendChild(m)}
    m.className='on';
    m.innerHTML='<div class="amb"><button class="amx" type="button" onclick="cierraCuenta()">✕</button><h3>Crea tu cuenta gratis</h3><p>'+esc(msg||'Entra para guardar tus favoritos y tu estadística personal.')+'</p>'+
      '<button type="button" class="amg" onclick="cuentaG()"><b>G</b> Continuar con Google</button><div class="amo">o con tu correo</div>'+
      '<input id="am_e" type="email" placeholder="Correo electrónico" autocomplete="email"><input id="am_p" type="password" placeholder="Contraseña (mín. 6)" autocomplete="current-password">'+
      '<div class="amr"><button type="button" class="amp" onclick="cuentaE(0)">Entrar</button><button type="button" class="ams" onclick="cuentaE(1)">Crear cuenta</button></div>'+
      '<button type="button" class="aml" onclick="cuentaR()">He olvidado mi contraseña</button><div class="amm" id="am_m"></div>'+
      '<div class="aml2">Solo se pide una vez: la sesión se recuerda hasta que pulses «Cerrar sesión».</div></div>';
  }
  window.modalCuenta=modalCuenta;
  window.cierraCuenta=function(){var m=document.getElementById('am');if(m)m.className=''};
  function msgE(e){
    var c=(e&&e.code)||'';
    var t={'auth/invalid-email':'El correo no es válido.','auth/wrong-password':'Contraseña incorrecta.','auth/invalid-credential':'Correo o contraseña incorrectos.','auth/user-not-found':'No hay cuenta con ese correo.','auth/email-already-in-use':'Ese correo ya tiene cuenta: pulsa Entrar.','auth/weak-password':'La contraseña es demasiado corta (mínimo 6).','auth/popup-closed-by-user':'Has cerrado la ventana de Google.','auth/network-request-failed':'Sin conexión. Inténtalo de nuevo.','auth/too-many-requests':'Demasiados intentos. Espera un poco.'};
    return t[c]||'No se ha podido completar. Inténtalo de nuevo.';
  }
  function ms(t,ok){var m=document.getElementById('am_m');if(m){m.textContent=t;m.className='amm'+(ok?' ok':'')}}
  window.cuentaG=function(){CUENTA.google().then(cierraCuenta).catch(function(e){ms(msgE(e))})};
  window.cuentaE=function(nuevo){
    var e=document.getElementById('am_e').value.trim(),p=document.getElementById('am_p').value;
    if(!e||!p){ms('Escribe tu correo y contraseña.');return}
    (nuevo?CUENTA.registro(e,p):CUENTA.entrar(e,p)).then(cierraCuenta).catch(function(x){ms(msgE(x))});
  };
  window.cuentaR=function(){
    var e=document.getElementById('am_e').value.trim();
    if(!e){ms('Escribe tu correo arriba y pulsa de nuevo.');return}
    CUENTA.reset(e).then(function(){ms('Te hemos enviado un correo para cambiarla.',1)}).catch(function(x){ms(msgE(x))});
  };
  // al iniciar sesión: mezclar con favoritos locales
  window.cuentaFavs=function(cloud,primera){
    cloud=cloud||{};
    var out={},k;
    if(primera){for(k in cloud)out[k]=cloud[k];for(k in FAV)if(!out[k])out[k]=FAV[k]}
    else out=cloud;
    FAV=out;guardaFav(false);
    if(primera&&window.CUENTA&&CUENTA.guardar)CUENTA.guardar(FAV);
    if(window.S&&S.data&&S.data.length)draw();
  };
  window.cuentaCambio=function(){if(window.S&&S.data&&S.data.length)draw()};
  // ---------- Top 5 ----------
  function nFmt(n){return n+(n===1?' selección':' selecciones')}
  topBox=function(t,a,fn){
    var ev=/EV/.test(t),n=a?a.length:0;
    var h='<section class="t5"><div class="t5h">'+(ev?SV.trend:SV.bars)+'<b>'+esc(t)+'</b><span class="t5n">'+nFmt(n)+'</span></div>';
    if(!n){
      h+='<div class="t5e">'+SV.target+'<span>'+(ev?'Sin selecciones con EV positivo: este día no hay Top 5.':'Pocos partidos o sin selecciones suficientes: este día no hay Top 5.')+'</span></div></section>';
      return h;
    }
    h+='<div class="box">';
    a.forEach(function(c,i){
      h+='<details class="tr"><summary class="row"><span class="n">'+(i+1)+'</span><div class="g">'+esc(c.suceso)+'<small>'+esc(c.local)+' v '+esc(c.visitante)+' · '+esc(c.hm)+'</small></div>'+fn(c)+bs(c)+starB(c)+'<span class="ar">▾</span></summary><div class="tb">'+bd(c)+cbody(c)+'</div></details>';
    });
    return h+'</div></section>';
  };
  // ---------- tarjeta ----------
  k2html=function(c){
    var d=datosFicha(c),J=d.J,mk=MKN[c.mercado]||"";
    var evc=c.ev>=0?"pos":"neg";
    var lg=c.lid?'<img class="cr" src="'+IMG+'leagues/'+c.lid+'.png" alt="" onerror="this.style.visibility=\'hidden\'">':'';
    var h='<div class="k2 n27"><div class="n-h"><div class="n-t">'+cr(c.hid)+'<b>'+esc(c.local)+'</b><i>v</i>'+cr(c.aid)+'<b>'+esc(c.visitante)+'</b></div><span class="n-hr">'+esc(c.hm)+'</span>'+starB(c)+'</div>';
    var cond=c.condTxt?' · Como '+esc(c.condTxt):'';
    if(J){
      h+='<div class="n-p"><span class="n-av">'+camisaSvg(c,BASE_COL,d.nombre)+'</span><div><b>'+esc(d.nombre)+'</b><small>'+lg+esc(c.liga)+' · '+esc(c.equipo||'')+(mk?' · '+mk:'')+cond+'</small></div></div>';
    }else{
      h+='<div class="n-s">'+lg+esc(c.liga)+(mk?' · '+mk:'')+cond+'</div>';
    }
    h+='<div class="n-big"><div class="n-a"><b>'+(!J&&c.tid?cr(c.tid):'')+esc(J?d.resto:c.suceso)+'</b><i>'+pc(c.prob)+'</i><span>Probabilidad estimada'+(d.ult.length?' · L10 '+d.h10+'/'+d.ult.length:'')+'</span></div>';
    h+='<div class="n-e"><u>EV</u><i class="'+evc+'">'+evt(c)+'</i><span>Cuota estimada '+f2(c.fair)+'</span></div></div>';
    h+='<div class="bar"><u style="width:'+Math.round(c.prob*100)+'%"></u></div>';
    var it=tiles(c);
    if(it.length)h+='<div class="k2t">'+it.map(function(p){return '<div><span>'+esc(p[0])+'</span><b>'+esc(p[1])+'</b></div>'}).join("")+'</div>';
    var br=barras2(c,d);
    if(br)h+='<details class="n-d"><summary><span>'+SV.bars+'Últimos 10 partidos</span><em>Ver detalle '+SV.chev+'</em></summary>'+br+'</details>';
    h+='<div class="n-f">Las cuotas pueden cambiar.</div></div>';
    return h;
  };
  fichaHtml=k2html;
  // ---------- barra inferior ----------
  var BN=[["radar","Inicio","home"],["resultados","Estadísticas","bars"],["favoritos","Favoritos","star"],["ajustes","Ajustes","gear"]];
  function grupo(t){return (t==="radar"||t==="errores"||t==="bookies")?"radar":t}
  function bnav(){
    var b=document.getElementById('bnav');
    if(!b){b=document.createElement('div');b.id='bnav';document.body.appendChild(b);
      b.onclick=function(e){
        var x=e.target.closest&&e.target.closest('button[data-b]');
        if(!x)return;
        var t=x.getAttribute('data-b');
        if(t==='radar'&&grupo(S.tab)==='radar')return;
        S.tab=t;draw();window.scrollTo(0,0);
      };
    }
    var g=grupo(S.tab);
    b.innerHTML=BN.map(function(x){
      var n=x[0]==='favoritos'?Object.keys(FAV).length:0;
      return '<button type="button" data-b="'+x[0]+'" class="'+(g===x[0]?'on':'')+'">'+SV[x[2]]+'<span>'+x[1]+'</span>'+(n?'<em>'+n+'</em>':'')+'</button>';
    }).join('');
  }
  // ---------- Favoritos ----------
  var FP="todo";
  window.favP=function(p){FP=p;draw()};
  function diaL(d){
    try{var t=new Date(d+'T12:00:00').toLocaleDateString('es-ES',{weekday:'long',day:'numeric',month:'long'});return t.charAt(0).toUpperCase()+t.slice(1)}catch(e){return d}
  }
  var FOPEN={};
  function fnum2(x){return Number(x).toFixed(2).replace('.',',')}
  function favEd(c,f){
    var cu=f.c||c.best.c,b=f.b||c.best.b;
    var o='<div class="fed"><b>Tu apuesta</b><div class="fedr"><label>Cuota<input type="text" inputmode="decimal" value="'+fnum2(cu)+'" onchange="favSet(\''+esc(c.k).replace(/'/g,"\\'")+'\',\'c\',this.value)"></label>';
    o+='<label>Casa<select onchange="favSet(\''+esc(c.k).replace(/'/g,"\\'")+'\',\'b\',this.value)">';
    var vistos={};
    c.q.forEach(function(q){vistos[q.b]=1;o+='<option value="'+esc(q.b)+'"'+(q.b===b?' selected':'')+'>'+esc(q.b)+' · '+fnum2(q.c)+'</option>'});
    if(b&&!vistos[b])o+='<option value="'+esc(b)+'" selected>'+esc(b)+'</option>';
    o+='</select></label></div>';
    if(c.best.c>cu+0.004)o+='<div class="fedh">Ahora hay <b>'+fnum2(c.best.c)+'</b> en '+esc(c.best.b)+' <button type="button" onclick="favUsa(\''+esc(c.k).replace(/'/g,"\\'")+'\')">Usar esa</button></div>';
    else if(c.best.c<cu-0.004)o+='<div class="fedh baja">La mejor cuota ahora es <b>'+fnum2(c.best.c)+'</b> ('+esc(c.best.b)+'): ha bajado desde tu cuota.</div>';
    return o+'</div>';
  }
  window.favSet=function(k,campo,v){
    var f=FAV[k];if(!f)return;
    if(campo==='c'){var n=parseFloat(String(v).replace(',','.'));if(!(n>=1.01&&n<=100))return;f.c=n}
    else{f.b=v;var c=S.data.filter(function(x){return x.k===k})[0];if(c){var q=c.q.filter(function(x){return x.b===v})[0];if(q)f.c=q.c}}
    guardaFav();draw();
  };
  window.favUsa=function(k){
    var f=FAV[k],c=S.data.filter(function(x){return x.k===k})[0];
    if(!f||!c)return;f.c=c.best.c;f.b=c.best.b;guardaFav();draw();
  };
  document.addEventListener('toggle',function(e){
    var t=e.target,k=t.getAttribute&&t.getAttribute('data-fk2');
    if(!k)return;
    if(t.open)FOPEN[k]=1;else delete FOPEN[k];
  },true);
  function favRow(c,i){
    var f=FAV[c.k]||{},cu=f.c||c.best.c,b=f.b||c.best.b;
    var p=c.estado==="ganada"?'<span class="v pos">Ganada</span>':c.estado==="perdida"?'<span class="v neg">Perdida</span>':c.estado==="nula"?'<span class="v gr">Nula</span>':'<span class="v gr">'+esc(c.hm)+'</span>';
    return '<details class="tr" data-fk2="'+esc(c.k)+'"'+(FOPEN[c.k]?' open':'')+'><summary class="row"><span class="n">'+(i+1)+'</span><div class="g">'+esc(c.suceso)+'<small>'+esc(c.local)+' v '+esc(c.visitante)+' · '+fnum2(cu)+' en '+esc(b)+'</small></div>'+p+starB(c)+'<span class="ar">▾</span></summary><div class="tb">'+favEd(c,f)+bd(c)+cbody(c)+'</div></details>';
  }
  function favoritos(){
    var ks=Object.keys(FAV),L=[];
    ks.forEach(function(k){
      var c=S.data.filter(function(x){return x.k===k})[0];
      if(c)L.push({c:c,f:FAV[k]});
    });
    var lim=0;
    if(FP==="7")lim=Date.now()-7*864e5;
    if(FP==="hoy")lim=-1;
    if(FP==="7")L=L.filter(function(x){return (x.f.t||0)>=lim});
    if(FP==="hoy")L=L.filter(function(x){return x.c.dia===hoyS()});
    var g=0,pd=0,nl=0,pe=0,pr=0;
    L.forEach(function(x){
      var c=x.c,cu=x.f.c||c.best.c;
      if(c.estado==="ganada"){g++;pr+=cu-1}
      else if(c.estado==="perdida"){pd++;pr-=1}
      else if(c.estado==="nula")nl++;
      else pe++;
    });
    var res=g+pd,ac=res?Math.round(g/res*100):null,roi=res?pr/res*100:null;
    var h='<h2 class="h2f">Favoritos</h2>';
    if(window.CUENTA&&CUENTA.ok&&!CUENTA.user)h+='<div class="fvb"><span>Inicia sesión y tus favoritos te seguirán en todos tus dispositivos.</span><button type="button" onclick="modalCuenta()">Entrar</button></div>';
    else if(window.CUENTA&&CUENTA.user)h+='<div class="fvb ok"><span>Sesión iniciada como '+esc(CUENTA.user.email||CUENTA.user.name||'')+'</span></div>';
    h+='<div class="chips">'+[["todo","Todos"],["hoy","Hoy"],["7","Últimos 7 días"]].map(function(p){return '<button class="'+(FP===p[0]?'on':'')+'" onclick="favP(\''+p[0]+'\')">'+p[1]+'</button>'}).join("")+'</div>';
    h+='<div class="fst"><div><span>Seguidas</span><b>'+L.length+'</b></div><div><span>Ganadas</span><b class="pos">'+g+'</b></div><div><span>Perdidas</span><b class="neg">'+pd+'</b></div><div><span>Pendientes</span><b>'+pe+'</b></div></div>';
    h+='<div class="fst f2"><div><span>Acierto</span><b>'+(ac==null?'–':ac+'%')+'</b></div><div><span>Balance con la cuota que marcaste</span><b class="'+(roi==null?'':roi>=0?'pos':'neg')+'">'+(roi==null?'–':(roi>=0?'+':'')+roi.toFixed(0).replace('.',',')+'%')+'</b></div></div>';
    if(!L.length){
      h+='<div class="t5e big">'+SV.star+'<span>'+(ks.length?'No hay favoritos en este periodo.':'Aún no tienes favoritos. Toca la estrella de una selección para seguirla y ver aquí tu estadística.')+'</span></div>';
      return h;
    }
    var dias={};
    L.forEach(function(x){var d=x.c.dia||'';(dias[d]=dias[d]||[]).push(x.c)});
    Object.keys(dias).sort().reverse().forEach(function(d){
      h+='<div class="fdia">'+esc(diaL(d))+'</div><div class="box">'+dias[d].map(favRow).join("")+'</div>';
    });
    return h;
  }
  // ---------- Ajustes ----------
  function ajustes(){
    var h='<h2 class="h2f">Ajustes</h2>';
    var cu=window.CUENTA;
    h+='<div class="ajb"><h3>Cuenta</h3>';
    if(cu&&cu.user)h+='<p>'+esc(cu.user.email||cu.user.name||'Sesión iniciada')+'</p><button type="button" class="ajt" onclick="CUENTA.salir()">Cerrar sesión</button>';
    else if(cu&&cu.ok)h+='<p>Entra para guardar tus favoritos en cualquier dispositivo.</p><button type="button" class="ajp" onclick="modalCuenta()">Iniciar sesión o crear cuenta</button>';
    else h+='<p>Tus favoritos se guardan en este dispositivo.</p>';
    h+='</div><div class="ajb"><h3>App</h3><button type="button" class="ajt" onclick="abrirApp()">Instalar en el móvil</button></div>';
    h+='<div class="ajb"><h3>Juego responsable</h3><p>Solo para mayores de 18 años. Apostar puede crear adicción. Si el juego te causa problemas, pide ayuda en <a href="https://www.jugarbien.es" target="_blank" rel="noopener">jugarbien.es</a>.</p></div>';
    return h;
  }
  var d0=draw;
  draw=function(){
    var n=document.getElementById('nav'),esR=grupo(S.tab)==='radar';
    if(S.tab==='favoritos'||S.tab==='ajustes'){
      nav();
      document.getElementById('app').innerHTML=(S.tab==='favoritos'?favoritos():ajustes());
    }else d0();
    if(n)n.style.display=esR?'':'none';
    document.body.classList.toggle('sinnav',!esR);
    bnav();
  };
})();
if(S.data&&S.data.length)draw();
// fin
