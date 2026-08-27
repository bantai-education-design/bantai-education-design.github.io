(()=>{
'use strict';
const $=s=>document.querySelector(s);
const university=$('#review-university');
const submissionId=$('#review-submission-id');
const input=$('#review-photo-input');
const list=$('#review-photo-list');
const loadStatus=$('#review-load-status');
const workspace=$('#review-editor-workspace');
const exportPanel=$('#review-export-panel');
const activeFile=$('#review-active-file');
const canvas=$('#review-preview');
const ctx=canvas.getContext('2d',{alpha:false});
const cardImage=$('#review-card-image');
const cardUniversity=$('#review-card-university');
const rights=$('#review-rights-confirm');
const generate=$('#review-generate');
const downloadButton=$('#review-download');
const exportStatus=$('#review-export-status');
const rotateLeft=$('#review-rotate-left');
const rotateRight=$('#review-rotate-right');
const reset=$('#review-reset');
const controls={
  tilt:$('#review-tilt'),zoom:$('#review-zoom'),x:$('#review-x'),y:$('#review-y'),
  brightness:$('#review-brightness'),contrast:$('#review-contrast')
};
const outputs={
  tilt:$('#review-tilt-out'),zoom:$('#review-zoom-out'),x:$('#review-x-out'),y:$('#review-y-out'),
  brightness:$('#review-brightness-out'),contrast:$('#review-contrast-out'),rotation:$('#review-rotation-out')
};
const defaults={rotation:0,tilt:0,zoom:100,x:50,y:50,brightness:100,contrast:100};
const enc=new TextEncoder();
let items=[];
let activeKey='';
let mainKey='';
let zipBlob=null;

function uid(){return crypto.randomUUID?crypto.randomUUID():`${Date.now()}-${Math.random()}`;}
function active(){return items.find(x=>x.key===activeKey)||null;}
function main(){return items.find(x=>x.key===mainKey)||null;}
function safeName(value){return String(value||'university').normalize('NFKC').replace(/[\\/:*?"<>|]/g,'-').replace(/\s+/g,'-').replace(/-+/g,'-').replace(/^-|-$/g,'').slice(0,50)||'university';}
function loadImage(file){return new Promise((resolve,reject)=>{const url=URL.createObjectURL(file);const img=new Image();img.onload=()=>{URL.revokeObjectURL(url);resolve(img)};img.onerror=()=>{URL.revokeObjectURL(url);reject(new Error('画像を読み込めませんでした'))};img.src=url;});}
async function sha256(blob){const buf=await blob.arrayBuffer();const hash=await crypto.subtle.digest('SHA-256',buf);return [...new Uint8Array(hash)].map(v=>v.toString(16).padStart(2,'0')).join('');}
function canvasBlob(target){return new Promise((resolve,reject)=>target.toBlob(blob=>blob?resolve(blob):reject(new Error('JPEG生成に失敗しました')),'image/jpeg',0.9));}
function updateGenerateState(){
  const ok=items.length>0&&!!mainKey&&!!university.value.trim()&&rights.checked;
  generate.disabled=!ok;
  if(!items.length)loadStatus.textContent='写真未選択';
  else loadStatus.textContent=`${items.length}枚読み込み済み・メイン写真 ${main()?main().file.name:'未選択'}`;
  cardUniversity.textContent=university.value.trim()||'大学名';
}
function setOutputs(item){const a=item?.adjustments||defaults;outputs.rotation.textContent=`${Number(a.rotation||0)}°`;outputs.tilt.textContent=`${Number(a.tilt||0).toFixed(1)}°`;outputs.zoom.textContent=`${Number(a.zoom||100)}%`;outputs.x.textContent=String(Number(a.x??50));outputs.y.textContent=String(Number(a.y??50));outputs.brightness.textContent=`${Number(a.brightness||100)}%`;outputs.contrast.textContent=`${Number(a.contrast||100)}%`;}
function drawItem(item,target,targetCtx){
  if(!item){targetCtx.fillStyle='#111';targetCtx.fillRect(0,0,target.width,target.height);return;}
  const a={...defaults,...item.adjustments};
  const cw=target.width,ch=target.height,iw=item.image.naturalWidth||item.image.width,ih=item.image.naturalHeight||item.image.height;
  const rotation=((Number(a.rotation)||0)%360+360)%360;
  const tilt=Number(a.tilt)||0,tiltRad=tilt*Math.PI/180;
  const quarter=rotation===90||rotation===270,rw=quarter?ih:iw,rh=quarter?iw:ih;
  const c=Math.abs(Math.cos(tiltRad)),s=Math.abs(Math.sin(tiltRad));
  const requiredW=(cw*c+ch*s)/rw,requiredH=(cw*s+ch*c)/rh;
  const scale=Math.max(requiredW,requiredH)*(Number(a.zoom)/100);
  const effectiveW=rw*scale,effectiveH=rh*scale;
  const overflowX=Math.max(0,effectiveW-cw),overflowY=Math.max(0,effectiveH-ch);
  const shiftX=((50-Number(a.x))/50)*(overflowX/2),shiftY=((50-Number(a.y))/50)*(overflowY/2);
  targetCtx.save();
  targetCtx.fillStyle='#111';targetCtx.fillRect(0,0,cw,ch);
  targetCtx.translate(cw/2+shiftX,ch/2+shiftY);
  targetCtx.rotate((rotation+tilt)*Math.PI/180);
  targetCtx.filter=`brightness(${a.brightness}%) contrast(${a.contrast}%)`;
  targetCtx.drawImage(item.image,-iw*scale/2,-ih*scale/2,iw*scale,ih*scale);
  targetCtx.restore();
}
function syncEditor(){
  const item=active();
  if(!item){workspace.hidden=true;return;}
  workspace.hidden=false;exportPanel.hidden=false;activeFile.textContent=`編集中: ${item.file.name}`;
  item.adjustments={...defaults,...item.adjustments};
  Object.entries(controls).forEach(([key,el])=>{el.value=item.adjustments[key]??defaults[key];});
  setOutputs(item);drawItem(item,canvas,ctx);refreshCardPreview();
}
function refreshCardPreview(){
  const item=main();
  if(!item){cardImage.removeAttribute('src');return;}
  const out=document.createElement('canvas');out.width=720;out.height=405;drawItem(item,out,out.getContext('2d',{alpha:false}));
  cardImage.src=out.toDataURL('image/jpeg',0.86);
  cardUniversity.textContent=university.value.trim()||'大学名';
}
function renderList(){
  list.innerHTML='';
  items.forEach(item=>{
    const row=document.createElement('div');row.className='review-photo-row'+(item.key===activeKey?' active':'');
    row.innerHTML=`<img src="${item.previewUrl}" alt=""><div class="review-photo-meta"><strong></strong><small></small></div><div class="review-photo-actions"><label><input type="radio" name="review-main" ${item.key===mainKey?'checked':''}> メイン</label><button type="button" class="edit-photo">編集</button><button type="button" class="remove-photo">削除</button></div>`;
    row.querySelector('.review-photo-meta strong').textContent=item.file.name;
    row.querySelector('.review-photo-meta small').textContent=`${item.image.naturalWidth}×${item.image.naturalHeight}`;
    row.querySelector('input[type=radio]').addEventListener('change',()=>{mainKey=item.key;zipBlob=null;downloadButton.disabled=true;renderList();refreshCardPreview();updateGenerateState();});
    row.querySelector('.edit-photo').addEventListener('click',()=>{activeKey=item.key;renderList();syncEditor();workspace.scrollIntoView({behavior:'smooth',block:'start'});});
    row.querySelector('.remove-photo').addEventListener('click',()=>{URL.revokeObjectURL(item.previewUrl);items=items.filter(x=>x.key!==item.key);if(mainKey===item.key)mainKey=items[0]?.key||'';if(activeKey===item.key)activeKey=items[0]?.key||'';zipBlob=null;downloadButton.disabled=true;renderList();syncEditor();refreshCardPreview();updateGenerateState();});
    list.appendChild(row);
  });
  updateGenerateState();
}
async function acceptFiles(fileList){
  const files=[...fileList].filter(f=>/^image\/(jpeg|png|webp)$/.test(f.type));
  if(!files.length)return;
  const available=Math.max(0,9-items.length);const selected=files.slice(0,available);
  if(!available){loadStatus.textContent='最大9枚です。';return;}
  loadStatus.textContent='写真を読み込んでいます…';
  for(const file of selected){try{const image=await loadImage(file);items.push({key:uid(),file,image,previewUrl:URL.createObjectURL(file),adjustments:{...defaults}});}catch(err){console.error(err);}}
  if(!mainKey&&items.length)mainKey=items[0].key;if(!activeKey&&items.length)activeKey=items[0].key;
  if(files.length>available)loadStatus.textContent=`最大9枚のため${available}枚だけ読み込みました。`;
  renderList();syncEditor();refreshCardPreview();
}
input.addEventListener('change',()=>{acceptFiles(input.files);input.value='';});
university.addEventListener('input',()=>{zipBlob=null;downloadButton.disabled=true;refreshCardPreview();updateGenerateState();});
rights.addEventListener('change',updateGenerateState);
Object.entries(controls).forEach(([key,el])=>el.addEventListener('input',()=>{const item=active();if(!item)return;item.adjustments[key]=Number(el.value);zipBlob=null;downloadButton.disabled=true;setOutputs(item);drawItem(item,canvas,ctx);if(item.key===mainKey)refreshCardPreview();}));
rotateLeft.addEventListener('click',()=>{const item=active();if(!item)return;item.adjustments.rotation=((Number(item.adjustments.rotation)||0)-90+360)%360;zipBlob=null;downloadButton.disabled=true;setOutputs(item);drawItem(item,canvas,ctx);if(item.key===mainKey)refreshCardPreview();});
rotateRight.addEventListener('click',()=>{const item=active();if(!item)return;item.adjustments.rotation=((Number(item.adjustments.rotation)||0)+90)%360;zipBlob=null;downloadButton.disabled=true;setOutputs(item);drawItem(item,canvas,ctx);if(item.key===mainKey)refreshCardPreview();});
reset.addEventListener('click',()=>{const item=active();if(!item)return;item.adjustments={...defaults};zipBlob=null;downloadButton.disabled=true;syncEditor();});

function crcTable(){const t=[];for(let n=0;n<256;n++){let c=n;for(let k=0;k<8;k++)c=(c&1)?0xedb88320^(c>>>1):c>>>1;t[n]=c>>>0;}return t;}const CRC=crcTable();
function crc32(bytes){let c=0xffffffff;for(const b of bytes)c=CRC[(c^b)&255]^(c>>>8);return (c^0xffffffff)>>>0;}
function le16(n){const b=new Uint8Array(2);new DataView(b.buffer).setUint16(0,n,true);return b;}function le32(n){const b=new Uint8Array(4);new DataView(b.buffer).setUint32(0,n>>>0,true);return b;}
function concat(parts){const len=parts.reduce((sum,p)=>sum+p.length,0),out=new Uint8Array(len);let offset=0;for(const part of parts){out.set(part,offset);offset+=part.length;}return out;}
async function makeZip(entries){const locals=[],centrals=[];let offset=0;for(const entry of entries){const name=enc.encode(entry.name),data=entry.data instanceof Uint8Array?entry.data:new Uint8Array(await entry.data.arrayBuffer()),crc=crc32(data);const local=concat([le32(0x04034b50),le16(20),le16(0),le16(0),le16(0),le16(0),le32(crc),le32(data.length),le32(data.length),le16(name.length),le16(0),name,data]);locals.push(local);const central=concat([le32(0x02014b50),le16(20),le16(20),le16(0),le16(0),le16(0),le16(0),le32(crc),le32(data.length),le32(data.length),le16(name.length),le16(0),le16(0),le16(0),le16(0),le32(0),le32(offset),name]);centrals.push(central);offset+=local.length;}const centralBytes=concat(centrals);const end=concat([le32(0x06054b50),le16(0),le16(0),le16(entries.length),le16(entries.length),le32(centralBytes.length),le32(offset),le16(0)]);return new Blob([concat([...locals,centralBytes,end])],{type:'application/zip'});}
function download(blob,name){const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);}

generate.addEventListener('click',async()=>{
  if(generate.disabled)return;
  generate.disabled=true;generate.textContent='生成中…';exportStatus.textContent='補正済み写真と審査情報を作成しています…';
  try{
    const ordered=[main(),...items.filter(x=>x.key!==mainKey)].filter(Boolean);
    const entries=[];const manifestPhotos=[];
    for(let index=0;index<ordered.length;index++){
      const item=ordered[index],out=document.createElement('canvas');out.width=720;out.height=405;drawItem(item,out,out.getContext('2d',{alpha:false}));
      const blob=await canvasBlob(out),sourceHash=await sha256(item.file),outputHash=await sha256(blob);
      const filename=`${String(index+1).padStart(2,'0')}-${index===0?'main':'sub'}.jpg`;
      entries.push({name:`photos/${filename}`,data:blob});
      manifestPhotos.push({role:index===0?'main':'sub',original_filename:item.file.name,output_filename:`photos/${filename}`,source_sha256:sourceHash,output_sha256:outputHash,adjustments:{...defaults,...item.adjustments}});
    }
    const manifest={
      schema_version:1,
      purpose:'Jotformで受信した大学実景写真の審査済み掲載パッケージ',
      source_type:'jotform_community_submission',
      university_name:university.value.trim(),
      submission_reference:submissionId.value.trim(),
      rights_status:'submitter_confirmed',
      rights_basis:'submission_agreement',
      rights_note:'投稿者が本人撮影または掲載許可済みであること、およびBan.Tai大学DBへの掲載に同意したことを管理者がJotformで確認済み。',
      scene_integrity:'scene_unchanged',
      ai_redraw:false,
      allowed_adjustments:['rotation_90','straighten_max_5deg','light_crop','brightness','contrast','resize'],
      forbidden_adjustments:['generative_redraw','object_add_remove','background_replace','scene_fabrication'],
      output_size:'720x405',
      main_photo:manifestPhotos[0]?.output_filename||'',
      photos:manifestPhotos,
      reviewed_at:new Date().toISOString(),
      next_action:'Attach this ZIP to ChatGPT for GitHub review, CI, PR and main merge. Do not write directly to main from this browser.'
    };
    entries.push({name:'manifest.json',data:enc.encode(JSON.stringify(manifest,null,2))});
    entries.push({name:'README.txt',data:enc.encode('Ban.Tai 大学写真 審査済み掲載パッケージ\n\nこのZIPは公開DBへ直接反映しません。ChatGPTへ添付し、大学ID照合・既存写真との整合・CI・PR確認後にmainへ反映してください。\n')});
    zipBlob=await makeZip(entries);downloadButton.disabled=false;exportStatus.textContent=`掲載用ZIPを生成しました（${ordered.length}枚・メイン1枚）。`;
  }catch(err){console.error(err);exportStatus.textContent=`生成に失敗しました: ${err.message||err}`;}
  finally{generate.textContent='掲載用ZIPを生成';updateGenerateState();}
});
downloadButton.addEventListener('click',()=>{if(!zipBlob)return;download(zipBlob,`bantai-university-photo-review-${safeName(university.value)}-${new Date().toISOString().slice(0,10)}.zip`);});

const params=new URLSearchParams(location.search);const preset=(params.get('university')||'').trim();if(preset)university.value=preset;updateGenerateState();
})();