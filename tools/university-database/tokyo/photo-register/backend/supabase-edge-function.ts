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

Deno.serve(async req=>{
  const origin=req.headers.get('origin')||'';
  if(req.method==='OPTIONS')return new Response(null,{status:204,headers:cors(origin)});
  if(req.method!=='POST')return json({ok:false,message:'POST only'},405,origin);
  if(!allowedOrigins.has(origin))return json({ok:false,message:'Origin not allowed'},403,origin);

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
    const agreements=metadata?.agreements||{};
    if(!(agreements.rights&&agreements.no_ai&&agreements.license))return json({ok:false,message:'agreements required'},400,origin);

    const serverId=`BT-UP-${new Date().toISOString().replace(/\D/g,'').slice(0,14)}-${crypto.randomUUID().slice(0,6).toUpperCase()}`;
    const supabase=createClient(Deno.env.get('SUPABASE_URL')!,Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!,{auth:{persistSession:false}});
    const path=`${serverId}/submission.zip`;
    const upload=await supabase.storage.from('university-photo-submissions').upload(path,packagePart,{contentType:'application/zip',upsert:false});
    if(upload.error)throw upload.error;

    const row={
      submission_id:serverId,
      university_id:metadata.university_id,
      university_name:String(metadata.university_name||'').slice(0,200),
      submitted_at:new Date().toISOString(),
      photo_count:metadata.photo_count,
      main_photo:metadata.photos?.find((p:any)=>p?.role==='main')||null,
      agreements,
      status:'pending',
      package_path:path,
      client_submission_id:metadata.submission_id||null
    };
    const inserted=await supabase.from('photo_submissions').insert(row);
    if(inserted.error){await supabase.storage.from('university-photo-submissions').remove([path]);throw inserted.error;}

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
    return json({ok:false,message:'投稿を受け付けられませんでした。'},500,origin);
  }
});
