import {describe,it,expect} from 'vitest';
import {dijkstra} from '../src/algorithms/dijkstra.js';
import {buildGraph} from '../src/algorithms/graph.js';
describe('Dijkstra',()=>{
 it('finds a simple shortest path',()=>{const g=new Map([['A',[{to:'B',weight:2},{to:'C',weight:8}]],['B',[{to:'C',weight:3}]],['C',[]]]);expect(dijkstra(g,'A','C')).toMatchObject({path:['A','B','C'],cost:5});});
 it('avoids a high-danger cell when an alternative exists',()=>{const e={bounds:{south:0,north:.02,west:0,east:.02},values:[[0,0,0],[0,0,0],[0,0,0]]};const zones=[{severity:'High',polygon:[[.006,.006],[.006,.014],[.014,.014],[.014,.006]]}];expect(dijkstra(buildGraph(e,zones,true).graph,3,5).path).not.toContain(4);expect(dijkstra(buildGraph(e,zones,false).graph,3,5).path).toContain(4);});
 it('returns null for an unreachable target',()=>expect(dijkstra(new Map([[0,[]],[1,[]]]),0,1)).toBeNull());
 it('handles identical endpoints',()=>expect(dijkstra(new Map([[0,[]]]),0,0).path).toEqual([0]));
});
