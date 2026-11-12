import {it,expect} from 'vitest';
import {generateTerrain,nearest,routeTo,sites,SIZE,tier} from '../src/mars/model.js';
it('generates reproducible 65-square Mars data and bounded margins',()=>{const a=generateTerrain(),b=generateTerrain();expect(a).toEqual(b);expect(a).toHaveLength(SIZE*SIZE);expect(a.every(n=>Number.isFinite(n.slope)&&n.margin>=0&&n.margin<=100)).toBe(true);expect(generateTerrain(7)).not.toEqual(a);});
it('finds contiguous base-to-target paths on the real mock graph',()=>{const n=generateTerrain(),a=nearest(n,sites[0].x,sites[0].z),b=nearest(n,sites[5].x,sites[5].z),p=routeTo(n,a,b);expect(p[0]).toEqual(a);expect(p.at(-1)).toEqual(b);for(let i=1;i<p.length;i++)expect(Math.abs(p[i].r-p[i-1].r)+Math.abs(p[i].c-p[i-1].c)).toBe(1);});
it('keeps safety thresholds unambiguous',()=>{expect(tier(65)).toBe('Favorable');expect(tier(64)).toBe('Caution');expect(tier(40)).toBe('Caution');expect(tier(39)).toBe('Critical');});
