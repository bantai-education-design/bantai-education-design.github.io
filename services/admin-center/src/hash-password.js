// Enter the password locally, never in chat, a shell argument, or source files.
import {createInterface} from 'node:readline';
import {Writable} from 'node:stream';
import {writeFileSync} from 'node:fs';
import {resolve,sep,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {passwordHash} from './server.js';
const dest=process.argv[2],root=resolve(dirname(fileURLToPath(import.meta.url)),'../../..');
if(!dest || !process.stdin.isTTY) throw Error('TTYでリポジトリ外の保存先を指定してください');
if(resolve(dest)===root || resolve(dest).startsWith(root+sep)) throw Error('保存先はリポジトリ外にしてください');
const output=new Writable({write(_chunk,_encoding,done){done();}});
const rl=createInterface({input:process.stdin,output,terminal:true});
process.stderr.write('管理パスワード（16文字以上、表示しません）: ');
rl.question('',value=>{
  rl.close();process.stderr.write('\n');
  if(value.length<16)throw Error('16文字以上にしてください');
  writeFileSync(resolve(dest),passwordHash(value)+'\n',{mode:0o600,flag:'wx'});
  process.stderr.write('ハッシュを指定ファイルへ保存しました。秘密設定へ登録してください。\n');
});
