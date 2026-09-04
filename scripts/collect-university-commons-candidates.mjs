import fs from 'node:fs/promises';

// Re-run after PR #250 to isolate the remaining Tokyo universities without verified real photos.
const locationsPath='tools/university-database/tokyo/data/tokyo_locations.json';
const imagesPath='tools/university-database/tokyo/data/university-images.json';
const outPath=process.argv[2]||'tmp/university-commons-candidates.json';
const locations=JSON.parse(await fs.readFile(locationsPath,'utf8'));
const registry=JSON.parse(await fs.readFile(imagesPath,'utf8'));
const current=registry.images||{};

const acceptedLicense=/^(CC0|CC BY(?:-SA)?(?: |$)|Public domain|PD)/i;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const text=v=>String(v?.value||v||'').replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim();
const norm=s=>String(s||'').normalize('NFKC').toLowerCase().replace(/[\s・･,，.。()（）\-_]/g,'').replace(/大学院大学|専門職大学|大学/g,'');

function scoreCandidate(university,page,meta){
  const hay=norm(`${page.title} ${text(meta.ObjectName)} ${text(meta.ImageDescription)} ${text(meta.Categories)}`);
  const needle=norm(university.name);
  let score=0;
  if(needle&&hay.includes(needle))score+=100;
  if(norm(page.title).includes(needle))score+=40;
  const desc=text(meta.ImageDescription);
  if(desc.includes(university.name))score+=30;
  const title=page.title.toLowerCase();
  if(/logo|seal|emblem|map|diagram|poster|portrait|person|people|student|classroom/.test(title))score-=40;
  if(/campus|university|college|gate|building|hall|校舎|正門|門|キャンパス/.test(`${title} ${desc.toLowerCase()}`))score+=15;
  const width=page.imageinfo?.[0]?.width||0;
  const height=page.imageinfo?.[0]?.height||0;
  if(width>=1000&&height>=600)score+=10;
  return score;
}

async function fetchCommons(url){
  for(let attempt=0;attempt<5;attempt++){
    const response=await fetch(url,{headers:{
      'User-Agent':'BanTaiUniversityPhotoCollector/1.2 (education database; rights metadata audit)',
      'Accept':'application/json'
    }});
    if(response.ok)return response;
    if(response.status!==429&&response.status<500)throw new Error(`Commons ${response.status}`);
    const retryHeader=Number(response.headers.get('retry-after'));
    const waitMs=Number.isFinite(retryHeader)&&retryHeader>0?retryHeader*1000:Math.min(30000,2500*(attempt+1));
    console.log(`Commons ${response.status}; retrying in ${waitMs}ms`);
    await sleep(waitMs);
  }
  throw new Error('Commons rate limit retry exhausted');
}

async function searchCommons(university){
  const params=new URLSearchParams({
    action:'query',format:'json',origin:'*',generator:'search',
    gsrsearch:`\"${university.name}\"`,gsrnamespace:'6',gsrlimit:'6',
    prop:'imageinfo',iiprop:'url|mime|size|extmetadata',iiurlwidth:'640'
  });
  const url=`https://commons.wikimedia.org/w/api.php?${params}`;
  const response=await fetchCommons(url);
  const data=await response.json();
  const pages=Object.values(data.query?.pages||{});
  return pages.map(page=>{
    const ii=page.imageinfo?.[0]||{};
    const meta=ii.extmetadata||{};
    const license=text(meta.LicenseShortName)||text(meta.UsageTerms);
    const filePage=`https://commons.wikimedia.org/wiki/${encodeURIComponent(String(page.title).replace(/ /g,'_')).replace(/%3A/gi,':')}`;
    return {
      title:page.title,
      file_page:filePage,
      image_url:ii.url||'',
      thumbnail_url:ii.thumburl||'',
      mime:ii.mime||'',width:ii.width||0,height:ii.height||0,
      creator:text(meta.Artist),license,license_url:text(meta.LicenseUrl),
      description:text(meta.ImageDescription),credit:text(meta.Credit),
      categories:text(meta.Categories),
      score:scoreCandidate(university,page,meta),
      license_ok:acceptedLicense.test(license)
    };
  }).filter(x=>x.license_ok&&/^image\/(jpeg|png|webp)$/i.test(x.mime)&&x.image_url)
    .sort((a,b)=>b.score-a.score).slice(0,4);
}

const targets=locations.filter(u=>current[u.id]?.rights_status!=='verified');
const result={
  generated_at:new Date().toISOString(),
  policy:{auto_publish:false,accepted_license_pattern:String(acceptedLicense),note:'候補抽出のみ。大学一致・人物・画質・ライセンスを目視確認してから university-images.json に採用する。'},
  coverage:{total:locations.length,verified_real:Object.values(current).filter(x=>x.rights_status==='verified').length,ai_original:Object.values(current).filter(x=>x.rights_status==='ai_original').length,other_records:Object.values(current).filter(x=>!['verified','ai_original'].includes(x.rights_status)).length,target_count:targets.length},
  universities:[]
};
for(const [index,u] of targets.entries()){
  let candidates=[],error=null;
  try{candidates=await searchCommons(u);}catch(e){error=String(e?.message||e);}
  result.universities.push({university_id:u.id,university_name:u.name,municipality:u.municipality,current_status:current[u.id]?.rights_status||'missing',candidates,error});
  console.log(`[${index+1}/${targets.length}] ${u.id} ${u.name}: ${candidates.length} candidates${error?` (${error})`:''}`);
  await sleep(1000);
}
await fs.mkdir(outPath.split('/').slice(0,-1).join('/')||'.',{recursive:true});
await fs.writeFile(outPath,JSON.stringify(result,null,2)+'\n');
const withCandidates=result.universities.filter(x=>x.candidates.length).length;
console.log(`coverage total=${result.coverage.total} verified=${result.coverage.verified_real} ai=${result.coverage.ai_original} target=${result.coverage.target_count}`);
console.log(`universities_with_candidates=${withCandidates}/${targets.length}`);
