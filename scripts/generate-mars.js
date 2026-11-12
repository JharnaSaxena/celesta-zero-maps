import {writeFileSync} from 'node:fs';
import {SEED,SIZE,SPAN,sites,generateTerrain} from '../src/mars/model.js';
writeFileSync(new URL('../data/mock/mars.json',import.meta.url),JSON.stringify({seed:SEED,size:SIZE,spanKm:SPAN,description:'Synthetic Jezero-inspired terrain, not georeferenced Mars data',sites,nodes:generateTerrain()},null,2));
