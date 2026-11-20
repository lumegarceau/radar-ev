// Cuenta de usuario (Firebase). Solo se activa si config.js define window.FB_CONFIG
(function(){
  var C=window.CUENTA={ok:false,user:null,admin:false,cur:{ok:{},no:{},cargado:false,fallo:false}};
  var ADM=(window.ADMIN_EMAILS||[]).map(function(x){return String(x).toLowerCase()});
  function calcAdmin(){C.admin=!!(C.user&&C.user.email&&ADM.indexOf(String(C.user.email).toLowerCase())>=0)}
  // curacion de errores de cuota (publicados / descartados): la ve todo el mundo, solo la escribe el administrador
  C.curCargar=function(){C.cur.cargado=true;return Promise.resolve()};
  C.curSet=function(){return Promise.reject()};
  C.curBorrarNo=function(){return Promise.resolve()};
  var cfg=window.FB_CONFIG;
  if(!cfg||!cfg.apiKey)return;
  C.ok=true;
  var V="10.12.2",B="https://www.gstatic.com/firebasejs/"+V+"/";
  function carga(u){return new Promise(function(ok,ko){var s=document.createElement("script");s.src=B+u;s.onload=ok;s.onerror=ko;document.head.appendChild(s)})}
  var auth=null,db=null,listo=null;
  function init(){
    if(listo)return listo;
    listo=carga("firebase-app-compat.js").then(function(){return carga("firebase-auth-compat.js")}).then(function(){return carga("firebase-firestore-compat.js")}).then(function(){
      firebase.initializeApp(cfg);
      auth=firebase.auth();db=firebase.firestore();
      auth.onAuthStateChanged(function(u){
        C.user=u?{uid:u.uid,email:u.email,name:u.displayName}:null;
        calcAdmin();
        if(window.cuentaCambio)cuentaCambio();
        if(u)bajar(u);
      });
    }).catch(function(){C.ok=false});
    return listo;
  }
  function bajar(u){
    db.collection("users").doc(u.uid).get().then(function(d){
      var k="rev_uid",prev=null;
      try{prev=localStorage.getItem(k);localStorage.setItem(k,u.uid)}catch(e){}
      var primera=prev!==u.uid;
      if(window.cuentaFavs)cuentaFavs((d.exists&&d.data().favs)||{},primera);
    }).catch(function(){});
  }
  var DOC=function(){return db.collection("config").doc("errores")};
  C.cur.cargado=false;
  var curT=0,curP=null;
  C.curCargar=function(fuerza){
    if(curP&&!fuerza&&Date.now()-curT<60000)return curP;
    curT=Date.now();
    curP=init().then(function(){
      if(!db)throw new Error("sin db");
      return DOC().get();
    }).then(function(d){
      var x=d.exists?d.data():{};
      C.cur.ok=x.ok||{};C.cur.no=x.no||{};C.cur.cargado=true;C.cur.fallo=false;
      if(window.curCambio)curCambio();
    }).catch(function(){
      C.cur.cargado=true;C.cur.fallo=true;
      if(window.curCambio)curCambio();
    });
    return curP;
  };
  // e: "ok" (publicar), "no" (descartar) o null (quitar de las dos listas)
  C.curSet=function(k,e){
    if(!C.admin||!db)return Promise.reject(new Error("no admin"));
    var F=firebase.firestore.FieldValue,o={ok:{},no:{}},ahora=Date.now();
    var pOk=C.cur.ok[k],pNo=C.cur.no[k];
    o.ok[k]=e==="ok"?ahora:F.delete();
    o.no[k]=e==="no"?ahora:F.delete();
    if(e==="ok"){C.cur.ok[k]=ahora;delete C.cur.no[k]}
    else if(e==="no"){C.cur.no[k]=ahora;delete C.cur.ok[k]}
    else{delete C.cur.ok[k];delete C.cur.no[k]}
    return DOC().set(o,{merge:true}).catch(function(err){
      if(pOk)C.cur.ok[k]=pOk;else delete C.cur.ok[k];
      if(pNo)C.cur.no[k]=pNo;else delete C.cur.no[k];
      throw err;
    });
  };
  C.curBorrarNo=function(keys){
    if(!C.admin||!db||!keys.length)return Promise.resolve();
    var F=firebase.firestore.FieldValue,o={no:{}};
    keys.forEach(function(k){o.no[k]=F.delete();delete C.cur.no[k]});
    return DOC().set(o,{merge:true}).catch(function(){});
  };
  C.guardar=function(f){
    if(!C.user||!db)return;
    db.collection("users").doc(C.user.uid).set({favs:f,upd:Date.now()}).catch(function(){});
  };
  function w(fn){return init().then(function(){if(!auth)throw {code:"auth/network-request-failed"};return fn()})}
  C.google=function(){return w(function(){return auth.signInWithPopup(new firebase.auth.GoogleAuthProvider())})};
  C.registro=function(e,p){return w(function(){return auth.createUserWithEmailAndPassword(e,p)})};
  C.entrar=function(e,p){return w(function(){return auth.signInWithEmailAndPassword(e,p)})};
  C.reset=function(e){return w(function(){return auth.sendPasswordResetEmail(e)})};
  C.salir=function(){
    return w(function(){return auth.signOut()}).then(function(){
      try{localStorage.removeItem("rev_uid");localStorage.removeItem("rev_fav")}catch(e){}
      location.reload();
    });
  };
  init();
})();
// fin
