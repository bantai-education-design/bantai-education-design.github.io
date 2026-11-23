// 工程8: 案内型検索（大学名を知らない利用者向けに、5つの質問から登録済み客観事実のみで候補を案内し、既存の統一検索へ引き継ぐ）
(()=>{
'use strict';
if(typeof state==='undefined')return;

const esc=(v='')=>String(v).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const typeLabel={national:'国立',public:'公立',private:'私立'};
const guided={field:'all',qual:'',pref:'all',withCampus:false,type:'all',scale:'all',admGuide:'all'};

function buildSection(){
  const searchSec=document.querySelector('#search');
  if(!searchSec||document.querySelector('#guided-discovery'))return null;
  const sec=document.createElement('section');
  sec.id='guided-discovery';
  sec.className='section guided-section';
  sec.setAttribute('aria-label','5つの質問から大学を探す案内');
  sec.innerHTML=`
    <div class="guided-shell">
      <div class="guided-head">
        <div>
          <span class="section-kicker">GUIDED DISCOVERY</span>
          <h2>大学名が決まっていない方へ：5つの質問から探す</h2>
          <p>学びたい分野・取りたい資格・通える地域・設置区分や公式導線・大学規模を選ぶと、登録済みの事実データだけで候補を案内します。</p>
        </div>
        <button type="button" id="guided-toggle-btn" class="guided-toggle-btn" aria-expanded="false" aria-controls="guided-body">案内フォームを開く</button>
      </div>
      <div id="guided-body" class="guided-body" hidden>
        <div class="guided-grid">
          <div class="guided-q">
            <span class="guided-q-no">Q1</span>
            <label class="guided-q-title" for="guided-field">何を学びたいですか？</label>
            <select id="guided-field" class="guided-select">
              <option value="all">まだ決まっていない（すべて）</option>
              <option value="tech">情報・AI・工学</option>
              <option value="health">医療・看護・薬・保健</option>
              <option value="law_econ">経済・経営・法・政治</option>
              <option value="human_soc">人文・心理・社会・福祉</option>
              <option value="edu">教育・保育・子ども</option>
              <option value="global">国際・語学</option>
              <option value="arts">芸術・デザイン・音楽</option>
              <option value="sci_agri">理学・農学・環境・食</option>
              <option value="sports">スポーツ・健康</option>
            </select>
          </div>
          <div class="guided-q">
            <span class="guided-q-no">Q2</span>
            <label class="guided-q-title" for="guided-qual">取りたい資格・免許はありますか？</label>
            <select id="guided-qual" class="guided-select">
              <option value="">指定しない</option>
            </select>
          </div>
          <div class="guided-q">
            <span class="guided-q-no">Q3</span>
            <label class="guided-q-title" for="guided-pref">通える地域はどこですか？</label>
            <select id="guided-pref" class="guided-select">
              <option value="all">指定しない（4都県すべて）</option>
              <option value="東京都">東京都</option>
              <option value="埼玉県">埼玉県</option>
              <option value="神奈川県">神奈川県</option>
              <option value="千葉県">千葉県</option>
            </select>
            <label class="guided-check"><input type="checkbox" id="guided-campus" disabled><span>他県本部でも、その都県にキャンパスがある大学を含める</span></label>
          </div>
          <div class="guided-q">
            <span class="guided-q-no">Q4</span>
            <label class="guided-q-title" for="guided-type">設置区分・確認済み公式導線</label>
            <div class="guided-pair">
              <select id="guided-type" class="guided-select" aria-label="設置区分">
                <option value="all">国公私立すべて</option>
                <option value="national">国立</option>
                <option value="public">公立</option>
                <option value="private">私立</option>
              </select>
              <select id="guided-adm" class="guided-select" aria-label="入試・イベント導線">
                <option value="all">導線条件なし</option>
                <option value="guidelines">募集要項URL確認済み</option>
                <option value="web">Web出願URL確認済み</option>
                <option value="opencampus">オープンキャンパスURL確認済み</option>
              </select>
            </div>
          </div>
          <div class="guided-q">
            <span class="guided-q-no">Q5</span>
            <label class="guided-q-title" for="guided-scale">希望する大学規模（在籍学生数）</label>
            <select id="guided-scale" class="guided-select">
              <option value="all">こだわらない</option>
              <option value="small">小規模（1,500人未満）</option>
              <option value="medium">中規模（1,500〜4,999人）</option>
              <option value="large">大規模（5,000人以上）</option>
            </select>
          </div>
        </div>
        <div class="guided-result-panel">
          <div class="guided-result-head">
            <strong id="guided-match-count" role="status" aria-live="polite">条件を選ぶと候補大学数が表示されます</strong>
            <div class="guided-result-actions">
              <button type="button" id="guided-reset-btn" class="btn">回答をリセット</button>
              <button type="button" id="guided-apply-btn" class="btn primary">この条件で一覧を見る</button>
            </div>
          </div>
          <div id="guided-preview-list" class="guided-preview-list"></div>
          <p class="guided-policy-note">※ 登録済みの客観事実（分野・資格・所在地・学生数・公式導線）のみを使って候補を抽出します。適性の推測や独自の大学ランキングは行いません。</p>
        </div>
      </div>
    </div>
  `;
  searchSec.parentNode.insertBefore(sec,searchSec);
  return sec;
}

function populateQualifications(){
  const sel=document.querySelector('#guided-qual');
  if(!sel||sel.options.length>1)return;
  const counts=new Map();
  for(const row of state.rows){
    const groups=new Set((state.qualIdx.get(row.id)||[]).map(x=>x.group).filter(Boolean));
    for(const g of groups)counts.set(g,(counts.get(g)||0)+1);
  }
  const sorted=[...counts.entries()].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0],'ja'));
  for(const [g,n] of sorted){
    const opt=document.createElement('option');
    opt.value=g;
    opt.textContent=`${g}（${n}校）`;
    sel.appendChild(opt);
  }
}

