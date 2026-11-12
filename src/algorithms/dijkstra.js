/** Dijkstra with a binary min heap. Nonnegative weights required.
 * Time O((V + E) log V); space O(V + E), including queued relaxations.
 * Returns null for unreachable or absent endpoints. */
export function dijkstra(graph,start,end){
 if(!graph.has(start)||!graph.has(end))return null;
 const distances=new Map([[start,0]]),previous=new Map(),heap=[];
 function push(item){heap.push(item);let i=heap.length-1;while(i>0){const p=(i-1)>>1;if(heap[p][0]<=item[0])break;heap[i]=heap[p];i=p;}heap[i]=item;}
 function pop(){const first=heap[0],last=heap.pop();if(heap.length){let i=0;while(i*2+1<heap.length){let c=i*2+1;if(c+1<heap.length&&heap[c+1][0]<heap[c][0])c++;if(heap[c][0]>=last[0])break;heap[i]=heap[c];i=c;}heap[i]=last;}return first;}
 push([0,start]);let visited=0;
 while(heap.length){const [cost,id]=pop();if(cost!==distances.get(id))continue;visited++;if(id===end){const path=[];for(let at=end;at!==undefined;at=previous.get(at))path.push(at);return {path:path.reverse(),cost,visited};}
 for(const {to,weight} of graph.get(id)){if(weight<0||!Number.isFinite(weight))throw new Error('Weights must be finite and nonnegative');const next=cost+weight;if(next<(distances.get(to)??Infinity)){distances.set(to,next);previous.set(to,id);push([next,to]);}}}
 return null;
}
