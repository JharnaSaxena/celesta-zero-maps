export function LayerSwitcher(view){
 document.querySelectorAll('[data-base]').forEach(button=>button.onclick=()=>{document.querySelectorAll('[data-base]').forEach(b=>b.classList.toggle('active',b===button));view.setBase(button.dataset.base);});
 document.querySelectorAll('[data-layer]').forEach(input=>input.onchange=()=>{view.toggle(input.dataset.layer,input.checked);if(input.dataset.layer==='elevation')document.querySelector('#legend').hidden=!input.checked;});
 document.querySelector('#fit').onclick=()=>view.fit();
}
