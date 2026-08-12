import { existsSync, readFileSync, readdirSync } from "node:fs";
import { extname, join, relative, resolve } from "node:path";

const root=resolve(import.meta.dirname,"..");
const manifest=JSON.parse(readFileSync(resolve(root,"content/image-manifest.json"),"utf8"));
const missing=manifest.filter(item=>!existsSync(resolve(root,"public",item.path.replace(/^\//,""))));
if(missing.length){console.error("Missing marketing images:",missing.map(item=>item.path));process.exit(1)}
const walk=directory=>readdirSync(directory,{withFileTypes:true}).flatMap(entry=>entry.isDirectory()?walk(join(directory,entry.name)):[join(directory,entry.name)]);
const sourceFiles=[...walk(resolve(root,"app")),...walk(resolve(root,"components")),...walk(resolve(root,"content"))].filter(file=>[".ts",".tsx"].includes(extname(file)));
const forbidden=["app.breero.com","partners.breero.com","ops.breero.com","/partner/login","/ops/login"];
const forbiddenHits=sourceFiles.flatMap(file=>forbidden.filter(value=>readFileSync(file,"utf8").includes(value)).map(value=>`${relative(root,file)}: ${value}`));
if(forbiddenHits.length){console.error("Forbidden placeholder portal links:",forbiddenHits);process.exit(1)}
const pageFiles=walk(resolve(root,"app")).filter(file=>file.endsWith("page.tsx"));
const toRoute=file=>{const route=relative(resolve(root,"app"),file).replace(/\\/g,"/").replace(/(^|\/)\([^/]+\)\//g,"$1").replace(/\/page\.tsx$/,"/").replace(/^page\.tsx$/,"/").replace(/\/$/,"");return route?`/${route}`:"/"};
const staticRoutes=new Set(pageFiles.map(toRoute).filter(route=>!route.includes("[")));
const dynamicPrefixes=pageFiles.map(toRoute).filter(route=>route.includes("[")).map(route=>route.slice(0,route.indexOf("/[")));
const hrefPattern=/(?:href\s*=\s*|href\s*:\s*)["'](\/[^"'#?]*)/g;
const links=sourceFiles.flatMap(file=>[...readFileSync(file,"utf8").matchAll(hrefPattern)].map(match=>({file:relative(root,file),href:match[1].replace(/\/$/,"")||"/"})));
const broken=links.filter(({href})=>!staticRoutes.has(href)&&!dynamicPrefixes.some(prefix=>href.startsWith(`${prefix}/`)));
if(broken.length){console.error("Broken internal marketing links:",broken);process.exit(1)}
console.log(`Validated ${manifest.length} manifested images and ${links.length} internal links across ${staticRoutes.size} static routes.`);
