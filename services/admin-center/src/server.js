import http from 'node:http';
import {readFileSync,mkdirSync,writeFileSync,existsSync,realpathSync} from 'node:fs';
import {resolve,dirname,extname,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {randomBytes,createHash,scryptSync,timingSafeEqual,randomUUID} from 'node:crypto';
import {Store} from './store.js';
import {GitHub} from './github.js';
import {validateArticle,articlePage} from './content.js';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../../..');
const hash=s=>createHash('sha256').update(s).digest('hex');
export function passwordHash(password,salt=randomBytes(16).toString('hex')) {return `${salt}:${scryptSync(password,salt,64).toString('hex')}`;}
function checkPassword(password,encoded) {
  const [salt,key]=encoded.split(':');
  const actual=scryptSync(String(password),salt,64),expected=Buffer.from(key,'hex');
  return expected.length===actual.length && timingSafeEqual(actual,expected);
}
export function createApp({origin,dataDir,password,githubToken,development=false,github}={}) {
  if(!origin || new URL(origin).origin!==origin || (!development && !origin.startsWith('https://'))) throw Error('ADMIN_ORIGINはHTTPSのoriginを指定してください');
  if(development && !['127.0.0.1','localhost','[::1]'].includes(new URL(origin).hostname)) throw Error('開発HTTPモードはloopbackのみです');
  if(!password || !/^[a-f0-9]{32}:[a-f0-9]{128}$/.test(password)) throw Error('ADMIN_PASSWORD_HASHが未設定または不正です');
  dataDir=resolve(dataDir || '');
  if(dataDir===root || dataDir.startsWith(root+sep)) throw Error('保存先は公開リポジトリ外を指定してください');
  mkdirSync(resolve(dataDir,'images'),{recursive:true,mode:0o700});
  const store=new Store(resolve(dataDir,'admin.sqlite'));
  const gh=github || new GitHub(githubToken);
  let publishing=false;
  function send(res,status,value,type='application/json; charset=utf-8') {res.writeHead(status,{'Content-Type':type});res.end(type.startsWith('application/json')?JSON.stringify(value):value);}
  async function body(req,max=700000) {
    let size=0,parts=[];
    for await(const chunk of req) {size+=chunk.length;if(size>max) throw Object.assign(Error('送信サイズが大きすぎます'),{status:413});parts.push(chunk);}
    if(!(req.headers['content-type'] || '').startsWith('application/json')) throw Object.assign(Error('JSON形式が必要です'),{status:415});
    try{return JSON.parse(Buffer.concat(parts).toString());}catch{throw Object.assign(Error('JSONが不正です'),{status:400});}
  }
  const imageFile=p=>resolve(dataDir,'images',p.split('/').pop());
  const server=http.createServer(async(req,res)=>{
    res.setHeader('Cache-Control','no-store');res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('X-Frame-Options','DENY');res.setHeader('Referrer-Policy','no-referrer');
    res.setHeader('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'");
    if(!development) res.setHeader('Strict-Transport-Security','max-age=31536000');
    try {
      const path=new URL(req.url,origin).pathname;
      const mutate=!['GET','HEAD'].includes(req.method);
      if(mutate && req.headers.origin!==origin) return send(res,403,{message:'許可されていない送信元です'});
      if(req.method==='POST' && path==='/api/login') {
        const input=await body(req,4096);
        // Use socket IP, never untrusted forwarding headers. A reverse proxy may share a limit.
        const ip=req.socket.remoteAddress || 'unknown', now=Date.now();
        const old=store.db.prepare('SELECT * FROM attempts WHERE ip=?').get(ip);
        if(old && old.expires>now && old.count>=5) return send(res,429,{message:'ログイン試行が多すぎます。15分後にお試しください'});
        if(typeof input.password!=='string' || input.password.length>1000 || !checkPassword(input.password,password)) {
          store.db.prepare('INSERT INTO attempts VALUES(?,?,?) ON CONFLICT(ip) DO UPDATE SET count=excluded.count,expires=excluded.expires').run(ip,old && old.expires>now?old.count+1:1,old && old.expires>now?old.expires:now+900000);
          return send(res,401,{message:'ログインできませんでした'});
        }
        store.db.prepare('DELETE FROM attempts WHERE ip=? OR expires<?').run(ip,now);
        store.db.prepare('DELETE FROM sessions WHERE expires<?').run(now);
        const token=randomBytes(32).toString('hex'),csrf=randomBytes(32).toString('hex');
        store.db.prepare('INSERT INTO sessions VALUES(?,?,?)').run(hash(token),csrf,now+8*3600000);
        res.setHeader('Set-Cookie',`${development?'bantai_dev':'__Host-bantai'}=${token}; Path=/; HttpOnly; SameSite=Strict; Max-Age=28800${development?'':'; Secure'}`);
        store.event('session.login',{}); return send(res,200,{csrf});
      }
      const cookieName=development?'bantai_dev':'__Host-bantai';
      const token=(req.headers.cookie || '').split(';').map(s=>s.trim()).find(s=>s.startsWith(cookieName+'='))?.slice(cookieName.length+1) || '';
      const session=store.db.prepare('SELECT * FROM sessions WHERE hash=? AND expires>?').get(hash(token),Date.now());
      if(path.startsWith('/api/') || path.startsWith('/assets/images/admin/')) {
        if(!session) return send(res,401,{message:'ログインしてください'});
        if(mutate && req.headers['x-csrf-token']!==session.csrf) return send(res,403,{message:'再ログインしてください'});
        if(path==='/api/session' && req.method==='GET') return send(res,200,{csrf:session.csrf,publicationConfigured:!!(github || githubToken)});
        if(path==='/api/logout' && req.method==='POST') {
          store.db.prepare('DELETE FROM sessions WHERE hash=?').run(hash(token));
          res.setHeader('Set-Cookie',`${cookieName}=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0${development?'':'; Secure'}`); return send(res,200,{ok:true});
        }
        if(path==='/api/articles' && req.method==='GET') return send(res,200,store.list());
        if(path==='/api/articles' && req.method==='POST') {const b=await body(req);return send(res,201,store.save(null,0,validateArticle(b)));}
        const match=path.match(/^\/api\/articles\/([a-f0-9-]{36})(?:\/(versions|restore|preview|publish|unpublish))?$/);
        if(match) {
          const [,id,action]=match,a=store.get(id);if(!a) return send(res,404,{message:'記事がありません'});
          if(!action && req.method==='GET') return send(res,200,a);
          if(!action && req.method==='PUT') {const b=await body(req);return send(res,200,store.save(id,b.revision,validateArticle(b)));}
          if(action==='versions' && req.method==='GET') return send(res,200,store.versions(id));
          if(action==='restore' && req.method==='POST') {const b=await body(req);return send(res,200,store.restore(id,b.revision,b.target));}
          if(action==='preview' && req.method==='GET') return send(res,200,articlePage(a),'text/html; charset=utf-8');
          if(['publish','unpublish'].includes(action) && req.method==='POST') {
            const b=await body(req);if(b.revision!==a.revision) return send(res,409,{message:'保存した最新版から申請してください'});
            if(publishing) return send(res,409,{message:'公開申請中です'});
            publishing=true;
            try {
              const pr=await gh.publish(store,a,action,p=>readFileSync(imageFile(p)));
              const request={id:randomUUID(),article_id:id,revision:a.revision,action,url:pr.html_url,number:pr.number,state:'open'};
              store.db.prepare('INSERT INTO requests VALUES(?,?,?,?,?,?,?,?)').run(...Object.values(request));store.event('publication.requested',request);
              return send(res,201,request);
            } finally {publishing=false;}
          }
        }
        if(path==='/api/history' && req.method==='GET') return send(res,200,{events:store.history(),requests:store.requests()});
        if(path==='/api/sync' && req.method==='POST') {await gh.sync(store);return send(res,200,{requests:store.requests()});}
        if(path==='/api/legacy' && req.method==='GET') return send(res,200,JSON.parse(readFileSync(resolve(root,'data/columns.json'),'utf8')));
        if(path==='/api/proposals' && req.method==='GET') return send(res,200,store.db.prepare('SELECT * FROM proposals ORDER BY rowid DESC').all().map(r=>({id:r.id,...JSON.parse(r.body),created:r.created})));
        if(path==='/api/proposals' && req.method==='POST') {
          const b=await body(req,40000);
          if(!['tokyo','kanagawa','saitama'].includes(b.region) || ![b.universityId,b.field,b.before,b.after,b.reason].every(v=>typeof v==='string' && v.trim() && v.length<=5000)) throw Error('地域・大学ID・項目・変更前後・理由を入力してください');
          const data={region:b.region,universityId:b.universityId,field:b.field,before:b.before,after:b.after,reason:b.reason,source:new URL(b.source).protocol==='https:'?b.source:null};
          if(!data.source) throw Error('公式出典のHTTPS URLを入力してください');
          const id=randomUUID();store.db.prepare('INSERT INTO proposals VALUES(?,?,?)').run(id,JSON.stringify(data),new Date().toISOString());store.event('university.proposed',{id});return send(res,201,{id,...data});
        }
        const proposal=path.match(/^\/api\/proposals\/([a-f0-9-]{36})\/submit$/);
        if(proposal && req.method==='POST') {
          const p=store.db.prepare('SELECT * FROM proposals WHERE id=?').get(proposal[1]);if(!p) return send(res,404,{message:'提案がありません'});
          if(publishing) return send(res,409,{message:'公開申請中です'});publishing=true;
          try {
            const pr=await gh.createPR([{path:`data-source/admin-proposals/${p.id}.json`,content:JSON.stringify(JSON.parse(p.body),null,2)+'\n'}],'大学DB修正提案', '出典・大学IDを確認し、既存データ生成パイプラインで反映してください。このPRだけでは公開DBを変更しません。');
            const request={id:randomUUID(),article_id:null,revision:null,action:'university-proposal',url:pr.html_url,number:pr.number,state:'open'};
            store.db.prepare('INSERT INTO requests VALUES(?,?,?,?,?,?,?,?)').run(...Object.values(request));store.event('university.requested',request);return send(res,201,request);
          } finally {publishing=false;}
        }
        if(path==='/api/images' && req.method==='POST') {
          const b=await body(req,7500000),buf=Buffer.from(String(b.base64 || ''),'base64');
          let ext;
          if(buf.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]))) ext='png';
          else if(buf[0]===255 && buf[1]===216 && buf[2]===255) ext='jpg';
          else if(buf.toString('ascii',0,4)==='RIFF' && buf.toString('ascii',8,12)==='WEBP') ext='webp';
          if(!ext || buf.length>5*1024*1024) throw Error('5MB以内のPNG/JPEG/WebPを選択してください');
          const name=`${hash(buf)}.${ext}`,dest=resolve(dataDir,'images',name);
          if(!existsSync(dest)) writeFileSync(dest,buf,{mode:0o600,flag:'wx'});
          store.event('image.uploaded',{name});return send(res,201,{src:`/assets/images/admin/${name}`});
        }
        if(/^\/assets\/images\/admin\/[a-f0-9]{64}\.(png|jpg|webp)$/.test(path) && req.method==='GET') return send(res,200,readFileSync(imageFile(path)),`image/${path.endsWith('.jpg')?'jpeg':extname(path).slice(1)}`);
        return send(res,404,{message:'APIが見つかりません'});
      }
      if(!['GET','HEAD'].includes(req.method)) return send(res,405,{message:'この操作は利用できません'});
      // Serve only the login/editor shell and its assets, never source files or storage.
      const file=path==='/'?resolve(root,'admin/center/index.html'):resolve(root,'.'+path);
      const safe=resolve(root,'admin/center')+sep;
      if(!file.startsWith(safe) || !['.html','.js','.css'].includes(extname(file))) return send(res,404,{message:'ページがありません'});
      const real=realpathSync(file);if(!real.startsWith(safe)) return send(res,404,{message:'ページがありません'});
      return send(res,200,readFileSync(real),{'.html':'text/html; charset=utf-8','.js':'application/javascript; charset=utf-8','.css':'text/css; charset=utf-8'}[extname(file)]);
    } catch(e) {
      const status=e.status || (e.code==='ENOENT'?404:400);
      // Never log tokens, submitted bodies, upstream responses or credential errors.
      return send(res,status,{message:e.message || '操作に失敗しました'});
    }
  });
  server.requestTimeout=30000;server.headersTimeout=10000;
  return {server,store};
}
if(process.argv[1]===fileURLToPath(import.meta.url)) {
  const {ADMIN_ORIGIN,ADMIN_DATA_DIR,ADMIN_PASSWORD_HASH,ADMIN_GITHUB_TOKEN,ADMIN_DEV_HTTP,PORT}=process.env;
  if(!ADMIN_DATA_DIR) throw Error('ADMIN_DATA_DIRを設定してください');
  const {server}=createApp({origin:ADMIN_ORIGIN,dataDir:ADMIN_DATA_DIR,password:ADMIN_PASSWORD_HASH,githubToken:ADMIN_GITHUB_TOKEN,development:ADMIN_DEV_HTTP==='1'});
  server.listen(Number(PORT || 8787),'127.0.0.1',()=>console.log('Ban.Tai管理サーバー起動'));
}