function buildGuidedReasons(row){
  const reasons=[];
  if(guided.field!=='all'){
    const cat=(window.FIELD_CATEGORIES||[]).find(c=>c.id===guided.field);
    const tags=(row.academic_field_tags||[]).filter(t=>cat?.re?.test(t)).slice(0,2);
    reasons.push(`学びたい分野：${tags.length?tags.join('・'):(cat?.label||guided.field)}`);
  }
  if(guided.qual){
    const qs=(state.qualIdx.get(row.id)||[]).filter(x=>x.group===guided.qual).map(x=>x.name.replace(/（.*?）/g,'')).slice(0,2);
    reasons.push(`取得可能資格：${qs.length?qs.join('・'):guided.qual}`);
  }
  if(guided.pref!=='all'){
    const hp=row.prefecture||row.headquarters?.prefecture||'東京都';
    const muni=row.municipality||row.headquarters?.municipality||'';
    if(hp===guided.pref)reasons.push(`地域：${hp} ${muni}`);
    else if(guided.withCampus){
      const cs=(state.campusIdx.get(row.id)?.campuses||[]).filter(c=>c.prefecture===guided.pref).map(c=>c.name||'キャンパス').slice(0,2);
      reasons.push(`キャンパス：${guided.pref}${cs.length?`（${cs.join('・')}）`:''}`);
    }
  }
  if(guided.type!=='all'){
    reasons.push(`設置区分：${typeLabel[row.establishment_type]||''}`);
  }
  if(guided.admGuide!=='all'){
    reasons.push(`公式導線：${(window.ADM_GUIDE_LABELS||{})[guided.admGuide]||guided.admGuide}`);
  }
  if(guided.scale!=='all'){
    const n=Number(row.student_counts?.total)||0;
    reasons.push(`大学規模：在籍者数 ${n.toLocaleString('ja-JP')}人（${(window.SCALE_LABELS||{})[guided.scale]||''}）`);
  }
  return reasons;
}

