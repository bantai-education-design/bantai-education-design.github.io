import {randomBytes,createHash} from 'node:crypto';
import {Buffer} from 'node:buffer';
export const hash=s=>createHash('sha256').update(s).digest('hex');
const random=()=>randomBytes(32).toString('base64url');
export const cookie=(request,name)=>(request.headers.get('cookie') || '').split(';').map(s=>s.trim()).find(s=>s.startsWith(name+'='))?.slice(name.length+1) || '';
export const authReady=env=>!!(env.GITHUB_OAUTH_CLIENT_ID && env.GITHUB_OAUTH_CLIENT_SECRET && env.ADMIN_GITHUB_LOGIN && env.SESSION_SECRET?.length>=32);
export function sessionCookie(token,maxAge=28800){return `__Host-bantai=${token}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=${maxAge}`;}
async function key(secret){return crypto.subtle.importKey('raw',new TextEncoder().encode(secret),{name:'HMAC',hash:'SHA-256'},false,['sign','verify']);}
async function sign(value,secret){const encoded=Buffer.from(JSON.stringify(value)).toString('base64url'),signature=await crypto.subtle.sign('HMAC',await key(secret),new TextEncoder().encode(encoded));return encoded+'.'+Buffer.from(signature).toString('base64url');}
async function verify(value,secret){try{const [encoded,signature]=value.split('.');if(!encoded || !signature || !await crypto.subtle.verify('HMAC',await key(secret),Buffer.from(signature,'base64url'),new TextEncoder().encode(encoded)))return null;return JSON.parse(Buffer.from(encoded,'base64url'));}catch{return null;}}
export async function login(request,env,store){
 if(!authReady(env))return Response.json({message:'GitHubログインの初期設定が未完了です'},{status:503});
 const url=new URL(request.url),ip=hash((request.headers.get('cf-connecting-ip') || 'unknown')+env.SESSION_SECRET);
 const attempts=await store.first('INSERT INTO attempts VALUES(?,1,?) ON CONFLICT(ip) DO UPDATE SET count=CASE WHEN attempts.expires<? THEN 1 ELSE attempts.count+1 END,expires=CASE WHEN attempts.expires<? THEN excluded.expires ELSE attempts.expires END RETURNING count',ip,Date.now()+60000,Date.now(),Date.now());
 if(attempts.count>10)return Response.json({message:'ログイン試行が多すぎます。しばらくお待ちください'},{status:429});
 const state={nonce:random(),expires:Date.now()+600000,origin:url.origin};
 const target=new URL('https://github.com/login/oauth/authorize');target.search=new URLSearchParams({client_id:env.GITHUB_OAUTH_CLIENT_ID,redirect_uri:url.origin+'/auth/callback',state:state.nonce,scope:'read:user'});
 return new Response(null,{status:302,headers:{Location:target.href,'Set-Cookie':`__Host-bantai-state=${await sign(state,env.SESSION_SECRET)}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=600`}});
}
export async function callback(request,env,store,fetcher=fetch){
 if(!authReady(env))return Response.json({message:'ログイン設定が未完了です'},{status:503});
 const url=new URL(request.url),state=await verify(cookie(request,'__Host-bantai-state'),env.SESSION_SECRET);
 if(!state || state.origin!==url.origin || state.expires<Date.now() || state.nonce!==url.searchParams.get('state') || !url.searchParams.get('code'))return Response.json({message:'ログインの照合に失敗しました。最初からやり直してください'},{status:403});
 const tokenResponse=await fetcher('https://github.com/login/oauth/access_token',{method:'POST',headers:{Accept:'application/json','Content-Type':'application/json','User-Agent':'BanTaiAdminCenter'},body:JSON.stringify({client_id:env.GITHUB_OAUTH_CLIENT_ID,client_secret:env.GITHUB_OAUTH_CLIENT_SECRET,code:url.searchParams.get('code'),redirect_uri:url.origin+'/auth/callback'}),redirect:'error'});
 const token=await tokenResponse.json();if(!tokenResponse.ok || !token.access_token)return Response.json({message:'GitHubログインに失敗しました'},{status:401});
 const userResponse=await fetcher('https://api.github.com/user',{headers:{Authorization:'Bearer '+token.access_token,Accept:'application/vnd.github+json','User-Agent':'BanTaiAdminCenter'},redirect:'error'}),user=await userResponse.json();
 if(!userResponse.ok || typeof user.login!=='string' || user.login.toLowerCase()!==env.ADMIN_GITHUB_LOGIN.toLowerCase())return Response.json({message:'このGitHubアカウントには管理権限がありません'},{status:403});
 const raw=random(),csrf=random();await store.run('INSERT INTO sessions VALUES(?,?,?)',hash(raw),csrf,Date.now()+28800000);await store.event('session.login',{});
 const headers=new Headers({Location:'/', 'Cache-Control':'no-store'});headers.append('Set-Cookie',sessionCookie(raw));headers.append('Set-Cookie','__Host-bantai-state=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0');return new Response(null,{status:303,headers});
}
