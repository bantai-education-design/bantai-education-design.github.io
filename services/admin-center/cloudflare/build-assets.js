import {mkdir,cp,writeFile,readdir,readFile,rm} from 'node:fs/promises';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {importLegacy,legacyCandidatePath} from '../src/legacy.js';
import {existsSync} from 'node:fs';
import {PROFILE_FIELDS} from '../src/university.js';
const here=dirname(fileURLToPath(import.meta.url)),root=resolve(here,'../../..'),dest=resolve(here,'public');
// Only generated output is replaced. No source articles, DB files or images are edited.
await rm(dest,{recursive:true,force:true});await mkdir(dest,{recursive:true});
for(const path of ['admin/center','assets/images','assets/css','assets/style.css','data/columns.json']){await mkdir(dirname(resolve(dest,path)),{recursive:true});await cp(resolve(root,path),resolve(dest,path),{recursive:true});}
const rows=[];
for(const region of ['tokyo','kanagawa','saitama']){const base=resolve(root,'tools/university-database',region,'data/complete');for(const name of await readdir(base)){if(!/^u[0-9]{6}\.json$/.test(name))continue;const p=JSON.parse(await readFile(resolve(base,name),'utf8'));rows.push({region,id:p.university_id,name:p.name,fields:Object.fromEntries(Object.keys(PROFILE_FIELDS).map(k=>[k,p[k]||''])),source:p.official_url||'',fieldLabels:PROFILE_FIELDS});}}
await writeFile(resolve(dest,'data/admin-university-profiles.json'),JSON.stringify(rows));
console.log('Cloudflare public assets prepared (private drafts/images are not included).');

const catalog=JSON.parse(await readFile(resolve(root,'data/columns.json'),'utf8')),imports={};
for(const entry of catalog){let path=legacyCandidatePath(entry);if(path&&!existsSync(resolve(root,path)))path=null;imports[entry.id]=importLegacy(entry,path?await readFile(resolve(root,path),'utf8'):null,path);}
await writeFile(resolve(here,'generated-legacy.json'),JSON.stringify(imports));
console.log('Trusted legacy imports prepared privately at build time (not in public assets).');
