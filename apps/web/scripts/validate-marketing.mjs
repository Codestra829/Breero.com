import { existsSync, readFileSync, readdirSync } from "node:fs";
import { extname, join, relative, resolve } from "node:path";

const root=resolve(import.meta.dirname,"..");
const manifest=JSON.parse(readFileSync(resolve(root,"content/image-manifest.json"),"utf8"));
const publicRoutes=JSON.parse(readFileSync(resolve(root,"content/public-routes.json"),"utf8"));
const imageSource=readFileSync(resolve(root,"content/images.ts"),"utf8");
const imageDefinitions=[...imageSource.matchAll(/\s(\w+): image\("([^"]+)", "([^"]+)"\)/g)].map(([,id,path,alt])=>({id,path,alt}));
const manifestDrift=manifest.filter((item,index)=>JSON.stringify({id:item.id,path:item.path,alt:item.alt})!==JSON.stringify(imageDefinitions[index]));
if(imageDefinitions.length!==manifest.length||manifestDrift.length){console.error("Image manifest and TypeScript definitions have drifted",{definitionCount:imageDefinitions.length,manifestCount:manifest.length,manifestDrift});process.exit(1)}
const missing=manifest.filter(item=>!existsSync(resolve(root,"public",item.path.replace(/^\//,""))));
if(missing.length){console.error("Missing marketing images:",missing.map(item=>item.path));process.exit(1)}
const walk=directory=>readdirSync(directory,{withFileTypes:true}).flatMap(entry=>entry.isDirectory()?walk(join(directory,entry.name)):[join(directory,entry.name)]);
const sourceFiles=[...walk(resolve(root,"app")),...walk(resolve(root,"components")),...walk(resolve(root,"content"))].filter(file=>[".ts",".tsx"].includes(extname(file)));
const forbidden=["app.breero.com","partners.breero.com","ops.breero.com","/partner/login","/ops/login"];
const forbiddenHits=sourceFiles.flatMap(file=>forbidden.filter(value=>readFileSync(file,"utf8").includes(value)).map(value=>`${relative(root,file)}: ${value}`));
if(forbiddenHits.length){console.error("Forbidden placeholder portal links:",forbiddenHits);process.exit(1)}
const obsoleteIdentity=["Booked4"+"Seasons","BREERO "+"Ltd.","hello"+"@breero.com"];
const obsoleteIdentityHits=sourceFiles.flatMap(file=>obsoleteIdentity.filter(value=>readFileSync(file,"utf8").toLowerCase().includes(value.toLowerCase())).map(value=>`${relative(root,file)}: ${value}`));
if(obsoleteIdentityHits.length){console.error("Obsolete public identity references:",obsoleteIdentityHits);process.exit(1)}
const placeholderLinks=[/href\s*=\s*["']#["']/g,/href\s*=\s*["']javascript:/gi];
const placeholderHits=sourceFiles.flatMap(file=>placeholderLinks.flatMap(pattern=>[...readFileSync(file,"utf8").matchAll(pattern)].map(match=>`${relative(root,file)}: ${match[0]}`)));
if(placeholderHits.length){console.error("Placeholder links:",placeholderHits);process.exit(1)}
const buttonTags=sourceFiles.filter(file=>!file.endsWith("brand-preview/page.tsx")).flatMap(file=>[...readFileSync(file,"utf8").matchAll(/<(?:button|Button)\b([^>]*)>/g)].map(match=>({file:relative(root,file),tag:match[0],attributes:match[1]})));
const deadButtons=buttonTags.filter(({attributes})=>!/(?:onClick\s*=|type\s*=\s*["']submit["']|disabled(?:\s|=|$)|loading\s*=)/.test(attributes));
if(deadButtons.length){console.error("Actionless buttons:",deadButtons.map(item=>`${item.file}: ${item.tag}`));process.exit(1)}
const pageFiles=walk(resolve(root,"app")).filter(file=>file.endsWith("page.tsx"));
const toRoute=file=>{const route=relative(resolve(root,"app"),file).replace(/\\/g,"/").replace(/(^|\/)\([^/]+\)\//g,"$1").replace(/\/page\.tsx$/,"/").replace(/^page\.tsx$/,"/").replace(/\/$/,"");return route?`/${route}`:"/"};
const staticRoutes=new Set(pageFiles.map(toRoute).filter(route=>!route.includes("[")));
const dynamicPrefixes=pageFiles.map(toRoute).filter(route=>route.includes("[")).map(route=>route.slice(0,route.indexOf("/[")));
const hrefPattern=/(?:href\s*=\s*|href\s*:\s*)["'](\/[^"'#?]*)/g;
const links=sourceFiles.flatMap(file=>[...readFileSync(file,"utf8").matchAll(hrefPattern)].map(match=>({file:relative(root,file),href:match[1].replace(/\/$/,"")||"/"})));
const broken=links.filter(({href})=>!staticRoutes.has(href)&&!dynamicPrefixes.some(prefix=>href.startsWith(`${prefix}/`)));
if(broken.length){console.error("Broken internal marketing links:",broken);process.exit(1)}
const missingPublicRoutes=publicRoutes.filter(route=>!staticRoutes.has(route)&&!dynamicPrefixes.some(prefix=>route.startsWith(`${prefix}/`)));
if(missingPublicRoutes.length){console.error("Missing intended public routes:",missingPublicRoutes);process.exit(1)}
const ctaCount=sourceFiles.reduce((count,file)=>count+[...readFileSync(file,"utf8").matchAll(/data-cta\s*=/g)].length,0);
console.log(`Validated ${manifest.length} manifested images, ${links.length} internal links, ${buttonTags.length} actionable buttons, ${ctaCount} CTA definitions, and ${publicRoutes.length} intended public routes across ${staticRoutes.size} static routes.`);
