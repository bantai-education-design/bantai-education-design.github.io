import {randomUUID} from 'node:crypto';
const now=()=>new Date().toISOString();
const failure=(message,status)=>Object.assign(Error(message),{status});
export class D1Store {
  constructor(db){this.db=db;}
  statement(sql,...args){return this.db.prepare(sql).bind(...args);}
  async first(sql,...args){return this.statement(sql,...args).first();}
  async all(sql,...args){return (await this.statement(sql,...args).all()).results;}
  async run(sql,...args){return this.statement(sql,...args).run();}
  async event(kind,detail){await this.run('INSERT INTO events(kind,detail,created) VALUES(?,?,?)',kind,JSON.stringify(detail),now());}
  eventStatement(kind,detail){return this.statement('INSERT INTO events(kind,detail,created) VALUES(?,?,?)',kind,JSON.stringify(detail),now());}
  async get(id){const r=await this.first('SELECT * FROM articles WHERE id=?',id);return r?{id:r.id,revision:r.revision,...JSON.parse(r.body)}:null;}
  async list(){return (await this.all('SELECT * FROM articles ORDER BY rowid DESC')).map(r=>({id:r.id,revision:r.revision,...JSON.parse(r.body)}));}
  async origin(id){const r=await this.first('SELECT body FROM origins WHERE article_id=?',id);return r?JSON.parse(r.body):null;}
  async save(id,revision,body,origin=null){
    const old=id?await this.get(id):null;
    if(id && !old)throw failure('記事がありません',404);
    if(old && old.revision!==revision)throw failure('別の画面で更新されています。本文を保護してから再読込してください',409);
    id ||= randomUUID();const next=(old?.revision || 0)+1,json=JSON.stringify(body),created=now();
    const statements=old?
      [this.statement('UPDATE articles SET revision=?,body=? WHERE id=? AND revision=?',next,json,id,revision)]:
      [this.statement('INSERT INTO articles VALUES(?,?,?)',id,next,json)];
    statements.push(this.statement('INSERT INTO versions(article_id,revision,body,created) SELECT id,revision,body,? FROM articles WHERE id=? AND revision=? AND changes()=1',created,id,next));
    statements.push(this.statement('INSERT INTO events(kind,detail,created) SELECT ?,?,? WHERE changes()=1','draft.saved',JSON.stringify({id,revision:next}),created));
    if(origin){
      const source=JSON.stringify(origin);if(source.length>1500000)throw failure('原本が無料保存領域の1レコード上限を超えます',413);
      statements.push(this.statement('INSERT INTO origins VALUES(?,?,?)',id,origin.entry.id,source));statements.push(this.eventStatement('legacy.imported',{id,catalogId:origin.entry.id}));
    }
    const result=await this.db.batch(statements);
    if(!result[0].meta.changes)throw failure('編集が競合しました。本文を保護してください',409);
    return this.get(id);
  }
  async versions(id){return this.all('SELECT revision,created FROM versions WHERE article_id=? ORDER BY revision DESC',id);}
  async restore(id,revision,target){const v=await this.first('SELECT body FROM versions WHERE article_id=? AND revision=?',id,target);if(!v)throw failure('復元元がありません',404);const a=await this.save(id,revision,JSON.parse(v.body));await this.event('draft.restored',{id,from:target,to:a.revision});return a;}
  async importLegacy(catalogId,origin,body,fresh=false){const existing=await this.first('SELECT article_id FROM origins WHERE catalog_id=? ORDER BY rowid DESC LIMIT 1',catalogId);if(existing&&!fresh)return this.get(existing.article_id);return this.save(null,0,body,origin);}
  async requests(){return this.all('SELECT * FROM requests ORDER BY rowid DESC');}
  async history(){return (await this.all('SELECT * FROM events ORDER BY id DESC LIMIT 200')).map(r=>({...r,detail:JSON.parse(r.detail)}));}
  async recordRequest(r,baseline,kind='publication.requested'){
    const statements=[this.statement('INSERT INTO requests VALUES(?,?,?,?,?,?,?)',r.id,r.article_id,r.revision,r.action,r.url,r.number,r.state),this.eventStatement(kind,r)];
    if(baseline)statements.push(this.statement('INSERT INTO request_results VALUES(?,?)',r.id,JSON.stringify(baseline)));
    await this.db.batch(statements);
  }
  async updateRequestState(r,state){
    const statements=[this.statement('UPDATE requests SET state=? WHERE id=?',state,r.id),this.eventStatement('publication.'+state,{url:r.url,article_id:r.article_id,revision:r.revision,action:r.action})];
    const origin=r.article_id?await this.origin(r.article_id):null;
    if(state==='merged' && origin){const result=await this.first('SELECT body FROM request_results WHERE request_id=?',r.id);if(result){Object.assign(origin,JSON.parse(result.body));statements.push(this.statement('UPDATE origins SET body=? WHERE article_id=?',JSON.stringify(origin),r.article_id));}}
    await this.db.batch(statements);
  }
  async acquireLock(){const owner=randomUUID();const r=await this.first("INSERT INTO locks VALUES('publication',?,?) ON CONFLICT(name) DO UPDATE SET owner=excluded.owner,expires=excluded.expires WHERE locks.expires<? RETURNING owner",owner,Date.now()+900000,Date.now());if(!r)throw failure('公開処理中です。完了後に再試行してください',409);return ()=>this.run("DELETE FROM locks WHERE name='publication' AND owner=?",owner);}
  async putImage(path,mime,data){
    const exists=await this.first('SELECT path FROM images WHERE path=?',path);if(exists)return;
    const parts=[];for(let start=0;start<data.byteLength;start+=1000000)parts.push(data.slice(start,start+1000000));
    const statements=[this.statement('INSERT OR IGNORE INTO images VALUES(?,?,?)',path,mime,data.byteLength)];
    parts.forEach((part,i)=>statements.push(this.statement('INSERT OR IGNORE INTO image_chunks VALUES(?,?,?)',path,i,part.buffer.slice(part.byteOffset,part.byteOffset+part.byteLength))));
    statements.push(this.eventStatement('image.uploaded',{path}));await this.db.batch(statements);
  }
  async getImage(path){const rows=await this.all('SELECT c.data,i.mime,i.size FROM image_chunks c JOIN images i ON i.path=c.path WHERE c.path=? ORDER BY c.part',path);if(!rows.length)throw failure('画像がありません',404);const data=new Uint8Array(rows[0].size);let position=0;for(const r of rows){const part=new Uint8Array(r.data);data.set(part,position);position+=part.length;}return {data,mime:rows[0].mime};}
}
