import {defineConfig} from 'vite';
export default defineConfig({server:{host:'0.0.0.0',allowedHosts:['terminal.local']},build:{rollupOptions:{input:{main:'index.html',earth:'earth.html'}}}});
