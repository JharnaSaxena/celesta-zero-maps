import {writeFileSync} from 'node:fs';
// Mulberry32: fixed seed makes every fixture reproducible.
let seed=20261104;
function random(){let t=seed+=0x6D2B79F5;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return ((t^t>>>14)>>>0)/4294967296;}
const bounds={south:13.30,north:13.40,west:77.62,east:77.72};
const coord=(r,c)=>[bounds.south+r/49*.1,bounds.west+c/49*.1];
const values=Array.from({length:50},(_,r)=>Array.from({length:50},(_,c)=>Math.round(780+420*Math.exp(-((r-28)**2+(c-25)**2)/170)+190*Math.exp(-((r-12)**2+(c-39)**2)/80)+35*Math.sin(c/7)+random()*12)));
const minerals=Array.from({length:10},(_,i)=>{const q=30+Math.floor(random()*25),f=20+Math.floor(random()*15),m=10+Math.floor(random()*10);return{id:i+1,name:['Granite ridge','Eastern outcrop','Quartz basin','Mica terrace','Feldspar shelf','Southern seam','Western spur','Valley deposit','Summit sample','Northern bed'][i],coordinates:coord(5+random()*39,5+random()*39),composition:{Quartz:q,Feldspar:f,Mica:m,Other:100-q-f-m}};});
const dangerZones=[[24,24,6,'High','Unstable rock face'],[36,14,4,'Medium','Loose scree'],[12,33,4,'High','Simulated landslide'],[13,12,4,'Low','Seasonal waterlogging'],[37,39,5,'Medium','Steep exposed slope']].map(([r,c,s,severity,name],i)=>({id:i+1,name,severity,polygon:[coord(r-s,c-s),coord(r-s,c+s),coord(r+s,c+s),coord(r+s,c-s)]}));
const environment=Array.from({length:25},(_,i)=>({coordinates:coord(5+Math.floor(i/5)*10,5+i%5*10),temperature:Math.round(22+random()*7),humidity:Math.round(45+random()*25),wind:Math.round(4+random()*13),aqi:Math.round(25+random()*35)}));
for(const [name,data] of Object.entries({elevation:{seed:20261104,bounds,values},minerals,dangerZones,environment}))writeFileSync(new URL(`../data/mock/${name}.json`,import.meta.url),JSON.stringify(data,null,2)+'\n');
