import {dijkstra} from '../algorithms/dijkstra.js';
export const SIZE=65,SPAN=50,SEED=20261110;
export const sites=[
{id:'H01',name:'Aurora base',type:'habitat',x:-5,z:5,note:'Flat crater-floor candidate near the simulated landing corridor. Assumes a sealed, shielded habitat.'},
{id:'H02',name:'Haven terrace',type:'habitat',x:9,z:7,note:'Secondary habitat candidate on a sheltered terrace. Engineering suitability is unverified.'},
{id:'R01',name:'Hydrated mineral hub',type:'resource',x:-11,z:-4,note:'Synthetic hydrated-mineral prospect. Resource concentration and extractability are invented.'},
{id:'R02',name:'Regolith works',type:'resource',x:8,z:12,note:'Mock feedstock staging site for construction research; no measured deposit data.'},
{id:'R03',name:'Ice prospect',type:'resource',x:15,z:-6,note:'Fictional subsurface ice prospect, not evidence of accessible ice in Jezero.'},
{id:'S01',name:'Delta archive',type:'science',x:-12,z:-8,note:'Synthetic delta-inspired outcrop for sediment sampling and ancient-environment research.'},
{id:'S02',name:'Crater rim station',type:'science',x:16,z:10,note:'Elevated mock geological survey target on the crater rim.'},
{id:'S03',name:'Basin core',type:'science',x:2,z:-5,note:'Simulated basin-floor core-sampling target; no claim of biological evidence.'}
];
export function generateTerrain(seed=SEED){let state=seed;const rand=()=>{let t=state+=0x6D2B79F5;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return ((t^t>>>14)>>>0)/4294967296;};const nodes=[];
 for(let r=0;r<SIZE;r++)for(let c=0;c<SIZE;c++){const x=c/(SIZE-1)*SPAN-SPAN/2,z=r/(SIZE-1)*SPAN-SPAN/2,d=Math.hypot(x,z),a=Math.atan2(z,x);const rim=2.05*Math.exp(-(((d-19.5)/2.2)**2))*(1+.18*Math.sin(a*9)+.09*Math.cos(a*17));const floor=.27*Math.sin(x*.31)*Math.cos(z*.27);const delta=1.25*Math.exp(-((x+12)**2/29+(z+7)**2/50))*(.65+.35*Math.sin(z*1.1+x*.6));const small=.4*Math.exp(-(((Math.hypot(x-9,z+11)-3)/.8)**2));const height=.25+rim+floor+delta+small+(rand()-.5)*.1;nodes.push({id:r*SIZE+c,r,c,x,z,height,dust:Math.round(15+45*rand()),slope:0});}
 for(const n of nodes){const right=nodes[n.r*SIZE+Math.min(SIZE-1,n.c+1)],left=nodes[n.r*SIZE+Math.max(0,n.c-1)],up=nodes[Math.max(0,n.r-1)*SIZE+n.c],down=nodes[Math.min(SIZE-1,n.r+1)*SIZE+n.c];n.slope=Math.atan(Math.hypot((right.height-left.height)/((right.c-left.c)*SPAN/(SIZE-1)),(down.height-up.height)/((down.r-up.r)*SPAN/(SIZE-1))))*180/Math.PI;n.baseDistance=Math.hypot(n.x+5,n.z-5);n.margin=Math.round(Math.max(0,Math.min(100,100-n.slope*2-n.dust*.32-n.baseDistance*1.1)));}return nodes;}
export const tier=m=>m>=65?'Favorable':m>=40?'Caution':'Critical';
export function nearest(nodes,x,z){return nodes.reduce((a,b)=>Math.hypot(a.x-x,a.z-z)<Math.hypot(b.x-x,b.z-z)?a:b);}
/** Grid graph O(V) construction. Dijkstra O((V+E) log V), O(V+E) space.
 * Undirected 4-neighbor routing trades distance for mock safety and slope. */
export function routeTo(nodes,from,to){const graph=new Map();for(const n of nodes){const edges=[];for(const [dr,dc] of [[1,0],[-1,0],[0,1],[0,-1]]){const r=n.r+dr,c=n.c+dc;if(r<0||c<0||r>=SIZE||c>=SIZE)continue;const b=nodes[r*SIZE+c],length=Math.hypot(n.x-b.x,n.z-b.z,n.height-b.height);edges.push({to:b.id,weight:length*(1+(100-Math.min(n.margin,b.margin))/22)+Math.abs(n.height-b.height)*6});}graph.set(n.id,edges);}const result=dijkstra(graph,from.id,to.id);return result?result.path.map(i=>nodes[i]):[];}
