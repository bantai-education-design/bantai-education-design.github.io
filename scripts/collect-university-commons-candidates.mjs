import fs from 'node:fs/promises';

const locationsPath='tools/university-database/tokyo/data/tokyo_locations.json';
const imagesPath='tools/university-database/tokyo/data/university-images.json';
const outPath=process.argv[2]||'tmp/university-commons-candidates.json';
const locations=JSON.parse(await fs.readFile(locationsPath,'utf8'));
const registry=JSON.parse(await fs.readFile(imagesPath,'utf8'));
const current=registry.images||{};

const acceptedLicense=/^(CC0|CC BY(?:-SA)?(?: |$)|Public domain|PD|Copyrighted free use)/i;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const text=v=>String(v?.value||v||'').replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim();
const norm=s=>String(s||'').normalize('NFKC').toLowerCase().replace(/[\s・･,，.。()（）\-_]/g,'').replace(/大学院大学|専門職大学|大学/g,'');

const supplementalQueries={
  u000069:[
    '"Japan College of Social Work"',
    '"Japan College of Social Work" Kiyose'
  ],
  u000090:[
    '"Nihonbashi Takashimaya Mitsui Building"',
    '"日本橋髙島屋三井ビルディング"'
  ],
  u000123:[
    '"Daiwa Misakicho Building"',
    '"Daiwa 三崎町ビル"',
    '"三崎町ビル" 神田'
  ]
};

function scoreCandidate(university,page,meta){
  const hay=norm(`${page.title} ${text(meta.ObjectName)} ${text(meta.ImageDescription)} ${text(meta.Categories)}`);
  const needle=norm(university.name);
  let score=0;
  if(needle&&hay.includes(needle))score+=100;
  if(norm(page.title).includes(needle))score+=40;
  const desc=text(meta.ImageDescription);
  if(desc.includes(university.name))score+=30;
  const combined=`${page.title} ${desc} ${text(meta.Categories)}`.toLowerCase();
  if(/logo|seal|emblem|map|diagram|poster|portrait|person|people|student|classroom|ロゴ|校章|人物|学生/.test(combined))score-=45;
  if(/cafeteria|dining|restaurant|bus|gymnasium|stadium|食堂|レストラン|バス|体育館|競技場/.test(combined))score-=25;
  if(/campus|university|college|gate|building|hall|main building|校舎|正門|門|キャンパス|本館|大学棟/.test(combined))score+=20;
  const width=page.imageinfo?.[0]?.width||0;
  const height=page.imageinfo?.[0]?.height||0;
  if(width>=1200&&height>=700)score+=12;
  return score;
}

async function fetchCommons(url){
  for(let attempt=0;attempt<5;attempt++){
    const response=await fetch(url,{headers:{
      'User-Agent':'BanTaiUniversityPhotoCollector/1.3 (education database; rights metadata audit)',
      'Accept':'application/json'
    }});
    if(response.ok)return response;
    if(response.status!==429&&response.status<500)throw new Error(`Commons ${response.status}`);
    const retryHeader=Number(response.headers.get('retry-after'));
    const waitMs=Number.isFinite(retryHeader)&&retryHeader>0?retryHeader*1000:Math.min(45000,3000*(attempt+1));
    console.log(`Commons ${response.status}; retrying in ${waitMs}ms`);
    await sleep(waitMs);
  }
  throw new Error('Commons rate limit retry exhausted');
}

async function searchOnce(university,query){
  const params=new URLSearchParams({
    action:'query',format:'json',origin:'*',generator:'search',
    gsrsearch:query,gsrnamespace:'6',gsrlimit:'8',
    prop:'imageinfo',iiprop:'url|mime|size|extmetadata',iiurlwidth:'640'
  });
  const response=await fetchCommons(`https://commons.wikimedia.org/w/api.php?${params}`);
  const data=await response.json();
  return Object.values(data.query?.pages||{}).map(page=>({page,query}));
}

async function searchCommons(university){
  const queries=[
    `"${university.name}"`,
    `"${university.name}" 正門`,
    `"${university.name}" キャンパス`,
    `"${university.name}" 校舎`,
    ...(supplementalQueries[university.id]||[])
  ];
  const found=new Map();
  for(const query of queries){
    for(const item of await searchOnce(university,query)){
      const key=String(item.page.title||'');
      if(!found.has(key))found.set(key,{page:item.page,queries:new Set()});
      found.get(key).queries.add(query);
    }
    await sleep(1100);
  }
  return [...found.values()].map(({page,queries})=>{
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
      categories:text(meta.Categories),query_sources:[...queries],
      score:scoreCandidate(university,page,meta),
      license_ok:acceptedLicense.test(license)
    };
  }).filter(x=>x.license_ok&&/^image\/(jpeg|png|webp)$/i.test(x.mime)&&x.image_url)
    .sort((a,b)=>b.score-a.score).slice(0,10);
}

const targets=locations.filter(u=>current[u.id]?.rights_status!=='verified');
const result={
  generated_at:new Date().toISOString(),
  policy:{auto_publish:false,accepted_license_pattern:String(acceptedLicense),search_version:3,note:'候補抽出のみ。大学一致・人物・画質・ライセンスを目視確認してから university-images.json に採用する。未充足校では英語名や現行入居建物名も補助検索する。Commons上で目的を問わない再利用・再配布・商用利用・改変が明示された Copyrighted free use も候補として許可する。'},
  coverage:{total:locations.length,verified_real:Object.values(current).filter(x=>x.rights_status==='verified').length,ai_original:Object.values(current).filter(x=>x.rights_status==='ai_original').length,other_records:Object.values(current).filter(x=>!['verified','ai_original'].includes(x.rights_status)).length,target_count:targets.length},
  universities:[]
};
for(const [index,u] of targets.entries()){
  let candidates=[],error=null;
  try{candidates=await searchCommons(u);}catch(e){error=String(e?.message||e);}
  result.universities.push({university_id:u.id,university_name:u.name,municipality:u.municipality,current_status:current[u.id]?.rights_status||'missing',candidates,error});
  console.log(`[${index+1}/${targets.length}] ${u.id} ${u.name}: ${candidates.length} candidates${error?` (${error})`:''}`);
  await sleep(1200);
}
await fs.mkdir(outPath.split('/').slice(0,-1).join('/')||'.',{recursive:true});
await fs.writeFile(outPath,JSON.stringify(result,null,2)+'\n');
const withCandidates=result.universities.filter(x=>x.candidates.length).length;
console.log(`coverage total=${result.coverage.total} verified=${result.coverage.verified_real} ai=${result.coverage.ai_original} target=${result.coverage.target_count}`);
console.log(`universities_with_candidates=${withCandidates}/${targets.length}`);
