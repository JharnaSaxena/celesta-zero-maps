import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {elevationColor} from './MapView.js';
export function View3D(elevation,route){
 const dialog=document.querySelector('#terrain-dialog'),host=document.querySelector('#three-host');dialog.showModal();host.innerHTML='';let renderer;
 try{renderer=new THREE.WebGLRenderer({antialias:true});}catch{host.textContent='WebGL is unavailable in this browser. The 2D terrain view remains available.';return;}
 renderer.setPixelRatio(Math.min(devicePixelRatio,2));host.append(renderer.domElement);const scene=new THREE.Scene();scene.background=new THREE.Color('#e9eee6');const camera=new THREE.PerspectiveCamera(45,1,.1,1000);camera.position.set(62,65,70);const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.target.set(0,7,0);
 const geometry=new THREE.PlaneGeometry(80,80,49,49);geometry.rotateX(-Math.PI/2);const positions=geometry.attributes.position,colors=[];
 // Plane row zero is north; the stored grid row zero is south.
 for(let i=0;i<positions.count;i++){const r=49-Math.floor(i/50),c=i%50,v=elevation.values[r][c];positions.setY(i,(v-750)/25);const color=new THREE.Color(elevationColor(v));colors.push(color.r,color.g,color.b);}geometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));geometry.computeVertexNormals();scene.add(new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({vertexColors:true,side:THREE.DoubleSide,roughness:1})));
 scene.add(new THREE.HemisphereLight(0xffffff,0x556649,2));const light=new THREE.DirectionalLight(0xffffff,2);light.position.set(-40,70,20);scene.add(light);
 let lineGeometry,lineMaterial;if(route.length){lineGeometry=new THREE.BufferGeometry().setFromPoints(route.map(n=>new THREE.Vector3(n.c/49*80-40,(n.elevation-750)/25+.5,40-n.r/49*80)));lineMaterial=new THREE.LineBasicMaterial({color:0x172f29});scene.add(new THREE.Line(lineGeometry,lineMaterial));}
 const resize=()=>{const w=host.clientWidth,h=host.clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();};const observer=new ResizeObserver(resize);observer.observe(host);resize();renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,camera);});dialog.addEventListener('close',()=>{observer.disconnect();renderer.setAnimationLoop(null);controls.dispose();geometry.dispose();scene.traverse(o=>{if(o.isMesh)o.material.dispose();});lineGeometry?.dispose();lineMaterial?.dispose();renderer.dispose();host.innerHTML='';},{once:true});
}
