(()=>{
'use strict';
const $=s=>document.querySelector(s);
const input=$('#photo-input'),drop=$('#drop-zone'),list=$('#batch-list'),count=$('#batch-count'),status=$('#batch-status');
const select=$('#university-select'),canvas=$('#preview'),ctx=canvas.getContext('2d',{alpha:false}),empty=$('#empty-preview'),fileInfo=$('#file-info'),editor=$('#photo-editor');
const generate=$('#generate-batch'),downloadZip=$('#download-zip'),downloadJson=$('#download-json'),copyJson=$('#copy-json'),result=$('#result'),jsonOutput=$('#json-output');
const rotateLeft=$('#rotate-left'),rotateRight=$('#rotate-right'),rotationOut=$('#rotation-out');
const controls={tilt:$('#tilt'),zoom:$('#zoom'),x:$('#pos-x'),y:$('#pos-y'),brightness:$('#brightness'),contrast:$('#contrast')};
const outputs={tilt:$('#tilt-out'),zoom:$('#zoom-out'),x:$('#pos-x-out'),y:$('#pos-y-out'),brightness:$('#brightness-out'),contrast:$('#contrast-out')};
const defaults={rotation:0,tilt:0,zoom:100,x:50,y:50,brightness:100,contrast:100};
const MAX_SOURCE_FILE_BYTES=2*1024*1024;
let universities=[],baseRegistry={schema_version:1,purpose:'撮影者本人から提供された大学実景写真を、既存の公開画像台帳へ安全に上書きする。',records:{}},items=[],activeId=null,zipBlob=null,mergedRegistry=null;

const enc=new TextEncoder();
async function sha256(blob){const b=await blob.arrayBuffer();const h=await crypto.subtle.digest('SHA-256',b);return [...new Uint8Array(h)].map(x=>x.toString(16).padStart(2,'0')).join('');}
function safeName(name){return name.normalize('NFKC').replace(/[\\/:*?"<>|]/g,'-').replace(/\s+/g,'-').replace(/-+/g,'-').replace(/^-|-$/g,'').slice(0,50)||'university';}
function norm(s){return String(s||'').normalize('NFKC').toLowerCase().replace(/[\s　_\-()（）.・]/g,'');}
function uid(){return crypto.randomUUID?crypto.randomUUID():`${Date.now()}-${Math.random()}`;}
function active(){return items.find(x=>x.key===activeId)||null;}
function universityById(id){return universities.find(u=>u.id===id)||null;}
function universityLabel(id){const u=universityById(id);return u?`${u.name}（${u.id}）`:'';}
function optionMarkup(rows,selected){return '<option value="">大学を選択</option>'+rows.map(u=>`<option value="${u.id}" ${u.id===selected?'selected':''}>${u.name}（${u.id}）</option>`).join('');}
function options(selected){return optionMarkup(universities,selected);}
function matchingUniversities(query){const n=norm(query);if(!n)return universities;return universities.filter(u=>norm(u.id).includes(n)||norm(u.name).includes(n)||norm(`${u.name}${u.id}`).includes(n));}
function resolveUniversity(query){const n=norm(query);if(!n)return null;const exact=universities.find(u=>norm(u.id)===n||norm(u.name)===n||norm(`${u.name}（${u.id}）`)===n);if(exact)return exact;const matches=matchingUniversities(query);return matches.length===1?matches[0]:null;}
function setOutputs(){const item=active(),a=item?.adjustments||defaults;outputs.tilt.value=`${Number(a.tilt||0).toFixed(1)}°`;outputs.zoom.value=`${controls.zoom.value}%`;outputs.x.value=controls.x.value;outputs.y.value=controls.y.value;outputs.brightness.value=`${controls.brightness.value}%`;outputs.contrast.value=`${controls.contrast.value}%`;rotationOut.value=`${Number(a.rotation||0)}°`;rotationOut.textContent=`${Number(a.rotation||0)}°`;}
function loadImage(file){return new Promise((resolve,reject)=>{const url=URL.createObjectURL(file);const img=new Image();img.onload=()=>{URL.revokeObjectURL(url);resolve(img)};img.onerror=()=>{URL.revokeObjectURL(url);reject(new Error('画像を読み込めませんでした'))};img.src=url;});}
function autoUniversity(file){const n=norm(file.name);return universities.find(u=>n.includes(norm(u.id))||n.includes(norm(u.name)))||null;}
function invalidateOutput(){zipBlob=null;mergedRegistry=null;downloadZip.disabled=true;downloadJson.disabled=true;copyJson.disabled=true;result.hidden=true;}
function syncGenerateState(){const assigned=items.filter(x=>x.universityId).length;const unique=new Set(items.filter(x=>x.universityId).map(x=>x.universityId)).size;const duplicates=assigned!==unique;generate.disabled=!items.length||assigned!==items.length||duplicates;count.textContent=`${items.length}枚`;status.textContent=!items.length?'写真未選択':duplicates?'同じ大学が重複しています':assigned===items.length?`${assigned}枚すべて割当済み`:`${assigned}/${items.length}枚を割当済み`;status.classList.toggle('warn',duplicates||assigned!==items.length);}
function refreshRowSelect(selectEl,query,selectedId){const matches=matchingUniversities(query);selectEl.innerHTML=optionMarkup(matches,selectedId);if(selectedId&&matches.some(u=>u.id===selectedId))selectEl.value=selectedId;}
function assignUniversity(item,id,searchEl,selectEl){item.universityId=id||'';if(searchEl)searchEl.value=universityLabel(item.universityId);if(selectEl){selectEl.innerHTML=options(item.universityId);selectEl.value=item.universityId;}invalidateOutput();if(item.key===activeId)syncEditor();syncGenerateState();}
function renderList(){
  list.innerHTML='';
  for(const item of items){
    const row=document.createElement('div');
    row.className='batch-row'+(item.key===activeId?' active':'');
    row.dataset.key=item.key;
    row.innerHTML=`<div class="thumb"><img src="${item.previewUrl}" alt=""></div><div class="batch-main"><strong>${item.file.name}</strong><small>${item.image.naturalWidth}×${item.image.naturalHeight} ・ SHA ${item.sourceHash.slice(0,10)}…</small><div class="university-assign"><input class="row-university-search" type="text" autocomplete="off" placeholder="大学名・大学IDを入力して検索" aria-label="大学名または大学IDを入力"><select class="row-university" aria-label="大学候補から選択"></select><span class="assign-help">文字入力で候補を絞るか、下の一覧から選択できます。</span></div></div><div class="batch-actions"><button type="button" class="edit-item">編集</button><button type="button" class="remove-item">削除</button></div>`;
    const searchEl=row.querySelector('.row-university-search'),selectEl=row.querySelector('.row-university');
    searchEl.value=universityLabel(item.universityId);
    selectEl.innerHTML=options(item.universityId);
    selectEl.value=item.universityId;
    searchEl.addEventListener('input',()=>{
      refreshRowSelect(selectEl,searchEl.value,item.universityId);
      const exact=universities.find(u=>norm(u.id)===norm(searchEl.value)||norm(u.name)===norm(searchEl.value)||norm(`${u.name}（${u.id}）`)===norm(searchEl.value));
      if(exact&&exact.id!==item.universityId){item.universityId=exact.id;selectEl.value=exact.id;invalidateOutput();if(item.key===activeId)syncEditor();syncGenerateState();}
    });
    const commitSearch=()=>{const match=resolveUniversity(searchEl.value);if(match)assignUniversity(item,match.id,searchEl,selectEl);};
    searchEl.addEventListener('change',commitSearch);
    searchEl.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();commitSearch();}});
    selectEl.addEventListener('change',()=>assignUniversity(item,selectEl.value,searchEl,selectEl));
    row.querySelector('.edit-item').addEventListener('click',()=>{
      activeId=item.key;
      syncEditor();
      renderList();
      requestAnimationFrame(()=>{editor?.focus({preventScroll:true});editor?.scrollIntoView({behavior:'smooth',block:'start'});});
    });
    row.querySelector('.remove-item').addEventListener('click',()=>removeItem(item.key));
    list.appendChild(row);
  }
  syncGenerateState();
}
function removeItem(key){const i=items.findIndex(x=>x.key===key);if(i<0)return;URL.revokeObjectURL(items[i].previewUrl);items.splice(i,1);if(activeId===key)activeId=items[0]?.key||null;invalidateOutput();syncEditor();renderList();}
function syncEditor(){
  const item=active();
  if(!item){select.disabled=true;select.innerHTML='<option>写真を選択してください</option>';fileInfo.textContent='編集対象なし';empty.hidden=false;ctx.clearRect(0,0,canvas.width,canvas.height);rotateLeft.disabled=true;rotateRight.disabled=true;setOutputs();return;}
  item.adjustments={...defaults,...item.adjustments};
  select.disabled=false;select.innerHTML=options(item.universityId);select.value=item.universityId;fileInfo.textContent=`${item.file.name} ・ ${item.image.naturalWidth}×${item.image.naturalHeight}`;
  for(const [k,el] of Object.entries(controls))el.value=item.adjustments[k]??defaults[k];
  rotateLeft.disabled=false;rotateRight.disabled=false;
  drawItem(item,canvas,ctx);
}
function drawItem(item,target,targetCtx){
  const cw=target.width,ch=target.height,iw=item.image.naturalWidth||item.image.width,ih=item.image.naturalHeight||item.image.height,a={...defaults,...item.adjustments};
  const rotation=((Number(a.rotation)||0)%360+360)%360,tilt=Number(a.tilt)||0,tiltRad=tilt*Math.PI/180;
  const quarter=rotation===90||rotation===270,rw=quarter?ih:iw,rh=quarter?iw:ih;
  const c=Math.abs(Math.cos(tiltRad)),s=Math.abs(Math.sin(tiltRad));
  const requiredW=(cw*c+ch*s)/rw,requiredH=(cw*s+ch*c)/rh;
  const cover=Math.max(requiredW,requiredH),scale=cover*(Number(a.zoom)/100);
  const effectiveW=rw*scale,effectiveH=rh*scale;
  const overflowX=Math.max(0,effectiveW-cw),overflowY=Math.max(0,effectiveH-ch);
  const shiftX=((50-Number(a.x))/50)*(overflowX/2),shiftY=((50-Number(a.y))/50)*(overflowY/2);
  targetCtx.save();
  targetCtx.fillStyle='#000';targetCtx.fillRect(0,0,cw,ch);
  targetCtx.translate(cw/2+shiftX,ch/2+shiftY);
  targetCtx.rotate((rotation+tilt)*Math.PI/180);
  targetCtx.filter=`brightness(${a.brightness}%) contrast(${a.contrast}%)`;
  targetCtx.drawImage(item.image,-iw*scale/2,-ih*scale/2,iw*scale,ih*scale);
  targetCtx.restore();
  if(target===canvas){empty.hidden=true;setOutputs();}
}
function canvasBlob(c){return new Promise((resolve,reject)=>c.toBlob(b=>b?resolve(b):reject(new Error('JPEG生成失敗')),'image/jpeg',0.9));}
async function acceptFiles(fileList){const selected=[...fileList],files=selected.filter(f=>/^image\/(jpeg|png|webp)$/.test(f.type)&&f.size>0&&f.size<=MAX_SOURCE_FILE_BYTES);if(!files.length){status.textContent='JPEG・PNG・WebP形式で、1枚2MB以下の写真を選択してください。';status.classList.add('warn');return;}if(files.length!==selected.length){status.textContent='JPEG・PNG・WebP形式、1枚2MB以下の写真だけを追加しました。';status.classList.add('warn');}else{status.textContent='読み込み中…';status.classList.remove('warn');}const loaded=await Promise.all(files.map(async file=>{try{const [image,sourceHash]=await Promise.all([loadImage(file),sha256(file)]);const match=autoUniversity(file);return {key:uid(),file,image,sourceHash,previewUrl:URL.createObjectURL(file),universityId:match?.id||'',adjustments:{...defaults}};}catch(e){console.error(e);return null;}}));items.push(...loaded.filter(Boolean));if(!activeId&&items.length)activeId=items[0].key;invalidateOutput();syncEditor();renderList();}

function crcTable(){const t=[];for(let n=0;n<256;n++){let c=n;for(let k=0;k<8;k++)c=(c&1)?0xedb88320^(c>>>1):c>>>1;t[n]=c>>>0;}return t;}const CRC=crcTable();
function crc32(bytes){let c=0xffffffff;for(const b of bytes)c=CRC[(c^b)&255]^(c>>>8);return (c^0xffffffff)>>>0;}
function le16(n){const b=new Uint8Array(2);new DataView(b.buffer).setUint16(0,n,true);return b;}function le32(n){const b=new Uint8Array(4);new DataView(b.buffer).setUint32(0,n>>>0,true);return b;}
function concat(parts){const len=parts.reduce((s,p)=>s+p.length,0),out=new Uint8Array(len);let o=0;for(const p of parts){out.set(p,o);o+=p.length;}return out;}
async function makeZip(entries){const locals=[],centrals=[];let offset=0;for(const entry of entries){const name=enc.encode(entry.name),data=entry.data instanceof Uint8Array?entry.data:new Uint8Array(await entry.data.arrayBuffer()),crc=crc32(data);const local=concat([le32(0x04034b50),le16(20),le16(0),le16(0),le16(0),le16(0),le32(crc),le32(data.length),le32(data.length),le16(name.length),le16(0),name,data]);locals.push(local);const central=concat([le32(0x02014b50),le16(20),le16(20),le16(0),le16(0),le16(0),le16(0),le32(crc),le32(data.length),le32(data.length),le16(name.length),le16(0),le16(0),le16(0),le16(0),le32(0),le32(offset),name]);centrals.push(central);offset+=local.length;}const centralBytes=concat(centrals);const end=concat([le32(0x06054b50),le16(0),le16(0),le16(entries.length),le16(entries.length),le32(centralBytes.length),le32(offset),le16(0)]);return new Blob([concat([...locals,centralBytes,end])],{type:'application/zip'});}
function download(blob,name){const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);}
async function generateBatch(){
  invalidateOutput();const ids=items.map(x=>x.universityId);if(!items.length||ids.some(x=>!x)||new Set(ids).size!==ids.length)return;generate.disabled=true;generate.textContent='生成中…';
  try{
    const newRecords={},zipEntries=[],manifestItems=[];
    for(const item of items){
      const u=universityById(item.universityId),out=document.createElement('canvas');out.width=720;out.height=405;drawItem(item,out,out.getContext('2d',{alpha:false}));
      const jpeg=await canvasBlob(out),outputHash=await sha256(jpeg);const filename=`${u.id}-${safeName(u.name)}-owner.jpg`,relative=`assets/card-images/${filename}`,a={...defaults,...item.adjustments};
      const record={university_id:u.id,university_name:u.name,rights_status:'verified',rights_basis:'photographer_permission',image_url:relative,source_url:relative,source_label:'撮影者提供',creator:'Ban.Tai Education Design提供',license:'撮影者本人提供・本DB利用許諾',rights_note:'撮影者本人からBan.Tai東京都大学DBでの利用許諾を受けた実景写真。生成AIによる再描画・生成補完・背景置換・実景要素の追加削除は行わず、90度単位の回転、±5度以内の傾き補正、軽微なトリミングと明るさ・コントラスト調整のみを許可する。',alt:`${u.name}のキャンパス実景`,reviewed_at:new Date().toISOString().slice(0,10),scene_integrity:'scene_unchanged',ai_redraw:false,surfaces:['card','detail'],allowed_adjustments:['rotation','straighten','brightness','contrast','crop','resize'],forbidden_adjustments:['generative_redraw','object_addition','object_removal','background_replacement','scene_composite'],source_file:{name:item.file.name,size_bytes:item.file.size,sha256:item.sourceHash},card_file:{name:filename,width:720,height:405,quality:0.9,sha256:outputHash},adjustment_values:{rotation_degrees:Number(a.rotation),tilt_degrees:Number(a.tilt),zoom:Number(a.zoom),position_x:Number(a.x),position_y:Number(a.y),brightness:Number(a.brightness),contrast:Number(a.contrast)}};
      newRecords[u.id]=record;zipEntries.push({name:`tools/university-database/tokyo/${relative}`,data:jpeg});zipEntries.push({name:`source-originals/${u.id}-${safeName(u.name)}-${safeName(item.file.name)}`,data:item.file});manifestItems.push({university_id:u.id,university_name:u.name,public_image_path:`tools/university-database/tokyo/${relative}`,source_original:`source-originals/${u.id}-${safeName(u.name)}-${safeName(item.file.name)}`,source_sha256:item.sourceHash,output_sha256:outputHash,surfaces:['card','detail'],rotation_degrees:Number(a.rotation),tilt_degrees:Number(a.tilt)});
    }
    mergedRegistry={...baseRegistry,schema_version:Math.max(1,Number(baseRegistry.schema_version)||1),purpose:baseRegistry.purpose||'撮影者本人から提供された大学実景写真を、既存の公開画像台帳へ安全に上書きする。',records:{...(baseRegistry.records||{}),...newRecords}};
    const manifest={schema_version:1,kind:'university_owner_photo_batch',generated_at:new Date().toISOString(),scene_policy:'scene_unchanged',ai_redraw:false,target_registry:'tools/university-database/tokyo/data/user-photo-overrides.json',surfaces:['card','detail'],items:manifestItems};
    const registryBytes=enc.encode(JSON.stringify(mergedRegistry,null,2)+'\n'),manifestBytes=enc.encode(JSON.stringify(manifest,null,2)+'\n');zipEntries.push({name:'tools/university-database/tokyo/data/user-photo-overrides.json',data:registryBytes});zipEntries.push({name:'photo-batch-manifest.json',data:manifestBytes});zipBlob=await makeZip(zipEntries);jsonOutput.value=JSON.stringify(mergedRegistry,null,2);$('#result-university').textContent=`${items.length}校：${items.map(i=>universityById(i.universityId)?.name).join('、')}`;result.hidden=false;downloadZip.disabled=false;downloadJson.disabled=false;copyJson.disabled=false;
  }finally{generate.disabled=false;generate.textContent='一括ZIPを生成';}
}

Promise.all([fetch('../data/universities_tokyo_all.generated.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error('大学一覧を取得できません');return r.json()}),fetch('../data/user-photo-overrides.json',{cache:'no-store'}).then(r=>r.ok?r.json():baseRegistry).catch(()=>baseRegistry)]).then(([rows,registry])=>{universities=rows;baseRegistry=registry||baseRegistry;select.innerHTML=options('');syncGenerateState();}).catch(e=>{console.error(e);status.textContent='大学一覧の読み込みに失敗しました';});

input.addEventListener('change',()=>acceptFiles(input.files));['dragenter','dragover'].forEach(t=>drop.addEventListener(t,e=>{e.preventDefault();drop.classList.add('drag')}));['dragleave','drop'].forEach(t=>drop.addEventListener(t,e=>{e.preventDefault();drop.classList.remove('drag')}));drop.addEventListener('drop',e=>acceptFiles(e.dataTransfer.files));
Object.entries(controls).forEach(([k,el])=>el.addEventListener('input',()=>{const item=active();if(!item)return;item.adjustments[k]=Number(el.value);invalidateOutput();drawItem(item,canvas,ctx);}));
function rotateBy(delta){const item=active();if(!item)return;item.adjustments.rotation=((Number(item.adjustments.rotation)||0)+delta+360)%360;invalidateOutput();drawItem(item,canvas,ctx);}
rotateLeft.addEventListener('click',()=>rotateBy(-90));rotateRight.addEventListener('click',()=>rotateBy(90));
select.addEventListener('change',()=>{const item=active();if(!item)return;item.universityId=select.value;invalidateOutput();renderList();});
$('#reset-adjustments').addEventListener('click',()=>{const item=active();if(!item)return;item.adjustments={...defaults};syncEditor();invalidateOutput();});
$('#clear-batch').addEventListener('click',()=>{for(const i of items)URL.revokeObjectURL(i.previewUrl);items=[];activeId=null;invalidateOutput();syncEditor();renderList();input.value='';});
generate.addEventListener('click',()=>generateBatch().catch(e=>{console.error(e);alert('一括登録パッケージの生成に失敗しました。')}));
downloadZip.addEventListener('click',()=>{if(zipBlob)download(zipBlob,`university-photo-batch-${new Date().toISOString().slice(0,10)}.zip`)});downloadJson.addEventListener('click',()=>{if(mergedRegistry)download(new Blob([JSON.stringify(mergedRegistry,null,2)+'\n'],{type:'application/json'}),'user-photo-overrides.json')});copyJson.addEventListener('click',async()=>{if(!mergedRegistry)return;await navigator.clipboard.writeText(JSON.stringify(mergedRegistry,null,2));const old=copyJson.textContent;copyJson.textContent='コピーしました';setTimeout(()=>copyJson.textContent=old,1200)});
setOutputs();syncEditor();syncGenerateState();
})();
