(()=>{
'use strict';
const CONFIG='submission-runtime-config.json';
const ready=()=>window.dispatchEvent(new CustomEvent('bantai-submission-transport-ready'));
window.__bantaiPhotoSubmissionTransport={mode:'local'};

async function load(){
  try{
    const response=await fetch(CONFIG,{cache:'no-store'});
    const config=response.ok?await response.json():null;
    if(!config?.enabled||config.mode!=='remote'||!/^https:\/\//i.test(config.endpoint||'')){
      document.documentElement.dataset.submissionTransport='local';
      ready();
      return;
    }
    const endpoint=config.endpoint;
    window.__bantaiPhotoSubmissionTransport={
      mode:'remote',
      async submit(pkg){
        if(!pkg?.blob||!pkg?.metadata)throw new Error('投稿データを作成できませんでした。');
        const form=new FormData();
        form.append('metadata',new Blob([JSON.stringify(pkg.metadata)],{type:'application/json'}),'submission.json');
        form.append('package',pkg.blob,pkg.filename||'university-photo-submission.zip');
        const response=await fetch(endpoint,{method:'POST',body:form,credentials:'omit',redirect:'follow'});
        let payload={};
        try{payload=await response.json();}catch(_e){}
        if(!response.ok||payload?.ok===false)throw new Error(payload?.message||`提出に失敗しました（${response.status}）。時間をおいて再度お試しください。`);
        if(!payload?.submission_id)payload.submission_id=pkg.metadata.submission_id;
        return payload;
      }
    };
    document.documentElement.dataset.submissionTransport='remote';
    ready();
  }catch(err){
    console.warn('Photo submission transport unavailable; keeping local safe mode.',err);
    window.__bantaiPhotoSubmissionTransport={mode:'local'};
    document.documentElement.dataset.submissionTransport='local-error';
    ready();
  }
}
load();
})();
