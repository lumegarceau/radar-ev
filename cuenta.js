// Cuenta de usuario (Firebase). Solo se activa si config.js define window.FB_CONFIG
(function(){
  var C=window.CUENTA={ok:false,user:null};
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