function updateGuidedPreview(){
  if(!state.rows.length||typeof window.matchesAllUniversities!=='function')return;
  const ov={q:'',dept:'',status:'all',field:guided.field,qual:guided.qual,pref:guided.pref,withCampus:guided.withCampus,type:guided.type,scale:guided.scale,admGuide:guided.admGuide};
  const matches=state.rows.filter(r=>window.matchesAllUniversities(r,ov));
  const countEl=document.querySelector('#guided-match-count');
  const applyBtn=document.querySelector('#guided-apply-btn');
  const listEl=document.querySelector('#guided-preview-list');
  const hasAny=guided.field!=='all'||guided.qual||guided.pref!=='all'||guided.type!=='all'||guided.scale!=='all'||guided.admGuide!=='all';

  if(countEl)countEl.textContent=hasAny?`選んだ条件に一致する大学：${matches.length}校 / 全${state.rows.length}校`:`全${state.rows.length}校が対象です（気になる質問を1つ以上選んでください）`;
  if(applyBtn){
    applyBtn.textContent=`この条件で一覧を見る（${matches.length}校）`;
    applyBtn.disabled=matches.length===0;
  }
  if(!listEl)return;
  if(!hasAny){
    listEl.innerHTML='<p class="guided-empty-hint">例えば「Q1：医療・看護・薬・保健」＋「Q3：埼玉県」などを選ぶと、該当する大学と一致理由がここに表示されます。</p>';
    return;
  }
  if(!matches.length){
    listEl.innerHTML='<p class="guided-empty-hint">すべての条件を同時に満たす大学は0校でした。大学規模や公式導線、地域の条件を1つ緩めてお試しください。</p>';
    return;
  }
  const sample=matches.slice(0,4);
  listEl.innerHTML=sample.map(r=>{
    const reasons=buildGuidedReasons(r);
    const hp=r.prefecture||r.headquarters?.prefecture||'東京都';
    const muni=r.municipality||r.headquarters?.municipality||'';
    return `<article class="guided-preview-card"><div class="guided-preview-top"><span class="guided-preview-type">${esc(typeLabel[r.establishment_type]||'')}</span><span class="guided-preview-place">${esc(hp)} ${esc(muni)}</span></div><h3><a href="detail.html?id=${encodeURIComponent(r.id)}">${esc(r.name)}</a></h3><div class="guided-preview-reasons"><strong>一致した理由：</strong><span>${reasons.map(x=>esc(x)).join(' ／ ')}</span></div></article>`;
  }).join('')+(matches.length>4?`<p class="guided-more-note">ほか ${matches.length-4}校が一致しています。「この条件で一覧を見る」から全件確認できます。</p>`:'');
}

function init(){
  const sec=buildSection();
  if(!sec)return;
  const toggleBtn=sec.querySelector('#guided-toggle-btn');
  const body=sec.querySelector('#guided-body');
  const fSel=sec.querySelector('#guided-field');
  const qSel=sec.querySelector('#guided-qual');
  const pSel=sec.querySelector('#guided-pref');
  const cBox=sec.querySelector('#guided-campus');
  const tSel=sec.querySelector('#guided-type');
  const aSel=sec.querySelector('#guided-adm');
  const sSel=sec.querySelector('#guided-scale');

  toggleBtn.addEventListener('click',()=>{
    const opening=body.hidden;
    body.hidden=!opening;
    toggleBtn.setAttribute('aria-expanded',String(opening));
    toggleBtn.textContent=opening?'案内フォームを閉じる':'案内フォームを開く';
    if(opening){populateQualifications();updateGuidedPreview();}
  });

  const sync=()=>{
    guided.field=fSel.value;
    guided.qual=qSel.value;
    guided.pref=pSel.value;
    cBox.disabled=guided.pref==='all';
    if(guided.pref==='all')cBox.checked=false;
    guided.withCampus=cBox.checked;
    guided.type=tSel.value;
    guided.admGuide=aSel.value;
    guided.scale=sSel.value;
    updateGuidedPreview();
  };
  [fSel,qSel,pSel,cBox,tSel,aSel,sSel].forEach(el=>el.addEventListener('change',sync));

  sec.querySelector('#guided-reset-btn').addEventListener('click',()=>{
    fSel.value='all';qSel.value='';pSel.value='all';cBox.checked=false;cBox.disabled=true;tSel.value='all';aSel.value='all';sSel.value='all';
    sync();
  });
  sec.querySelector('#guided-apply-btn').addEventListener('click',()=>{
    if(typeof window.applyGuidedSearch==='function'){
      window.applyGuidedSearch({...guided});
    }
  });

  const waitData=()=>{
    if(!state.rows.length||!state.qualIdx.size){setTimeout(waitData,200);return;}
    populateQualifications();
    if(!body.hidden)updateGuidedPreview();
  };
  waitData();
}

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);
else init();
})();
