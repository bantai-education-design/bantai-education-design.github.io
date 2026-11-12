import {safeURL} from './content.js';
export const PROFILE_FIELDS={operator:'設置者',philosophy:'建学の精神・理念',history_summary:'沿革・歴史',feature_summary:'大学の特色',admissions_url:'入試情報URL',application_guidelines_url:'募集要項URL',brochure_request_url:'資料請求URL',open_campus_url:'オープンキャンパスURL'};
export function profilePath(region,id) {
  if(!['tokyo','kanagawa','saitama'].includes(region) || !/^u[0-9]{6}$/.test(id))throw Error('地域または大学IDが不正です');
  return `tools/university-database/${region}/data/complete/${id}.json`;
}
export function applyProfileProposal(profile,proposal) {
  if(!Object.hasOwn(PROFILE_FIELDS,proposal.field))throw Error('この項目は既存パイプラインでの反映が必要です');
  if(profile.university_id!==proposal.universityId || (profile.id && profile.id!==proposal.universityId))throw Error('大学IDが一致しません');
  if(typeof proposal.after!=='string' || !proposal.after.trim() || proposal.after.length>5000)throw Error('変更後の値が不正です');
  if(proposal.before===proposal.after)throw Error('変更前と変更後が同じです');
  if(proposal.sourceConfirmed!==true)throw Error('公式出典と変更内容を確認してください');
  const source=safeURL(proposal.source);if(!source.startsWith('https://'))throw Error('出典はHTTPSにしてください');
  if((profile[proposal.field] || '')!==proposal.before)throw Object.assign(Error('大学データが更新されています。最新情報を取り込み直してください'),{status:409});
  if(proposal.field.endsWith('_url'))safeURL(proposal.after);
  const updated=structuredClone(profile);updated[proposal.field]=proposal.after;
  updated.verification={...(updated.verification || {}),verification_status:'needs_review',notes:[updated.verification?.notes,`管理センター修正提案: ${proposal.field} / ${proposal.reason} / 出典 ${source}`].filter(Boolean).join('\n')};
  return updated;
}
