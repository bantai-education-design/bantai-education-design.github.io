import {readFileSync,realpathSync,statSync} from 'node:fs';
import {resolve,isAbsolute,sep,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../../..');
function secret(name,env) {
  const value=env[name],file=env[name+'_FILE'];
  if(value && file)throw Error(`${name}と${name}_FILEは同時に設定できません`);
  if(!file)return value || undefined;
  if(!isAbsolute(file))throw Error(`${name}_FILEはリポジトリ外の絶対パスにしてください`);
  const real=realpathSync(file);
  if(real===root || real.startsWith(root+sep))throw Error(`${name}_FILEは公開リポジトリ外に配置してください`);
  if(!statSync(real).isFile() || statSync(real).size>16384)throw Error(`${name}_FILEのサイズが不正です`);
  return readFileSync(real,'utf8').trim() || undefined;
}
export function runtimeConfig(env=process.env) {
  if(!env.ADMIN_DATA_DIR || !isAbsolute(env.ADMIN_DATA_DIR))throw Error('ADMIN_DATA_DIRは永続ディスクの絶対パスを設定してください');
  const development=env.ADMIN_DEV_HTTP==='1',host=env.ADMIN_BIND_HOST || '127.0.0.1';
  if(!['127.0.0.1','0.0.0.0','::1'].includes(host) || (development && host==='0.0.0.0'))throw Error('ADMIN_BIND_HOSTが不正です。開発時はloopbackのみです');
  const port=Number(env.PORT || 8787);if(!Number.isInteger(port) || port<1 || port>65535)throw Error('PORTが不正です');
  return {origin:env.ADMIN_ORIGIN || (env.RENDER_EXTERNAL_URL?new URL(env.RENDER_EXTERNAL_URL).origin:undefined),dataDir:env.ADMIN_DATA_DIR,password:secret('ADMIN_PASSWORD_HASH',env),githubToken:secret('ADMIN_GITHUB_TOKEN',env),development,host,port};
}
