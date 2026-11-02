var SITIO="lumegarceau.github.io/radar-ev";
var FOTOS=false;
var ESCUDOS=true;
window.addEventListener("DOMContentLoaded",function(){
  if(ESCUDOS)return;
  document.body.className+=" sinesc";
  var s=document.createElement("style");
  s.textContent=".sinesc .cr{display:none}";
  document.head.appendChild(s);
  cr=function(){return ""};
  var ci=cimg;
  cimg=function(u){
    if(u&&u.indexOf("/players/")>=0)return ci(u);
    return Promise.resolve(null);
  };
});
