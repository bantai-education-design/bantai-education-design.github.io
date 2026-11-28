import {DatabaseSync} from 'node:sqlite';
import {randomUUID} from 'node:crypto';
export class Store {
  constructor(path) {
    this.db = new DatabaseSync(path);
    this.db.exec(`PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;
      CREATE TABLE IF NOT EXISTS articles(id TEXT PRIMARY KEY, revision INTEGER NOT NULL, body TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS versions(id INTEGER PRIMARY KEY, article_id TEXT NOT NULL, revision INTEGER NOT NULL, body TEXT NOT NULL, created TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, kind TEXT NOT NULL, detail TEXT NOT NULL, created TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS sessions(hash TEXT PRIMARY KEY, csrf TEXT NOT NULL, expires INTEGER NOT NULL);
      CREATE TABLE IF NOT EXISTS attempts(ip TEXT PRIMARY KEY, count INTEGER NOT NULL, expires INTEGER NOT NULL);
      CREATE TABLE IF NOT EXISTS requests(id TEXT PRIMARY KEY, article_id TEXT, revision INTEGER, action TEXT NOT NULL, url TEXT NOT NULL, number INTEGER NOT NULL, state TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS origins(article_id TEXT PRIMARY KEY, catalog_id TEXT NOT NULL, body TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS request_results(request_id TEXT PRIMARY KEY, body TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS proposals(id TEXT PRIMARY KEY, body TEXT NOT NULL, created TEXT NOT NULL);`);
  }
  event(kind, detail) {this.db.prepare('INSERT INTO events(kind,detail,created) VALUES(?,?,?)').run(kind,JSON.stringify(detail),new Date().toISOString());}
  list() {return this.db.prepare('SELECT * FROM articles ORDER BY rowid DESC').all().map(r => ({id:r.id,revision:r.revision,...JSON.parse(r.body)}));}
  get(id) {const r = this.db.prepare('SELECT * FROM articles WHERE id=?').get(id); return r ? {id:r.id,revision:r.revision,...JSON.parse(r.body)} : null;}
  save(id, revision, body, origin=null) {
    const now = new Date().toISOString();
    this.db.exec('BEGIN IMMEDIATE');
    try {
      const old = id ? this.get(id) : null;
      if (id && !old) throw Object.assign(Error('記事が見つかりません'),{status:404});
      if (old && old.revision !== revision) throw Object.assign(Error('別の画面で更新されています。再読込前に本文をコピーしてください'),{status:409});
      id ||= randomUUID(); const rev = (old?.revision || 0) + 1;
      this.db.prepare('INSERT INTO articles VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET revision=excluded.revision,body=excluded.body').run(id,rev,JSON.stringify(body));
      this.db.prepare('INSERT INTO versions(article_id,revision,body,created) VALUES(?,?,?,?)').run(id,rev,JSON.stringify(body),now);
      if(origin){this.setOrigin(id,origin.entry.id,origin);this.event('legacy.imported',{id,catalogId:origin.entry.id});}
      this.event('draft.saved',{id,revision:rev}); this.db.exec('COMMIT'); return this.get(id);
    } catch(e) {this.db.exec('ROLLBACK');throw e;}
  }
  origin(id) {const r=this.db.prepare('SELECT body FROM origins WHERE article_id=?').get(id);return r?JSON.parse(r.body):null;}
  setOrigin(id,catalogId,origin) {this.db.prepare('INSERT INTO origins VALUES(?,?,?) ON CONFLICT(article_id) DO UPDATE SET body=excluded.body').run(id,catalogId,JSON.stringify(origin));}
  importLegacy(catalogId,origin,body,force=false) {
    const existing=this.db.prepare('SELECT article_id FROM origins WHERE catalog_id=? ORDER BY rowid DESC LIMIT 1').get(catalogId);
    if(existing && !force)return this.get(existing.article_id);
    return this.save(null,0,body,origin);
  }
  versions(id) {return this.db.prepare('SELECT revision,created FROM versions WHERE article_id=? ORDER BY revision DESC').all(id);}
  restore(id, revision, target) {
    const v = this.db.prepare('SELECT body FROM versions WHERE article_id=? AND revision=?').get(id,target);
    if(!v) throw Object.assign(Error('復元元がありません'),{status:404});
    const result = this.save(id,revision,JSON.parse(v.body)); this.event('draft.restored',{id,from:target,to:result.revision}); return result;
  }
  recordRequest(r,baseline,kind='publication.requested') {
    this.db.exec('BEGIN IMMEDIATE');
    try {
      this.db.prepare('INSERT INTO requests(id,article_id,revision,action,url,number,state) VALUES(?,?,?,?,?,?,?)').run(r.id,r.article_id,r.revision,r.action,r.url,r.number,r.state);
      if(baseline)this.db.prepare('INSERT INTO request_results VALUES(?,?)').run(r.id,JSON.stringify(baseline));
      this.event(kind,r);this.db.exec('COMMIT');
    }catch(e){this.db.exec('ROLLBACK');throw e;}
  }
  updateRequestState(r,state) {
    this.db.exec('BEGIN IMMEDIATE');
    try {
      this.db.prepare('UPDATE requests SET state=? WHERE id=?').run(state,r.id);
      const origin=r.article_id?this.origin(r.article_id):null;
      if(state==='merged' && origin) {
        const result=this.db.prepare('SELECT body FROM request_results WHERE request_id=?').get(r.id);
        if(result){Object.assign(origin,JSON.parse(result.body));this.setOrigin(r.article_id,origin.entry.id,origin);}
      }
      this.event('publication.'+state,{url:r.url,article_id:r.article_id,revision:r.revision,action:r.action});this.db.exec('COMMIT');
    }catch(e){this.db.exec('ROLLBACK');throw e;}
  }
  requests() {return this.db.prepare('SELECT * FROM requests ORDER BY rowid DESC').all();}
  history() {return this.db.prepare('SELECT * FROM events ORDER BY id DESC LIMIT 200').all().map(r=>({...r,detail:JSON.parse(r.detail)}));}
}
