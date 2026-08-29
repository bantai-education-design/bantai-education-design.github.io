(()=>{
'use strict';
if(new URLSearchParams(location.search).get('mode')!=='owner')return;

const universitySelect=document.querySelector('#university-first-select');
const list=document.querySelector('#batch-list');
const generate=document.querySelector('#generate-batch');
const downloadZip=document.querySelector('#download-zip');
const result=document.querySelector('#result');
const jsonOutput=document.querySelector('#json-output');
const resultUniversity=document.querySelector('#result-university');
const batchStatus=document.querySelector('#batch-status');
const preview=document.querySelector('#preview');
if(!universitySelect||!list||!generate||!downloadZip||!result||!jsonOutput||!preview)return;

const MAX=9;
const enc=new TextEncoder();
const defaults={rotation:0,tilt:0,zoom:100,x:50,y:50,brightness:100,contrast:100};
let registry={schema_version:2,purpose:'撮影者本人から提供された大学実景写真を、現実の光景を改変せず既存の公開画像台帳へ安全に上書きする。',records:{}};
let ownerZip=null;
let ownerZipName='';
let mergedRegistry=null;
let busy=false;
let refreshQueued=false;

const registryReady=fetch('../data/user-photo-overrides.json',{cache:'no-store'})
  .then(r=>r.ok?r.json():registry)
  .then(data=>{registry=data&&typeof data==='object'?data:registry;return registry;})
  .catch(()=>registry);

function helper(){return window.__universityPhotoMainChoice||null;}
function rows(){return [...list.querySelectorAll('.batch-row')];}
function safeName(name){return String(name||'photo').normalize('NFKC').replace(/[\\/:*?"<>|]/g,'-').replace(/\s+/g,'-').replace(/-+/g,'-').replace(/^-|-$/g,'').slice(0,50)||'photo';}
function selectedUniversityName(){const option=universitySelect.selectedOptions?.[0];return String(option?.textContent||'').replace(/（u\d{6}）\s*$/,'').trim()||'大学';}
function excludedUrls(){return new Set((helper()?.getExcludedPhotos?.()||[]).map(value=>String(value).replace(/^existing:/,'')));}
function photoUrl(item){return item?.image_url||item?.source_url||'';}
function uniquePhotos(items){const seen=new Set();return items.filter(item=>{const url=photoUrl(item);if(!url||seen.has(url))return false;seen.add(url);return true;});}
function ownerPhotos(record){
  if(!record?.image_url)return [];
  const main={
    image_url:record.image_url,
    source_url:record.source_url||record.image_url,
    alt:record.alt||`${record.university_name||'大学'}のキャンパス実景`,
    source_label:record.source_label||'撮影者提供・実景保持',
    role:'main'
  };
  const extras=[...(Array.isArray(record.gallery)?record.gallery:[]),...(Array.isArray(record.images)?record.images:[])].map(item=>({
    ...item,
    image_url:photoUrl(item),
    source_url:item?.source_url||photoUrl(item),
    role:'sub'
  }));
  return uniquePhotos([main,...extras]);
}
function deletedOwnerUrls(record){
  const known=new Set(ownerPhotos(record).map(photoUrl));
  return [...excludedUrls()].filter(url=>known.has(url));
}
function keptOwnerPhotos(record){const excluded=excludedUrls();return ownerPhotos(record).filter(item=>!excluded.has(photoUrl(item)));}
function choice(){return helper()?.getChoice?.()||{type:'new',key:''};}
function rowAssignmentsValid(id){const all=rows();return all.every(row=>(row.querySelector('.row-university')?.value||id)===id);}
function currentState(){
  const id=universitySelect.value||'';
  const record=id?(registry.records?.[id]||null):null;
  const kept=keptOwnerPhotos(record);
  const deleted=deletedOwnerUrls(record);
  const newRows=rows();
  const selected=choice();
  const mainChanged=!!record&&selected.type==='existing'&&selected.key&&selected.key!==record.image_url&&kept.some(x=>photoUrl(x)===selected.key);
  const changed=newRows.length>0||deleted.length>0||mainChanged;
  return {id,record,kept,deleted,newRows,selected,total:kept.length+newRows.length,changed};
}
function applyState(){
  refreshQueued=false;
  if(busy){generate.disabled=true;return;}
  const state=currentState();
  const valid=!!state.id&&state.total<=MAX&&state.changed&&rowAssignmentsValid(state.id);
  generate.disabled=!valid;
  if(batchStatus&&state.id){
    if(state.total>MAX){batchStatus.textContent=`写真は最大${MAX}枚です（現在${state.total}枚）`;batchStatus.classList.add('warn');}
    else if(state.changed){batchStatus.textContent=`登録後 ${state.total}枚（メイン1＋サブ${Math.max(0,state.total-1)}）`;batchStatus.classList.remove('warn');}
  }
  document.documentElement.dataset.ownerPhotoSetReady=valid?'true':'false';
}
function scheduleState(){if(refreshQueued)return;refreshQueued=true;setTimeout(applyState,0);}

function canvasBlob(canvas){return new Promise((resolve,reject)=>canvas.toBlob(blob=>blob?resolve(blob):reject(new Error('JPEG生成失敗')),'image/jpeg',0.9));}
async function sha256(blob){const buffer=await blob.arrayBuffer();const hash=await crypto.subtle.digest('SHA-256',buffer);return [...new Uint8Array(hash)].map(x=>x.toString(16).padStart(2,'0')).join('');}
async function waitFrames(count=2){for(let i=0;i<count;i++)await new Promise(resolve=>requestAnimationFrame(()=>resolve()));}
async function sourceBlobForRow(key){
  const row=list.querySelector(`.batch-row[data-key="${CSS.escape(key)}"]`);
  const img=row?.querySelector('.thumb img');
  if(!img?.src)throw new Error('元写真を取得できません');
  const response=await fetch(img.src);
  if(!response.ok)throw new Error('元写真を取得できません');
  return response.blob();
}
async function renderNewPhoto(key,index,id,name){
  let row=list.querySelector(`.batch-row[data-key="${CSS.escape(key)}"]`);
  if(!row)throw new Error('写真一覧が更新されたため、もう一度登録してください');
  const filename=row.querySelector('.batch-main strong')?.textContent?.trim()||`photo-${index+1}`;
  const source=await sourceBlobForRow(key);
  row.querySelector('.edit-item')?.click();
  await waitFrames(3);
  const jpeg=await canvasBlob(preview);
  const sourceHash=await sha256(source);
  const outputHash=await sha256(jpeg);
  const cardName=`${id}-${safeName(name)}-owner-${String(index+1).padStart(2,'0')}.jpg`;
  const relative=`assets/card-images/${cardName}`;
  return {
    key,
    filename,
    source,
    jpeg,
    sourceHash,
    outputHash,
    relative,
    entry:{
      image_url:relative,
      source_url:relative,
      alt:`${name}のキャンパス実景`,
      source_label:'撮影者提供・実景保持',
      role:'sub',
      source_file:{name:filename,sha256:sourceHash},
      card_file:{name:cardName,width:720,height:405,quality:0.9,sha256:outputHash}
    }
  };
}

function rightsBase(id,name){return {
  university_id:id,
  university_name:name,
  rights_status:'verified',
  rights_basis:'photographer_permission',
  source_label:'撮影者提供・実景保持',
  creator:'Ban.Tai Education Design提供',
  license:'撮影者本人提供・本DB利用許諾',
  rights_note:'撮影者本人からBan.Tai東京都大学DBでの利用許諾を受けた実景写真。大学公式写真の転載ではない。生成AIによる再描画・生成補完・景観要素の追加削除・背景置換は行わず、90度単位の回転、±5度以内の傾き補正、軽微なトリミング、明るさ・コントラスト調整だけを許可する。',
  reviewed_at:new Date().toISOString().slice(0,10),
  scene_integrity:'scene_unchanged',
  ai_redraw:false,
  surfaces:['card','detail'],
  allowed_adjustments:['rotation','straighten','brightness','contrast','crop','resize'],
  forbidden_adjustments:['generative_redraw','object_addition','object_removal','background_replacement','scene_composite']
};}
function asGalleryEntry(item,name){return {
  image_url:photoUrl(item),
  source_url:item.source_url||photoUrl(item),
  alt:item.alt||`${name}のキャンパス実景`,
  source_label:item.source_label||'撮影者提供・実景保持',
  role:'sub',
  ...(item.source_file?{source_file:item.source_file}:{}),
  ...(item.card_file?{card_file:item.card_file}:{})
};}
function chooseMain(state,newPhotos,finalPhotos){
  const selected=state.selected;
  if(selected.type==='new'&&selected.key){const hit=newPhotos.find(item=>item.key===selected.key);if(hit)return hit.entry;}
  if(selected.type==='existing'&&selected.key){const hit=state.kept.find(item=>photoUrl(item)===selected.key);if(hit)return hit;}
  if(state.record?.image_url){const old=state.kept.find(item=>photoUrl(item)===state.record.image_url);if(old)return old;}
  return finalPhotos[0]||null;
}

function crcTable(){const table=[];for(let n=0;n<256;n++){let c=n;for(let k=0;k<8;k++)c=(c&1)?0xedb88320^(c>>>1):c>>>1;table[n]=c>>>0;}return table;}const CRC=crcTable();
function crc32(bytes){let c=0xffffffff;for(const b of bytes)c=CRC[(c^b)&255]^(c>>>8);return (c^0xffffffff)>>>0;}
function le16(n){const b=new Uint8Array(2);new DataView(b.buffer).setUint16(0,n,true);return b;}
function le32(n){const b=new Uint8Array(4);new DataView(b.buffer).setUint32(0,n>>>0,true);return b;}
function concat(parts){const len=parts.reduce((sum,part)=>sum+part.length,0);const out=new Uint8Array(len);let offset=0;for(const part of parts){out.set(part,offset);offset+=part.length;}return out;}
async function makeZip(entries){const locals=[],centrals=[];let offset=0;for(const entry of entries){const name=enc.encode(entry.name);const data=entry.data instanceof Uint8Array?entry.data:new Uint8Array(await entry.data.arrayBuffer());const crc=crc32(data);const local=concat([le32(0x04034b50),le16(20),le16(0),le16(0),le16(0),le16(0),le32(crc),le32(data.length),le32(data.length),le16(name.length),le16(0),name,data]);locals.push(local);const central=concat([le32(0x02014b50),le16(20),le16(20),le16(0),le16(0),le16(0),le16(0),le32(crc),le32(data.length),le32(data.length),le16(name.length),le16(0),le16(0),le16(0),le16(0),le32(0),le32(offset),name]);centrals.push(central);offset+=local.length;}const centralBytes=concat(centrals);const end=concat([le32(0x06054b50),le16(0),le16(0),le16(entries.length),le16(entries.length),le32(centralBytes.length),le32(offset),le16(0)]);return new Blob([concat([...locals,centralBytes,end])],{type:'application/zip'});}
function download(blob,name){const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);}

async function generateOwnerSet(){
  await registryReady;
  const state=currentState();
  if(!state.id||state.total>MAX||!state.changed||!rowAssignmentsValid(state.id))throw new Error('大学・写真・削除内容を確認してください');
  busy=true;generate.disabled=true;document.documentElement.dataset.ownerPhotoSetExport='generating';
  try{
    const id=state.id,name=selectedUniversityName();
    const newKeys=state.newRows.map(row=>row.dataset.key||'').filter(Boolean);
    const newPhotos=[];
    for(let index=0;index<newKeys.length;index++)newPhotos.push(await renderNewPhoto(newKeys[index],index,id,name));
    const finalPhotos=uniquePhotos([...state.kept,...newPhotos.map(item=>item.entry)]);
    const main=chooseMain(state,newPhotos,finalPhotos);
    const records={...(registry.records||{})};
    if(!main){
      delete records[id];
    }else{
      const mainUrl=photoUrl(main);
      const gallery=finalPhotos.filter(item=>photoUrl(item)!==mainUrl).slice(0,MAX-1).map(item=>asGalleryEntry(item,name));
      records[id]={
        ...rightsBase(id,name),
        image_url:mainUrl,
        source_url:main.source_url||mainUrl,
        alt:main.alt||`${name}のキャンパス実景`,
        ...(main.source_file?{source_file:main.source_file}:{}),
        ...(main.card_file?{card_file:main.card_file}:{}),
        gallery
      };
    }
    mergedRegistry={...registry,schema_version:Math.max(2,Number(registry.schema_version)||2),records};
    const zipEntries=[];
    for(const item of newPhotos){
      zipEntries.push({name:`tools/university-database/tokyo/${item.relative}`,data:item.jpeg});
      zipEntries.push({name:`source-originals/${id}-${safeName(name)}-${safeName(item.filename)}`,data:item.source});
    }
    const manifest={
      schema_version:2,
      kind:'university_owner_photo_set',
      generated_at:new Date().toISOString(),
      university_id:id,
      university_name:name,
      replacement_mode:'authoritative_photo_set',
      max_photos:MAX,
      main_image_url:records[id]?.image_url||null,
      gallery_image_urls:records[id]?.gallery?.map(x=>x.image_url)||[],
      deleted_image_urls:state.deleted,
      owner_record_removed:!records[id],
      scene_policy:'scene_unchanged',
      ai_redraw:false,
      target_registry:'tools/university-database/tokyo/data/user-photo-overrides.json',
      new_files:newPhotos.map(item=>({image_url:item.relative,source_file:item.filename,source_sha256:item.sourceHash,output_sha256:item.outputHash}))
    };
    zipEntries.push({name:'tools/university-database/tokyo/data/user-photo-overrides.json',data:enc.encode(JSON.stringify(mergedRegistry,null,2)+'\n')});
    zipEntries.push({name:'photo-set-manifest.json',data:enc.encode(JSON.stringify(manifest,null,2)+'\n')});
    ownerZip=await makeZip(zipEntries);
    ownerZipName=`university-owner-photo-set-${id}-${new Date().toISOString().slice(0,10)}.zip`;
    jsonOutput.value=JSON.stringify(mergedRegistry,null,2);
    if(resultUniversity)resultUniversity.textContent=`${name}：${main?`${1+(records[id]?.gallery?.length||0)}枚（メイン1＋サブ${records[id]?.gallery?.length||0}）`:'本人写真をすべて解除'}`;
    result.hidden=false;
    downloadZip.disabled=false;
    document.documentElement.dataset.ownerPhotoSetExport='ready';
    window.__ownerPhotoSetLastManifest=manifest;
  }finally{
    busy=false;
    scheduleState();
  }
}

generate.addEventListener('click',event=>{
  event.preventDefault();
  event.stopImmediatePropagation();
  if(generate.disabled)return;
  generateOwnerSet().catch(error=>{
    console.error('owner photo set export failed',error);
    document.documentElement.dataset.ownerPhotoSetExport='error';
    if(batchStatus){batchStatus.textContent=error.message||'登録データを作成できませんでした';batchStatus.classList.add('warn');}
    ownerZip=null;downloadZip.disabled=true;busy=false;scheduleState();
  });
},true);

downloadZip.addEventListener('click',event=>{
  if(!ownerZip)return;
  event.preventDefault();
  event.stopImmediatePropagation();
  download(ownerZip,ownerZipName);
  document.documentElement.dataset.ownerPhotoSetExport='saved';
},true);

universitySelect.addEventListener('change',()=>{ownerZip=null;scheduleState();});
document.addEventListener('click',event=>{
  if(event.target.closest?.('.main-photo-choice-card,.photo-list-delete,.remove-item,.photo-main-button'))setTimeout(scheduleState,20);
},true);
new MutationObserver(scheduleState).observe(list,{childList:true,subtree:true});
new MutationObserver(scheduleState).observe(generate,{attributes:true,attributeFilter:['disabled']});
registryReady.finally(()=>{document.documentElement.dataset.ownerPhotoSetEngine='ready';scheduleState();});
window.__ownerPhotoSetExport={refresh:scheduleState,getState:currentState,getRegistry:()=>mergedRegistry,getManifest:()=>window.__ownerPhotoSetLastManifest||null};
})();
