(function(){
  var base=cbody;
  cbody=function(c){
    var h=base(c);
    if(c.empez){
      h='<div class="upd" style="margin:6px 0">Datos de la última lectura antes del inicio. En directo, las cuotas pueden ser muy distintas.</div>'+h;
    }
    return h;
  };
})();
