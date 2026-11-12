import {DatabaseSync,backup as sqliteBackup} from 'node:sqlite';
import {createHash} from 'node:crypto';
import {createReadStream} from 'node:fs';
import {mkdir,realpath,lstat,readdir,copyFile,writeFile,readFile} from 'node:fs/promises';
import {resolve,dirname,sep,isAbsolute,basename} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../../..');
const imageName=/^[a-f0-9]{64}\.(png|jpg|webp)$/;
async function sha(path){const h=createHash('sha256');for await(const chunk of createReadStream(path))h.update(chunk);return h.digest('hex');}
function outsideRepository(path){if(path===root || path.startsWith(root+sep))throw Error('バックアップ・復元先は公開リポジトリ外にしてください');}
async function newPrivateDirectory(path,source){
  if(!isAbsolute(path))throw Error('保存先は絶対パスにしてください');
  const normalized=resolve(path),target=resolve(await realpath(dirname(normalized)),basename(normalized));outsideRepository(target);
  if(target===source || target.startsWith(source+sep))throw Error('保存元と別のディレクトリを指定してください');
  await mkdir(target,{mode:0o700});return target; // EEXIST intentionally refuses to overwrite.
}
function checkDatabase(path){
  const db=new DatabaseSync(path,{readOnly:true});
  try{if(db.prepare('PRAGMA quick_check').get().quick_check!=='ok')throw Error('SQLite整合性検査に失敗しました');
    const tables=db.prepare("SELECT count(*) AS n FROM sqlite_master WHERE type='table' AND name IN ('articles','versions','sessions','requests')").get().n;
    if(tables!==4)throw Error('管理センターのデータベースではありません');
  }finally{db.close();}
}
export async function createBackup(dataDir,destination){
  const source=await realpath(dataDir);outsideRepository(source);
  const database=resolve(source,'admin.sqlite');if(!(await lstat(database)).isFile())throw Error('データベースが通常ファイルではありません');
  if(!(await lstat(resolve(source,'images'))).isDirectory())throw Error('画像保存先は通常のディレクトリにしてください');
  const target=await newPrivateDirectory(destination,source),db=new DatabaseSync(database,{readOnly:true});
  try{await sqliteBackup(db,resolve(target,'admin.sqlite'));}finally{db.close();}
  checkDatabase(resolve(target,'admin.sqlite'));
  await mkdir(resolve(target,'images'),{mode:0o700});
  const files={'admin.sqlite':await sha(resolve(target,'admin.sqlite'))};
  // Uploaded images are immutable and never deleted: copying after the DB snapshot
  // retains every image referenced by that snapshot, including concurrent saves.
  for(const name of await readdir(resolve(source,'images'))){
    if(!imageName.test(name))throw Error('画像保存先に想定外のファイルがあります');
    const src=resolve(source,'images',name);if(!(await lstat(src)).isFile())throw Error('画像が通常ファイルではありません');
    const key='images/'+name;await copyFile(src,resolve(target,key));files[key]=await sha(resolve(target,key));
    if(files[key]!==name.split('.')[0])throw Error('画像の内容とファイル名が一致しません');
  }
  await writeFile(resolve(target,'manifest.json'),JSON.stringify({version:1,createdAt:new Date().toISOString(),files},null,2)+'\n',{mode:0o600,flag:'wx'});
  return target;
}
export async function restoreBackup(backupDir,destination){
  const source=await realpath(backupDir);outsideRepository(source);
  const manifest=JSON.parse(await readFile(resolve(source,'manifest.json'),'utf8'));
  if(manifest.version!==1 || !manifest.files || typeof manifest.files['admin.sqlite']!=='string')throw Error('バックアップ形式が不正です');
  for(const [key,expected] of Object.entries(manifest.files)){
    if(key!=='admin.sqlite' && !(key.startsWith('images/') && imageName.test(key.slice(7))))throw Error('バックアップのファイル名が不正です');
    if(typeof expected!=='string' || !/^[a-f0-9]{64}$/.test(expected))throw Error('チェックサム形式が不正です');
    const path=resolve(source,key);if(!(await realpath(path)).startsWith(source+sep) || !(await lstat(path)).isFile() || await sha(path)!==expected)throw Error('バックアップの整合性検査に失敗しました');
  }
  checkDatabase(resolve(source,'admin.sqlite'));
  const target=await newPrivateDirectory(destination,source);await mkdir(resolve(target,'images'),{mode:0o700});
  for(const key of Object.keys(manifest.files))await copyFile(resolve(source,key),resolve(target,key));
  const db=new DatabaseSync(resolve(target,'admin.sqlite'));
  try{db.exec('BEGIN IMMEDIATE; DELETE FROM sessions; DELETE FROM attempts; COMMIT;');}finally{db.close();}
  checkDatabase(resolve(target,'admin.sqlite'));return target;
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
  const [action,source,destination]=process.argv.slice(2);
  if(!['create','restore'].includes(action) || !source || !destination)throw Error('使い方: node src/backup.js create|restore 保存元 新しい保存先');
  try{await (action==='create'?createBackup:restoreBackup)(source,destination);console.log(action==='create'?'非公開バックアップを作成しました':'新しい保存先へ復元し、旧セッションを失効させました');}
  catch(e){console.error(e.code==='EEXIST'?'保存先が既に存在します。上書きは行いません。':e.message);process.exitCode=1;}
}
