// Supabase Edge Function template: university-photo-submission
// Secrets: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, RESEND_API_KEY,
// REVIEW_NOTIFICATION_EMAIL, REVIEW_FROM_EMAIL, REVIEW_DASHBOARD_URL.
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const allowedOrigins=new Set([
  'https://bantai-education-design.github.io',
  'http://127.0.0.1:4173',
  'http://localhost:4173'
]);
const cors=(origin:string)=>({
  'access-control-allow-origin':allowedOrigins.has(origin)?origin:'https://bantai-education-design.github.io',
  'access-control-allow-methods':'POST,OPTIONS',
  'access-control-allow-headers':'content-type',
  'vary':'Origin'
});
const json=(body:unknown,status=200,origin='')=>new Response(JSON.stringify(body),{status,headers:{'content-type':'application/json; charset=utf-8',...cors(origin)}});
const decoder=new TextDecoder();

function readStoredZip(bytes:Uint8Array){
  const entries=new Map<string,Uint8Array>();
  const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
  let offset=0;
  while(offset+30<=bytes.length){
    const signature=view.getUint32(offset,true);
    if(signature!==0x04034b50)break;
    const flags=view.getUint16(offset+6,true);
    const method=view.getUint16(offset+8,true);
    const compressed=view.getUint32(offset+18,true);
    const uncompressed=view.getUint32(offset+22,true);
    const nameLength=view.getUint16(offset+26,true);
    const extraLength=view.getUint16(offset+28,true);
    if(flags&0x08)throw new Error('ZIP data descriptor is not supported');
    if(method!==0||compressed!==uncompressed)throw new Error('ZIP compression is not supported');
    const nameStart=offset+30;
    const dataStart=nameStart+nameLength+extraLength;
    const dataEnd=dataStart+compressed;
    if(dataEnd>bytes.length)throw new Error('Invalid ZIP entry');
    const name=decoder.decode(bytes.slice(nameStart,nameStart+nameLength));
    if(name.includes('..')||name.startsWith('/')||name.includes('\\'))throw new Error('Unsafe ZIP path');
    entries.set(name,bytes.slice(dataStart,dataEnd));
    if(entries.size>12)throw new Error('Too many ZIP entries');
    offset=dataEnd;
  }
  return entries;
}
function imageType(name:string,data:Uint8Array){
  const lower=name.toLowerCase();
  if(/\.jpe?g$/.test(lower)&&data.length>=3&&data[0]===0xff&&data[1]===0xd8&&data[2]===0xff)return'image/jpeg';
  if(/\.png$/.test(lower)&&data.length>=8&&data[0]===0x89&&data[1]===0x50&&data[2]===0x4e&&data[3]===0x47)return'image/png';
  if(/\.webp$/.test(lower)&&data.length>=12&&decoder.decode(data.slice(0,4))==='RIFF'&&decoder.decode(data.slice(8,12))==='WEBP')return'image/webp';
  return'';
}

