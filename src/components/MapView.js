import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
export const elevationColor=v=>{const t=Math.max(0,Math.min(1,(v-750)/500));return `hsl(${165-t*135},${30+t*35}%,${76-t*32}%)`;};
export function MapView(elevation,minerals,zones,onClick){
 const b=elevation.bounds,bounds=[[b.south,b.west],[b.north,b.east]];
 const map=L.map('map',{zoomControl:false,minZoom:9}).fitBounds(bounds);
 L.control.zoom({position:'bottomright'}).addTo(map);L.control.scale({position:'bottomleft',imperial:false}).addTo(map);
 const street=L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap contributors',maxZoom:19});
 const satellite=L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{attribution:'Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics',maxZoom:19});
 const canvas=document.createElement('canvas');canvas.width=canvas.height=500;const ctx=canvas.getContext('2d');elevation.values.forEach((row,r)=>row.forEach((v,c)=>{ctx.fillStyle=elevationColor(v);ctx.fillRect(c*10,(49-r)*10,10,10);}));
 const terrain=L.imageOverlay(canvas.toDataURL(),bounds,{opacity:1});
 const heat=L.imageOverlay(canvas.toDataURL(),bounds,{opacity:.6});
 const mineralLayer=L.layerGroup(minerals.map(m=>L.marker(m.coordinates,{icon:L.divIcon({className:'mineral-marker',html:'◇',iconSize:[28,28]})}).bindPopup(`<span class="popup-kicker">MOCK GEOLOGY · SITE ${String(m.id).padStart(2,'0')}</span><h3>${m.name}</h3>${Object.entries(m.composition).map(([name,v])=>`<div class="composition"><span>${name}</span><b>${v}%</b></div>`).join('')}`)));
 const dangerLayer=L.layerGroup(zones.map(z=>L.polygon(z.polygon,{color:z.severity==='High'?'#bf533f':'#c98a3d',weight:1.5,dashArray:'5 4',fillOpacity:.2}).bindPopup(`<span class="popup-kicker">SIMULATED HAZARD</span><h3>${z.name}</h3><b>${z.severity} severity</b><p>Routing applies a risk penalty here. This is mock data, not a real-world warning.</p>`)));
 L.rectangle(bounds,{color:'#496b60',weight:1,dashArray:'4 6',fill:false,interactive:false}).addTo(map);
 street.addTo(map);dangerLayer.addTo(map);mineralLayer.addTo(map);
 let active=street,route=null,markers=[],timer=null;
 map.on('click',e=>onClick([e.latlng.lat,e.latlng.lng]));
 return {map,bounds,setBase(name){map.removeLayer(active);active={Street:street,Satellite:satellite,Terrain:terrain}[name];active.addTo(map);if(name==='Terrain')active.bringToBack();},toggle(name,on){const layer={elevation:heat,minerals:mineralLayer,danger:dangerLayer}[name];on?layer.addTo(map):map.removeLayer(layer);},fit(){map.fitBounds(bounds,{padding:[24,24]});},clear(){clearInterval(timer);if(route)map.removeLayer(route);markers.forEach(m=>map.removeLayer(m));markers=[];},point(p,label){markers.push(L.marker(p,{icon:L.divIcon({className:'point-marker',html:label,iconSize:[30,30],iconAnchor:[15,15]})}).addTo(map));},draw(coords,animate=false,onStep=()=>{}){clearInterval(timer);if(route)map.removeLayer(route);route=L.polyline(animate?[]:coords,{color:'#153f35',weight:5,lineCap:'round'}).addTo(map);if(coords.length>1)map.fitBounds(L.latLngBounds(coords),{padding:[65,65],maxZoom:14});let i=0;if(animate)timer=setInterval(()=>{route.addLatLng(coords[i]);onStep(++i);if(i===coords.length)clearInterval(timer);},65);else onStep(coords.length);}};
}
