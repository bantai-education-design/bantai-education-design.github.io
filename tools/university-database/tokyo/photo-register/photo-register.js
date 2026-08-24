(()=>{
'use strict';
const $=s=>document.querySelector(s);
const select=$('#university-select'),input=$('#photo-input'),drop=$('#drop-zone'),canvas=$('#preview'),ctx=canvas.getContext('2d',{alpha:false});
const empty=$('#empty-preview'),fileInfo=$('#file-info'),generate=$('#generate'),downloadJpeg=$('#download-jpeg'),downloadJson=$('#download-json'),copyJson=$('#copy-json');
const result=$('#result'),jsonOutput=$('#json-output');
const controls={zoom:$('#zoom'),x:$('#pos-x'),y:$('#pos-y'),brightness:$('#brightness'),contrast:$('#contrast')};
const outputs={zoom:$('#zoom-out'),x:$('#pos-x-out'),y:$('#pos-y-out'),brightness:$('#brightness-out'),contrast:$('#contrast-out')};
let universities=[],sourceFile=null,sourceImage=null,sourceHash='',jpegBlob=null,registration=null;

async function sha256(blob){const b=await blob.arrayBuffer();const h=await crypto.subtle.digest('SHA-256',b);return [...new Uint8Array(h)].map(x=>x.toString(16).padStart(2,'0')).join('');}
function safeName(name){return name.normalize('NFKC').replace(/[\\/:*?"<>|]/g,'-').replace(/\s+/g,'-').replace(/-+/g,'-').replace(/^-|-$/g,'').slice(0,50)||'university';}
function selectedUniversity(){return universities.find(x=>x.id===select.value)||null;}
function setOutputs(){outputs.zoom.value=`${controls.zoom.value}%`;outputs.x.value=controls.x.value;outputs.y.value=controls.y.value;outputs.brightness.value=`${controls.brightness.value}%`;outputs.contrast.value=`${controls.contrast.value}%`;}
function invalidate(){jpegBlob=null;registration=null;downloadJpeg.disabled=true;downloadJson.disabled=true;copyJson.disabled=true;result.hidden=true;}
function render(){setOutputs();invalidate();if(!sourceImage)return;const cw=canvas.width,ch=canvas.height,iw=sourceImage.naturalWidth||sourceImage.width,ih=sourceImage.naturalHeight||sourceImage.height;const cover=Math.max(cw/iw,ch/ih);const scale=cover*(Number(controls.zoom.value)/100);const dw=iw*scale,dh=ih*scale;const overflowX=Math.max(0,dw-cw),overflowY=Math.max(0,dh-ch);const dx=-overflowX*(Number(controls.x.value)/100),dy=-overflowY*(Number(controls.y.value)/100);ctx.save();ctx.fillStyle='#000';ctx.fillRect(0,0,cw,ch);ctx.filter=`brightness(${controls.brightness.value}%) contrast(${controls.contrast.value}%)`;ctx.drawImage(sourceImage,dx,dy,dw,dh);ctx.restore();empty.hidden=true;generate.disabled=!selectedUniversity();}
function loadImage(file){return new Promise((resolve,reject)=>{const url=URL.createObjectURL(file);const img=new Image();img.onload=()=>{URL.revokeObjectURL(url);resolve(img)};img.onerror=()=>{URL.revokeObjectURL(url);reject(new Error('画像を読み込めませんでした'))};img.src=url;});}
async function acceptFile(file){if(!file||!/^image\/(jpeg|png|webp)$/.test(file.type)){alert('JPEG / PNG / WebP を選択してください。');return;}sourceFile=file;fileInfo.textContent=`${file.name} ・ ${(file.size/1024/1024).toFixed(2)} MB ・ SHA-256計算中…`;try{[sourceImage,sourceHash]=await Promise.all([loadImage(file),sha256(file)]);fileInfo.textContent=`${file.name} ・ ${sourceImage.naturalWidth}×${sourceImage.naturalHeight} ・ SHA-256 ${sourceHash.slice(0,12)}…`;render();}catch(e){console.error(e);fileInfo.textContent='画像の読み込みに失敗しました';}}
function canvasBlob(){return new Promise((resolve,reject)=>canvas.toBlob(b=>b?resolve(b):reject(new Error('JPEG生成失敗')),'image/jpeg',0.9));}
function download(blob,name){const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);}
async function build(){const u=selectedUniversity();if(!u||!sourceImage||!sourceFile)return;jpegBlob=await canvasBlob();const outputHash=await sha256(jpegBlob);const filename=`${u.id}-${safeName(u.name)}-owner.jpg`;const imagePath=`assets/card-images/${filename}`;const now=new Date();const reviewed=now.toISOString().slice(0,10);const record={
  university_id:u.id,university_name:u.name,rights_status:'verified',rights_basis:'photographer_permission',
  image_url:imagePath,source_url:imagePath,source_label:'撮影者提供',creator:'Ban.Tai Education Design提供',
  license:'撮影者本人提供・本DB利用許諾',
  rights_note:'撮影者本人からBan.Tai東京都大学DBでの利用許諾を受けた実景写真。生成AIによる再描画・生成補完・背景置換・実景要素の追加削除は行わず、軽微なトリミングと明るさ・コントラスト調整のみを許可する。',
  alt:`${u.name}のキャンパス実景`,reviewed_at:reviewed,scene_integrity:'scene_unchanged',ai_redraw:false,
  allowed_adjustments:['brightness','contrast','crop','resize'],forbidden_adjustments:['generative_redraw','object_addition','object_removal','background_replacement','scene_composite'],
  source_file:{name:sourceFile.name,size_bytes:sourceFile.size,sha256:sourceHash},
  card_file:{name:filename,width:720,height:405,quality:0.9,sha256:outputHash},
  adjustment_values:{zoom:Number(controls.zoom.value),position_x:Number(controls.x.value),position_y:Number(controls.y.value),brightness:Number(controls.brightness.value),contrast:Number(controls.contrast.value)}
};
registration={schema_version:1,kind:'university_owner_photo_registration',generated_at:now.toISOString(),target_registry:'tools/university-database/tokyo/data/user-photo-overrides.json',target_image:`tools/university-database/tokyo/${imagePath}`,record};
jsonOutput.value=JSON.stringify(registration,null,2);$('#result-university').textContent=`${u.name}（${u.id}）`;$('#result-image-path').textContent=imagePath;result.hidden=false;downloadJpeg.disabled=false;downloadJson.disabled=false;copyJson.disabled=false;}

fetch('../data/universities_tokyo_all.generated.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error('大学一覧を取得できません');return r.json()}).then(rows=>{universities=rows;select.innerHTML='<option value="">大学を選択してください</option>'+rows.map(u=>`<option value="${u.id}">${u.name}（${u.id}）</option>`).join('');select.disabled=false;}).catch(e=>{console.error(e);select.innerHTML='<option>大学一覧の読み込みに失敗しました</option>';});

input.addEventListener('change',()=>acceptFile(input.files[0]));
['dragenter','dragover'].forEach(t=>drop.addEventListener(t,e=>{e.preventDefault();drop.classList.add('drag')}));
['dragleave','drop'].forEach(t=>drop.addEventListener(t,e=>{e.preventDefault();drop.classList.remove('drag')}));
drop.addEventListener('drop',e=>acceptFile(e.dataTransfer.files[0]));
Object.values(controls).forEach(el=>el.addEventListener('input',render));
select.addEventListener('change',()=>{invalidate();generate.disabled=!(sourceImage&&selectedUniversity())});
$('#reset-adjustments').addEventListener('click',()=>{controls.zoom.value=100;controls.x.value=50;controls.y.value=50;controls.brightness.value=100;controls.contrast.value=100;render()});
generate.addEventListener('click',()=>build().catch(e=>{console.error(e);alert('登録パッケージの生成に失敗しました。')}));
downloadJpeg.addEventListener('click',()=>{if(jpegBlob&&registration)download(jpegBlob,registration.record.card_file.name)});
downloadJson.addEventListener('click',()=>{if(registration){const blob=new Blob([JSON.stringify(registration,null,2)+'\n'],{type:'application/json'});download(blob,`${registration.record.university_id}-photo-registration.json`)}});
copyJson.addEventListener('click',async()=>{if(!registration)return;await navigator.clipboard.writeText(JSON.stringify(registration,null,2));const old=copyJson.textContent;copyJson.textContent='コピーしました';setTimeout(()=>copyJson.textContent=old,1200)});
setOutputs();
})();
