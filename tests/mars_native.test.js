import {test} from 'node:test';
import assert from 'node:assert';
import {generateTerrain, nearest, routeTo, sites, SIZE, tier} from '../src/mars/model.js';
import {dijkstra} from '../src/algorithms/dijkstra.js';

test('generates reproducible 65-square Mars data and bounded margins', () => {
  const a = generateTerrain(), b = generateTerrain();
  assert.deepStrictEqual(a, b);
  assert.strictEqual(a.length, SIZE * SIZE);
  assert.strictEqual(a.every(n => Number.isFinite(n.slope) && n.margin >= 0 && n.margin <= 100), true);
  assert.notDeepStrictEqual(generateTerrain(7), a);
});

test('finds contiguous base-to-target paths on the real mock graph', () => {
  const n = generateTerrain();
  const a = nearest(n, sites[0].x, sites[0].z);
  const b = nearest(n, sites[5].x, sites[5].z);
  const p = routeTo(n, a, b);
  assert.deepStrictEqual(p[0], a);
  assert.deepStrictEqual(p.at(-1), b);
  for (let i = 1; i < p.length; i++) {
    assert.strictEqual(Math.abs(p[i].r - p[i-1].r) + Math.abs(p[i].c - p[i-1].c), 1);
  }
});

test('keeps safety thresholds unambiguous', () => {
  assert.strictEqual(tier(65), 'Favorable');
  assert.strictEqual(tier(64), 'Caution');
  assert.strictEqual(tier(40), 'Caution');
  assert.strictEqual(tier(39), 'Critical');
});

test('dijkstra pathfinding on synthetic graph', () => {
  const g = new Map([
    [1, [{to: 2, weight: 2}, {to: 3, weight: 5}]],
    [2, [{to: 3, weight: 1}, {to: 4, weight: 7}]],
    [3, [{to: 4, weight: 2}]],
    [4, []]
  ]);
  const res = dijkstra(g, 1, 4);
  assert.strictEqual(res.cost, 5);
  assert.deepStrictEqual(res.path, [1, 2, 3, 4]);
});