Deno.serve(async req=>{
  const origin=req.headers.get('origin')||'';
  if(req.method==='OPTIONS')return new Response(null,{status:204,headers:cors(origin)});
  if(req.method!=='POST')return json({ok:false,message:'POST only'},405,origin);
  if(!allowedOrigins.has(origin))return json({ok:false,message:'Origin not allowed'},403,origin);

  const uploadedPaths:string[]=[];
  let supabase:any=null;
  try{
    const form=await req.formData();
    const metadataPart=form.get('metadata');
    const packagePart=form.get('package');
    if(!(metadataPart instanceof File)||!(packagePart instanceof File))return json({ok:false,message:'metadata/package required'},400,origin);
    if(packagePart.size<=0||packagePart.size>80*1024*1024)return json({ok:false,message:'package too large'},413,origin);

    const metadata=JSON.parse(await metadataPart.text());
    if(metadata?.kind!=='bantai_university_photo_submission'||metadata?.review_status!=='pending')return json({ok:false,message:'invalid submission'},400,origin);
    if(!/^u\d{6}$/.test(metadata?.university_id||''))return json({ok:false,message:'invalid university id'},400,origin);
    if(!Number.isInteger(metadata?.photo_count)||metadata.photo_count<1||metadata.photo_count>9)return json({ok:false,message:'photo count must be 1..9'},400,origin);
    if(!Array.isArray(metadata?.photos)||metadata.photos.length!==metadata.photo_count)return json({ok:false,message:'photo metadata mismatch'},400,origin);
    if(metadata.photos.filter((p:any)=>p?.role==='main').length!==1)return json({ok:false,message:'one main photo required'},400,origin);
    const agreements=metadata?.agreements||{};
    if(!(agreements.rights&&agreements.no_ai&&agreements.license))return json({ok:false,message:'agreements required'},400,origin);

    const serverId=`BT-UP-${new Date().toISOString().replace(/\D/g,'').slice(0,14)}-${crypto.randomUUID().slice(0,6).toUpperCase()}`;
    supabase=createClient(Deno.env.get('SUPABASE_URL')!,Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!,{auth:{persistSession:false}});
    const zipBytes=new Uint8Array(await packagePart.arrayBuffer());
    const zipEntries=readStoredZip(zipBytes);
    const normalizedPhotos:any[]=[];

    for(const photo of metadata.photos){
      const role=photo?.role==='main'?'main':'sub';
      if(photo?.kind==='existing'){
        const imageUrl=String(photo?.image_url||'');
        if(!imageUrl||imageUrl.length>1500)return json({ok:false,message:'invalid existing photo'},400,origin);
        normalizedPhotos.push({kind:'existing',role,image_url:imageUrl,origin:String(photo?.origin||'existing').slice(0,80)});
        continue;
      }
      if(photo?.kind!=='new')return json({ok:false,message:'invalid photo kind'},400,origin);
      const filename=String(photo?.filename||'');
      if(!/^photos\/[A-Za-z0-9._()\-ぁ-んァ-ヶ一-龠々ー]+\.(?:jpe?g|png|webp)$/i.test(filename))return json({ok:false,message:'invalid photo filename'},400,origin);
      const bytes=zipEntries.get(filename);
      if(!bytes||bytes.length<=0||bytes.length>20*1024*1024)return json({ok:false,message:'photo file missing or too large'},400,origin);
      const contentType=imageType(filename,bytes);
      if(!contentType)return json({ok:false,message:'invalid photo format'},400,origin);
      const path=`${serverId}/${filename}`;
      const upload=await supabase.storage.from('university-photo-submissions').upload(path,bytes,{contentType,upsert:false});
      if(upload.error)throw upload.error;
      uploadedPaths.push(path);
      normalizedPhotos.push({
        kind:'new',role,path,
        original_name:String(photo?.original_name||'').slice(0,240),
        source_filename:filename
      });
    }

    const packagePath=`${serverId}/submission.zip`;
    const packageUpload=await supabase.storage.from('university-photo-submissions').upload(packagePath,zipBytes,{contentType:'application/zip',upsert:false});
    if(packageUpload.error)throw packageUpload.error;
    uploadedPaths.push(packagePath);

    const mainPhoto=normalizedPhotos.find((p:any)=>p.role==='main')||null;
    const row={
      submission_id:serverId,
      university_id:metadata.university_id,
      university_name:String(metadata.university_name||'').slice(0,200),
      submitted_at:new Date().toISOString(),
      photo_count:metadata.photo_count,
      main_photo:mainPhoto,
      photos:normalizedPhotos,
      agreements,
      status:'pending',
      package_path:packagePath,
      client_submission_id:metadata.submission_id||null
    };
    const inserted=await supabase.from('photo_submissions').insert(row);
    if(inserted.error)throw inserted.error;

    let notified=false;
    const apiKey=Deno.env.get('RESEND_API_KEY');
    const to=Deno.env.get('REVIEW_NOTIFICATION_EMAIL');
    const from=Deno.env.get('REVIEW_FROM_EMAIL');
    if(apiKey&&to&&from){
      const reviewBase=Deno.env.get('REVIEW_DASHBOARD_URL')||'';
      const reviewUrl=reviewBase?`${reviewBase}${reviewBase.includes('?')?'&':'?'}submission=${encodeURIComponent(serverId)}`:'';
      const mail=await fetch('https://api.resend.com/emails',{
        method:'POST',
        headers:{authorization:`Bearer ${apiKey}`,'content-type':'application/json'},
        body:JSON.stringify({
          from,
          to:[to],
          subject:`[大学写真投稿] ${row.university_name} / ${row.photo_count}枚 / ${serverId}`,
          text:[
            '大学写真の新しい投稿があります。',
            `大学: ${row.university_name}`,
            `写真: ${row.photo_count}枚`,
            `受付番号: ${serverId}`,
            `投稿日時: ${row.submitted_at}`,
            reviewUrl?`審査: ${reviewUrl}`:''
          ].filter(Boolean).join('\n')
        })
      });
      notified=mail.ok;
    }

    return json({ok:true,submission_id:serverId,notified,review_status:'pending'},200,origin);
  }catch(err){
    console.error(err);
    if(supabase&&uploadedPaths.length){
      try{await supabase.storage.from('university-photo-submissions').remove(uploadedPaths);}catch(cleanupError){console.error('cleanup failed',cleanupError);}
    }
    return json({ok:false,message:'投稿を受け付けられませんでした。'},500,origin);
  }
});
