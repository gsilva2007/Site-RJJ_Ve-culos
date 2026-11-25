// Interacoes da galeria e mensagem do WhatsApp.
document.addEventListener('DOMContentLoaded',()=>{
 const main=document.querySelector('#galeria-principal');
 const thumbs=[...document.querySelectorAll('.thumb')];let current=0;
 function show(i){if(!main||!thumbs.length)return;current=(i+thumbs.length)%thumbs.length;main.src=thumbs[current].dataset.image;thumbs.forEach((t,j)=>t.classList.toggle('active',j===current));}
 thumbs.forEach((t,i)=>t.addEventListener('click',()=>show(i)));
 document.querySelectorAll('[data-direction]').forEach(b=>b.addEventListener('click',()=>show(current+Number(b.dataset.direction))));
 const btn=document.querySelector('#consultar-todos');if(btn)btn.addEventListener('click',()=>{const items=document.querySelector('#interesses-texto').textContent.trim();const msg='Olá! Tenho interesse nestes veículos da RJJ:\n'+items;window.open('https://wa.me/'+btn.dataset.numero+'?text='+encodeURIComponent(msg),'_blank','noopener');});
});
