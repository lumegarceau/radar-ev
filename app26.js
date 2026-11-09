// Decoración: anillo de probabilidad en los Top 5
(function(){
  function deco(){
    var l=document.querySelectorAll('.row .v:not(.rg):not(.pos):not(.neg)');
    for(var i=0;i<l.length;i++){
      var v=l[i],n=parseFloat(String(v.textContent).replace(',','.'));
      if(isNaN(n)||String(v.textContent).indexOf('%')<0)continue;
      v.className+=' rg '+(n>=88?'t1':n>=80?'t2':'t3');
      v.style.setProperty('--p',Math.max(0,Math.min(100,n)));
    }
  }
  var t=null,mo=new MutationObserver(function(){clearTimeout(t);t=setTimeout(deco,30)});
  function ini(){var m=document.querySelector('main')||document.body;mo.observe(m,{childList:true,subtree:true});deco()}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ini);else ini();
})();
// fin
