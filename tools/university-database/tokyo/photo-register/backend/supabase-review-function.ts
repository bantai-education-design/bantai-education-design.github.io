// Supabase Edge Function template: university-photo-review
// Secrets: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, REVIEW_ADMIN_CODE.
// REVIEW_ADMIN_CODE is never stored in GitHub or returned to the browser.
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const allowedOrigins=new Set([
  'https://bantai-education-design.github.io',
  'http://127.0.0.1:4173',
  'http://localhost:4173'
]);
const cors=(origin:string)=>({
  'access-control-allow-origin':allowedOrigins.has(origin)?origin:'https://bantai-education-design.github.io',
  'access-control-allow-methods':'POST,OPTIONS',
  'access-control-allow-headers':'content-type,x-bantai-admin-code',
  'cache-control':'no-store',
  'vary':'Origin'
});
const json=(body:unknown,status=200,origin='')=>new Response(JSON.stringify(body),{status,headers:{'content-type':'application/json; charset=utf-8',...cors(origin)}});
const encoder=new TextEncoder();
function safeEqual(a:string,b:string){
  const left=encoder.encode(a),right=encoder.encode(b);
  let diff=left.length^right.length;
  const size=Math.max(left.length,right.length);
  for(let i=0;i<size;i++)diff|=(left[i]||0)^(right[i]||0);
  return diff===0;
}

Deno.serve(async req=>{
  const origin=req.headers.get('origin')||'';
  if(req.method==='OPTIONS')return new Response(null,{status:204,headers:cors(origin)});
  if(req.method!=='POST')return json({ok:false,message:'POST only'},405,origin);
  if(!allowedOrigins.has(origin))return json({ok:false,message:'Origin not allowed'},403,origin);

  const expected=Deno.env.get('REVIEW_ADMIN_CODE')||'';
  if(expected.length<12)return json({ok:false,message:'Review admin is not configured'},503,origin);
  const supplied=req.headers.get('x-bantai-admin-code')||'';
  if(!safeEqual(supplied,expected))return json({ok:false,message:'管理コードが違います。'},401,origin);

  try{
    const body=await req.json().catch(()=>({}));
    const action=String(body?.action||'');
    const supabase=createClient(Deno.env.get('SUPABASE_URL')!,Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!,{auth:{persistSession:false}});

    if(action==='health')return json({ok:true,review_admin:true},200,origin);

    if(action==='list'){
      const allowedStatus=new Set(['all','pending','approved','rejected','published']);
      const status=allowedStatus.has(body?.status)?body.status:'pending';
      const limit=Math.min(Math.max(Number(body?.limit)||50,1),100);
      let query=supabase.from('photo_submissions')
        .select('submission_id,client_submission_id,university_id,university_name,submitted_at,photo_count,main_photo,photos,agreements,status,package_path,reviewer_note,reviewed_at')
        .order('submitted_at',{ascending:false})
        .limit(limit);
      if(status!=='all')query=query.eq('status',status);
      const result=await query;
      if(result.error)throw result.error;
      const rows=result.data||[];
      const paths:string[]=[];
      for(const row of rows){
        if(row.package_path)paths.push(row.package_path);
        for(const photo of Array.isArray(row.photos)?row.photos:[])if(photo?.path)paths.push(photo.path);
      }
      const unique=[...new Set(paths)];
      const signed=new Map<string,string>();
      if(unique.length){
        const signedResult=await supabase.storage.from('university-photo-submissions').createSignedUrls(unique,20*60);
        if(signedResult.error)throw signedResult.error;
        for(const item of signedResult.data||[])if(item?.path&&item?.signedUrl)signed.set(item.path,item.signedUrl);
      }
      const submissions=rows.map(row=>({
        ...row,
        package_url:row.package_path?signed.get(row.package_path)||'':'',
        photos:(Array.isArray(row.photos)?row.photos:[]).map((photo:any)=>({
          ...photo,
          url:photo?.path?signed.get(photo.path)||'':photo?.image_url||''
        }))
      }));
      return json({ok:true,submissions},200,origin);
    }

    if(action==='update'){
      const id=String(body?.submission_id||'');
      if(!/^BT-UP-[A-Z0-9-]{8,}$/.test(id))return json({ok:false,message:'受付番号が不正です。'},400,origin);
      const allowedStatus=new Set(['pending','approved','rejected','published']);
      const status=String(body?.status||'');
      if(!allowedStatus.has(status))return json({ok:false,message:'審査状態が不正です。'},400,origin);
      const note=String(body?.reviewer_note||'').slice(0,2000);
      const patch={status,reviewer_note:note,reviewed_at:status==='pending'?null:new Date().toISOString()};
      const updated=await supabase.from('photo_submissions')
        .update(patch)
        .eq('submission_id',id)
        .select('submission_id,university_id,university_name,submitted_at,photo_count,main_photo,agreements,status,reviewer_note,reviewed_at')
        .single();
      if(updated.error)throw updated.error;
      return json({ok:true,submission:updated.data},200,origin);
    }

    return json({ok:false,message:'Unknown action'},400,origin);
  }catch(err){
    console.error(err);
    return json({ok:false,message:'審査処理を完了できませんでした。'},500,origin);
  }
});
