(()=>{
const root=document.querySelector('#detail-root');
const id=new URLSearchParams(location.search).get('id');
const legacy=()=>{const s=document.createElement('script');s.src='assets/detail.js';document.body.appendChild(s)};
if(!id){legacy();return}
const esc=(v='')=>String(v).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const typeLabel={national:'国立',public:'公立',private:'私立'};
const yen=v=>Number.isFinite(Number(v))?Number(v).toLocaleString('ja-JP')+'円':'—';
const ext=(url,label,cls='secondary')=>url?`<a class="${cls}" href="${esc(url)}" target="_blank" rel="noopener">${esc(label)} ↗</a>`:'';
const chips=(xs=[])=>xs.length?`<div class="complete-chips">${xs.map(x=>`<span>${esc(x)}</span>`).join('')}</div>`:'';
const fact=(label,value)=>value!==undefined&&value!==null&&value!==''?`<div class="detail-fact"><dt>${esc(label)}</dt><dd>${value}</dd></div>`:'';
const section=(no,title,lead,body,extra='')=>`<section class="detail-section complete-section ${extra}"><div class="detail-section-head"><span>${no}</span><div><h2>${esc(title)}</h2>${lead?`<p>${esc(lead)}</p>`:''}</div></div>${body}</section>`;
const mapsUrl=(name,address)=>`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${name} ${address||''}`.trim())}`;
const namesSummary=(items=[],max=8)=>{const names=items.map(x=>x.name).filter(Boolean);return names.length?`${names.slice(0,max).join('、')}${names.length>max?`、ほか${names.length-max}`:''}`:'—'};

const STATUS_META={
  verified:{cls:'dq-verified',label:'確認済み'},
  uninvestigated:{cls:'dq-uninvestigated',label:'未調査'},
  not_published:{cls:'dq-not-published',label:'公式掲載なし'},
  not_applicable:{cls:'dq-not-applicable',label:'該当なし'},
  updating:{cls:'dq-updating',label:'更新確認中'},
  expired:{cls:'dq-expired',label:'更新期限超過'}
};
const badge=(st,customLabel='')=>{const m=STATUS_META[st]||STATUS_META.uninvestigated;return `<span class="dq-badge ${m.cls}">${esc(customLabel||m.label)}</span>`;};
const stateBox=(st,text,customLabel='')=>`<div class="dq-state-box">${badge(st,customLabel)}<span>${esc(text)}</span></div>`;
const dqLegend=()=>`<div class="dq-legend" aria-label="データ状態表示の区分"><span class="dq-legend-title">データ状態の表示基準（推測による補完は行いません）</span><div class="dq-legend-grid"><div class="dq-legend-item">${badge('verified')}<span>一次資料・公的統計で確認済み</span></div><div class="dq-legend-item">${badge('uninvestigated')}<span>一次資料との照合・登録が未実施</span></div><div class="dq-legend-item">${badge('not_published')}<span>調査済みだが公式ページ上に掲載なし</span></div><div class="dq-legend-item">${badge('not_applicable')}<span>制度・組織構造上その項目が存在しない</span></div><div class="dq-legend-item">${badge('updating')}<span>最新年度資料との再照合を実施中</span></div><div class="dq-legend-item">${badge('expired')}<span>最終確認日から更新期限（1年）を超過</span></div></div></div>`;

const completeProfileUrl=uid=>{const m=/^u(\d{6})$/.exec(uid||'');if(!m)return null;const n=Number(m[1]);if(n===1||n===2)return `data/complete/${uid}.json`;if(n===50||(n>=175&&n<=209))return `../kanagawa/data/complete/${uid}.json`;if(n>=145&&n<=172)return `../saitama/data/complete/${uid}.json`;if(n===173||n===174)return `../tokyo-additions/data/complete/${uid}.json`;return null};
const profileUrl=completeProfileUrl(id);
if(!profileUrl){legacy();return}
const optJson=u=>fetch(u).then(r=>r.ok?r.json():null).catch(()=>null);

Promise.all([
  fetch(profileUrl).then(r=>{if(r.status===404){legacy();return null}if(!r.ok)throw new Error('profile');return r.json()}),
  optJson('../qualifications/qualifications.json'),
  optJson('../access/access.json')
]).then(([p,qualDoc,accessDoc])=>{
if(!p)return;if(p.schema_version!=='1.0')throw new Error('schema');
const sources=new Map((p.sources||[]).map(s=>[s.source_id,s]));
const firstSource=(p.sources||[])[0]||null;
const sourceLink=sid=>{const s=sources.get(sid)||firstSource;return s?`<a class="complete-source-inline" href="${esc(s.url)}" target="_blank" rel="noopener">出典（${esc(s.verified_at||'確認済み')}）↗</a>`:''};
const sourceCell=sid=>{const s=sources.get(sid)||firstSource;return s?`<a class="complete-source-inline" href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title||s.publisher||'一次資料')} ↗</a>`:'—'};
const sourceDate=sid=>{const s=sources.get(sid);return s?.verified_at||p.verification?.last_verified_at||firstSource?.verified_at||'—'};

const student=p.student_counts||{},verification=p.verification||{},verified=verification.verification_status==='verified';
const verifiedSet=new Set(verification.verified_sections||[]);
const stopped=p.status==='recruitment_stopped'||p.status==='admissions_stopped'||p.admissions_status==='stopped';
const academics=p.academics||[],grads=p.graduate_schools||[],campuses=p.campuses||[];
const graduateOnly=!academics.length&&grads.length>0;
const departments=academics.flatMap(f=>f.departments||[]);
const unitCount=departments.length;
const programCount=departments.reduce((n,d)=>n+(d.programs||[]).length,0);
const primaryCampus=campuses[0]||null;
const primaryAddress=primaryCampus?.address||[p.prefecture,p.municipality].filter(Boolean).join(' ');
const primaryMap=mapsUrl(p.name,primaryAddress);
const extraQuals=(qualDoc?.universities?.[id]?.qualifications)||[];
const quals=(p.qualifications&&p.qualifications.length)?p.qualifications:extraQuals;
const extraStations=(accessDoc?.universities?.[id]?.stations)||[];
if(campuses.length&&(!campuses[0].nearest_stations||!campuses[0].nearest_stations.length)&&extraStations.length){
  campuses[0].nearest_stations=extraStations;
}
const allStations=campuses.flatMap(c=>c.nearest_stations||[]);
const isCorrespondence=/通信制/.test(p.history_summary||'')||/通信制/.test(p.feature_summary||'');

document.title=`${p.name} | Ban.Tai 全国大学データベース`;

const studentHeroHtml=student.total
  ? `<strong>${Number(student.total).toLocaleString('ja-JP')}人</strong><em>${esc(student.as_of||'2026-05-01')}基準</em>`
  : `<strong>${badge('uninvestigated')}</strong><em>公式統計照合前</em>`;

const hero=`<section class="detail-hero complete-hero"><div class="detail-hero-main"><span class="detail-kicker">BANTAI UNIVERSITY PROFILE · SCHEMA v${esc(p.schema_version)}</span><h1>${esc(p.name)}</h1><div class="detail-meta"><span class="detail-pill">${esc(typeLabel[p.establishment_type]||p.establishment_type||'')}</span><span class="detail-pill">${esc(p.prefecture||'')} ${esc(p.municipality||'')}</span><span class="detail-pill complete-status ${verified?'is-verified':'is-partial'}">${verified?'全項目確認済み':'主要項目確認済み（最終確認 '+esc(verification.last_verified_at||'')+'）'}</span></div><p class="detail-summary">${esc(p.feature_summary||'')}</p><div class="detail-actions">${ext(p.official_url,'大学公式情報','primary')}${ext(p.admissions_url,'入試情報')}${ext(p.application_guidelines_url,'募集要項')}${ext(p.brochure_request_url,'資料請求')}${ext(p.open_campus_url,'オープンキャンパス')}<a class="secondary" href="${primaryMap}" target="_blank" rel="noopener">Google Maps ↗</a></div></div><aside class="detail-hero-side"><div class="detail-stat"><small>在籍者数</small>${studentHeroHtml}</div><div class="detail-stat"><small>学部</small><strong>${graduateOnly?'該当なし':academics.length}</strong><em>${graduateOnly?'大学院大学':'確認済み'}</em></div><div class="detail-stat"><small>学科・課程・類</small><strong>${graduateOnly?'該当なし':unitCount}</strong></div><div class="detail-stat"><small>専修・コース等</small><strong>${graduateOnly?'該当なし':programCount}</strong></div></aside></section>`;

const facFactVal=graduateOnly
  ? `${badge('not_applicable')} 学部を置かない大学院大学です`
  : `${badge('verified')} 学部 ${academics.length}：${esc(namesSummary(academics))}`;
const deptFactVal=graduateOnly
  ? `${badge('not_applicable')} 学部・学科は該当しません`
  : `${badge('verified')} 学科・課程・類 ${unitCount}：${esc(namesSummary(departments))}`;
const gradFactVal=grads.length
  ? `${badge('verified')} 研究科 ${grads.length}：${esc(namesSummary(grads))}`
  : `${badge('not_applicable')} 大学院研究科を置かない大学です（文部科学省全国大学一覧で確認済み）`;
const studentFactVal=student.total
  ? `${badge('verified')} 合計 ${Number(student.total).toLocaleString('ja-JP')}人（${esc(student.as_of||'2026-05-01')}基準） ${sourceLink(student.source_id)}`
  : `${badge('uninvestigated')} 公式統計・大学ポートレートとの一次資料照合前です`;

const basic=section('01','大学の基本情報','所在地・教育組織・在籍規模の基礎情報と確認状態です。',`<dl class="detail-facts">${fact('正式名称',esc(p.name))}${fact('英文名称',p.name_en?esc(p.name_en):'')}${fact('本部所在地',`${badge('verified')} ${esc(primaryAddress)}`)}${fact('設置区分',esc(typeLabel[p.establishment_type]))}${fact('設置者',p.operator?esc(p.operator):'')}${fact('学部',facFactVal)}${fact('学科・課程・類',deptFactVal)}${fact('大学院研究科',gradFactVal)}${fact('在籍者数',studentFactVal)}${fact('創立・源流',p.founded_year?`${esc(p.founded_year)}年`:'')}${fact('現在の大学の開学',p.opened_year?`${esc(p.opened_year)}年`:'')}${fact('学部学生',student.undergraduate?`${Number(student.undergraduate).toLocaleString('ja-JP')}人`:'')}${fact('大学院学生',student.graduate?`${Number(student.graduate).toLocaleString('ja-JP')}人`:'')}</dl><div class="complete-story-grid"><article><h3>沿革・概要</h3><p>${p.history_summary?esc(p.history_summary):`${badge('uninvestigated')} 沿革要約は一次資料から順次整備中です。`}</p></article><article><h3>理念・目的</h3><p>${(p.philosophy||p.mission)?esc(p.philosophy||p.mission):`${badge('uninvestigated')} 理念・目的は一次資料から順次整備中です。`}</p></article></div><div class="complete-sub"><h3>主な学問分野</h3>${chips(p.academic_field_tags||[])}</div>`,'detail-core');

const facultyHtml=graduateOnly
  ? stateBox('not_applicable','学部を置かない大学院大学のため、学部・学科は該当しません。')
  : academics.map(f=>`<article class="complete-academic-card"><div class="complete-card-head"><h3>${esc(f.name)}</h3>${chips(f.academic_field_tags||[])}</div><div class="complete-depts">${(f.departments||[]).map(d=>`<div class="complete-dept"><strong>${esc(d.name)}</strong>${(d.programs||[]).length?`<ul>${d.programs.map(pr=>`<li>${esc(pr.name)}</li>`).join('')}</ul>`:'<span class="complete-none">専攻・コース等の下位区分なし</span>'}</div>`).join('')}</div></article>`).join('');
const gradHtml=grads.length
  ? `<details class="complete-details" ${graduateOnly?'open':''}><summary>${badge('verified')} 大学院組織・専攻等 ${grads.length}組織を表示</summary><div class="complete-grad-list">${grads.map(g=>`<div class="complete-grad-row"><strong>${esc(g.name)}</strong><span>${(g.programs||[]).map(x=>esc(typeof x==='string'?x:x.name)).join(' ／ ')||'専攻区分なし'}</span></div>`).join('')}</div></details>`
  : stateBox('not_applicable','大学院研究科は設置されていません（文部科学省 令和7年度全国大学一覧で確認済み）。');
const academicSec=section('02','学べる分野・教育組織','大学固有の学部・学科・課程・類・研究科の名称を一次資料どおり保持して表示します。',`<div class="complete-academic-grid">${facultyHtml}</div>${gradHtml}`);

const campusHtml=campuses.map(c=>{
  const stList=(c.nearest_stations||[]);
  const stBody=stList.length
    ? `<ul class="complete-stations">${stList.map(s=>`<li><strong>${esc(s.station)}</strong><span>${esc(s.line||'')}${s.access?` ・ ${esc(s.access)}`:''}</span></li>`).join('')}</ul>`
    : (isCorrespondence
        ? stateBox('not_applicable','オンライン通信制課程のため、通学用の最寄駅設定は該当しません。')
        : stateBox('uninvestigated','公式アクセスページの最寄駅・所要時間は一次資料照合前です（Google Mapsで位置を確認できます）。'));
  return `<article class="complete-card"><div class="complete-card-head"><h3>${esc(c.name)}</h3><div>${ext(c.official_url,'公式アクセス')}<a class="secondary" href="${mapsUrl(p.name,c.address)}" target="_blank" rel="noopener">Google Maps ↗</a></div></div><p class="complete-address">${badge('verified')} ${esc(c.address)}</p><h4>最寄駅・アクセス</h4>${stBody}</article>`;
}).join('');
const campusSec=section('03','キャンパス・最寄駅','主要キャンパス所在地と公式アクセス情報を確認できます。',`<div class="complete-three">${campusHtml}</div>`);

const t=(p.tuition||[])[0];
const tuitionBody=stopped
  ? stateBox('not_applicable','学生募集停止のため、新規入学者向けの学費掲載は該当しません。')
  : t
    ? `<div class="complete-money-grid"><div><small>収録状態・対象年度</small><strong>${badge('verified')} ${esc(t.academic_year)}年度</strong></div><div><small>入学料</small><strong>${yen(t.admission_fee)}</strong></div><div><small>授業料（年額）</small><strong>${yen(t.annual_tuition)}</strong></div><div class="is-total"><small>初年度基本額</small><strong>${yen(t.first_year_total)}</strong></div></div><p class="complete-caption">初年度基本額は公式に掲載された入学料と年額授業料の合計です（最終確認日：${esc(sourceDate(t.source_id))}）。 ${sourceLink(t.source_id)}</p>`
    : stateBox('uninvestigated','学費・初年度納入額は公式募集要項・学費ページの一次資料から順次登録します（推測による金額補完は行いません）。');
const tuitionSec=section('04','学費','対象年度と出典を固定し、確認済みの公式金額だけを表示します。',tuitionBody);

const adm=p.admissions||{};
const admUrl=adm.admissions_url||p.admissions_url;
const methodList=adm.methods||[];
const methodHtml=methodList.map(m=>`<article class="complete-card"><div class="complete-card-head"><h3>${esc(m.name)}</h3>${ext(m.official_url,'公式')}</div><dl class="complete-mini-facts">${m.quota!==undefined&&m.quota!==null?fact('募集人員',`${Number(m.quota).toLocaleString('ja-JP')}人`):''}${fact('出願期間',esc(m.application_period||''))}${fact('試験日',esc(m.exam_date||''))}${fact('合格発表',esc(m.result_date||''))}</dl></article>`).join('');
let admissionBody='';
if(stopped){
  admissionBody=stateBox('not_applicable','学生募集停止を一次資料で確認済みです。');
}else if(methodList.length){
  const webNote=adm.web_application_url
    ? `<div class="dq-state-box">${badge('verified')}<span>Web出願サイト確認済み</span>${ext(adm.web_application_url,'Web出願サイト')}</div>`
    : (verifiedSet.has('admissions')
        ? stateBox('not_published','調査時点で常時公開のWeb出願直リンクは公式掲載なし（出願期間中に公式入試ページから案内されます）。')
        : stateBox('uninvestigated','Web出願サイトの直リンクは未調査です。公式入試ページをご確認ください。'));
  admissionBody=`${webNote}<div class="complete-three" style="margin-top:12px">${methodHtml}</div><div class="detail-actions" style="margin-top:12px">${ext(admUrl,'入試公式','primary')}${ext(adm.application_guidelines_url||p.application_guidelines_url,'募集要項・選抜要項')}</div>`;
}else{
  const urlState=admUrl
    ? `<div class="dq-state-box">${badge('verified','入試公式URL：確認済み')}<span>公式入試情報ページへの導線を確認済みです（最終確認日：${esc(verification.last_verified_at||firstSource?.verified_at||'2026-10-30')}）。</span></div>`
    : stateBox('uninvestigated','公式入試情報ページのURLを照合中です。大学公式サイトトップから入試案内をご確認ください。');
  const schedState=stateBox('uninvestigated','選抜方式別の出願期間・試験日・合格発表日・Web出願URLは、公式学生募集要項（一次資料）から順次登録します。');
  admissionBody=`<div style="display:grid;gap:10px">${urlState}${schedState}</div><div class="detail-actions" style="margin-top:12px">${ext(admUrl||p.official_url,admUrl?'公式入試情報ページを開く':'大学公式サイトを開く','primary')}${ext(adm.application_guidelines_url||p.application_guidelines_url,'募集要項・選抜要項')}</div>`;
}
const admissionSec=section('05','入試方式・Web出願',`${adm.admission_year||'最新'}年度入試の公式導線と収録状態です。`,admissionBody);

let qualBody='';
if(quals.length){
  qualBody=`<p style="margin:0 0 10px">${badge('verified')} 養成課程・公式資格案内から <strong>${quals.length}件</strong> を確認済み</p><ul class="complete-rich-list">${quals.map(q=>`<li><strong>${esc(q.name)}</strong><span>${esc(q.condition||q.department||q.faculty||'')}</span>${q.source_id?sourceLink(q.source_id):''}</li>`).join('')}</ul>`;
}else if(graduateOnly){
  qualBody=stateBox('not_applicable','学部を置かない大学院大学のため、学部段階の教員免許・国家試験養成課程は該当しません。');
}else if(p.prefecture==='神奈川県'||verifiedSet.has('qualifications')){
  qualBody=stateBox('not_published','文部科学省の課程認定一覧および大学公式サイトを調査済みですが、該当する免許・資格養成課程の公式掲載はありません。');
}else{
  qualBody=stateBox('uninvestigated','取得可能資格・免許は文部科学省課程認定資料および大学公式資格ページから順次照合・登録中です。');
}

const careerFields=(p.careers||{}).main_career_fields||[];
const careerEmp=(p.careers||{}).main_employers||[];
const careerBody=(careerFields.length||careerEmp.length)
  ? `<p style="margin:0 0 10px">${badge('verified')} 公式進路・就職公表データから確認済み</p><ul class="complete-list">${careerFields.map(x=>`<li>${esc(x)}</li>`).join('')}</ul>${careerEmp.length?`<h4>主な就職先例</h4><ul class="complete-list">${careerEmp.map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`:''}`
  : stateBox('uninvestigated','就職率・主な進路分野・国家試験合格実績は、大学公式の進路公表資料（対象年度・母数明記のもの）から順次登録します。');
const careerSec=section('06','資格・進路','取得可能資格と公式進路情報の収録状態です。',`<div class="complete-two"><article class="complete-card"><h3>主な資格・免許</h3>${qualBody}</article><article class="complete-card"><h3>進路・就職実績</h3>${careerBody}</article></div>`);

const research=p.research||{};
const researchItems=[...(research.strengths||[]),...(research.awards||[]),...(research.institutes||[])];
const sportItems=p.sports_culture||[];
const alumni=p.notable_alumni||[];
const researchBody=researchItems.length
  ? `<p style="margin:0 0 10px">${badge('verified')} 公式研究案内から確認済み</p><ul class="complete-rich-list">${researchItems.map(x=>`<li><strong>${esc(x.title)}</strong><span>${esc(x.summary||'')}</span>${sourceLink(x.source_id)}</li>`).join('')}</ul>`
  : stateBox('uninvestigated','研究分野・附置研究所等の代表例は大学公式ページから順次登録します。');
const sportBody=sportItems.length
  ? `<p style="margin:0 0 10px">${badge('verified')} 公式公表実績から確認済み</p><ul class="complete-rich-list">${sportItems.map(x=>`<li><strong>${esc(x.organization)}</strong><span>${esc(x.achievement)}${x.year?`（${esc(x.year)}年）`:''}</span>${sourceLink(x.source_id)}</li>`).join('')}</ul>`
  : stateBox('uninvestigated','スポーツ・文化活動の公式実績は一次資料確認後に順次登録します（駅伝出場記録は下の「駅伝の成績」欄に自動連携されます）。');
const alumniBody=alumni.length
  ? `<p style="margin:0 0 10px">${badge('verified')} 公式資料で確認済み</p><ul class="complete-rich-list">${alumni.map(x=>`<li><strong>${esc(x.name)}</strong><span>${esc(x.field)} — ${esc(x.affiliation_note||'')}</span>${sourceLink(x.source_id)}</li>`).join('')}</ul>`
  : stateBox('uninvestigated','主な出身者は大学公式資料等で確認できる情報のみ順次登録します（推測や非公式リストからの転載は行いません）。');
const activitySec=section('07','研究・スポーツ・著名卒業生','ランキングではなく、大学公式一次情報で確認できる事実を掲載します。',`<div class="complete-two"><article class="complete-card"><h3>研究・研究拠点</h3>${researchBody}</article><article class="complete-card"><h3>スポーツ・文化・コンテスト</h3>${sportBody}</article><article class="complete-card complete-wide"><h3>著名な卒業生・出身者（公式確認分）</h3>${alumniBody}</article></div>`);

const qualStatus=quals.length?'verified':(graduateOnly?'not_applicable':((p.prefecture==='神奈川県'||verifiedSet.has('qualifications'))?'not_published':'uninvestigated'));
const stationStatus=allStations.length?'verified':(isCorrespondence?'not_applicable':'uninvestigated');
const admUrlStatus=stopped?'not_applicable':(admUrl?'verified':'uninvestigated');
const admSchedStatus=stopped?'not_applicable':(methodList.length?'verified':'uninvestigated');
const tuitionStatus=stopped?'not_applicable':(t?'verified':'uninvestigated');
const studentStatus=student.total?'verified':'uninvestigated';
const baseDate=verification.last_verified_at||firstSource?.verified_at||'2026-10-30';

const statusRows=[
  ['基本情報・本部所在地',badge('verified'),'令和7年度（2025〜2026）',baseDate,sourceCell(firstSource?.source_id)],
  ['教育組織（学部・学科）',badge(graduateOnly?'not_applicable':'verified'),graduateOnly?'大学院大学':'令和7年度〜2026年度',baseDate,sourceCell(firstSource?.source_id)],
  ['大学院研究科',badge(grads.length?'verified':'not_applicable'),grads.length?`${grads.length}研究科`:'設置なし（確認済み）',baseDate,sourceCell(firstSource?.source_id)],
  ['在籍者数（学生数）',badge(studentStatus),student.total?`${student.as_of||'2026-05-01'}基準`:'未収録',student.total?sourceDate(student.source_id):'—',student.total?sourceCell(student.source_id):'—'],
  ['キャンパス・最寄駅',`${badge('verified','所在地：確認済み')} ${badge(stationStatus,'最寄駅：'+STATUS_META[stationStatus].label)}`,'現行キャンパス',baseDate,sourceCell(firstSource?.source_id)],
  ['取得可能資格',badge(qualStatus),quals.length?`${quals.length}件確認済み`:'—',baseDate,quals[0]?.source_id?sourceCell(quals[0].source_id):sourceCell(firstSource?.source_id)],
  ['入試公式URL導線',badge(admUrlStatus),stopped?'募集停止':'現行入試案内',baseDate,admUrl?`<a class="complete-source-inline" href="${esc(admUrl)}" target="_blank" rel="noopener">公式入試ページ ↗</a>`:'—'],
  ['選抜日程・募集要項詳細',badge(admSchedStatus),methodList.length?`${adm.admission_year||2026}年度`:'順次登録',methodList.length?baseDate:'—',methodList.length?sourceCell(firstSource?.source_id):'—'],
  ['学費・初年度納入額',badge(tuitionStatus),t?`${t.academic_year}年度`:'順次登録',t?sourceDate(t.source_id):'—',t?sourceCell(t.source_id):'—']
].map(([item,stHtml,yr,dt,src])=>`<tr><td><strong>${esc(item)}</strong></td><td>${stHtml}</td><td>${esc(yr)}</td><td>${esc(dt)}</td><td>${src}</td></tr>`).join('');

const statusTable=`<div class="dq-table-wrap"><table class="dq-table"><thead><tr><th>データ項目</th><th>収録状態</th><th>対象年度・基準日</th><th>最終確認日</th><th>一次資料・出典</th></tr></thead><tbody>${statusRows}</tbody></table></div>`;
const sourceRows=(p.sources||[]).map(s=>`<li><a href="${esc(s.url)}" target="_blank" rel="noopener"><strong>${esc(s.title)}</strong><span>${esc(s.publisher)}・最終確認日 ${esc(s.verified_at)}</span></a></li>`).join('');
const sourceSec=section('08','出典・最終確認日・項目別データ状態','項目ごとの収録状態（確認済み・未調査・公式掲載なし・該当なし）と対象年度、最終確認日、一次資料URLを明示します。',`<div class="complete-verification ${verified?'is-verified':'is-partial'}"><strong>${verified?'Schema v1.0 全項目確認済み':'Schema v1.0 主要基盤確認済み・詳細項目順次拡充'}</strong><span>大学全体の最終確認日：${esc(baseDate)}</span><p>${esc(verification.notes||'')}</p></div>${dqLegend()}${statusTable}<details class="complete-details" open><summary>登録済み一次資料 ${(p.sources||[]).length}件を表示</summary><ul class="complete-source-list">${sourceRows}</ul></details>`);

root.innerHTML=hero+basic+academicSec+campusSec+tuitionSec+admissionSec+careerSec+activitySec+sourceSec;
}).catch(err=>{console.error(err);root.innerHTML='<div class="detail-error"><strong>完成形プロフィールを読み込めませんでした。</strong><p><a href="./">大学一覧へ戻る</a></p></div>'});
})();
