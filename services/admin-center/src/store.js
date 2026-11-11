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
      CREATE TABLE IF NOT EXISTS proposals(id TEXT PRIMARY KEY, body TEXT NOT NULL, created TEXT NOT NULL);`);
  }
  event(kind, detail) {this.db.prepare('INSERT INTO events(kind,detail,created) VALUES(?,?,?)').run(kind,JSON.stringify(detail),new Date().toISOString());}
  list() {return this.db.prepare('SELECT * FROM articles ORDER BY rowid DESC').all().map(r => ({id:r.id,revision:r.revision,...JSON.parse(r.body)}));}
  get(id) {const r = this.db.prepare('SELECT * FROM articles WHERE id=?').get(id); return r ? {id:r.id,revision:r.revision,...JSON.parse(r.body)} : null;}
  save(id, revision, body) {
    const now = new Date().toISOString();
    this.db.exec('BEGIN IMMEDIATE');
    try {
      const old = id ? this.get(id) : null;
      if (id && !old) throw Object.assign(Error('記事が見つかりません'),{status:404});
      if (old && old.revision !== revision) throw Object.assign(Error('別の画面で更新されています。再読込前に本文をコピーしてください'),{status:409});
      id ||= randomUUID(); const rev = (old?.revision || 0) + 1;
      this.db.prepare('INSERT INTO articles VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET revision=excluded.revision,body=excluded.body').run(id,rev,JSON.stringify(body));
      this.db.prepare('INSERT INTO versions(article_id,revision,body,created) VALUES(?,?,?,?)').run(id,rev,JSON.stringify(body),now);
      this.event('draft.saved',{id,revision:rev}); this.db.exec('COMMIT'); return this.get(id);
    } catch(e) {this.db.exec('ROLLBACK');throw e;}
  }
  versions(id) {return this.db.prepare('SELECT revision,created FROM versions WHERE article_id=? ORDER BY revision DESC').all(id);}
  restore(id, revision, target) {
    const v = this.db.prepare('SELECT body FROM versions WHERE article_id=? AND revision=?').get(id,target);
    if(!v) throw Object.assign(Error('復元元がありません'),{status:404});
    const result = this.save(id,revision,JSON.parse(v.body)); this.event('draft.restored',{id,from:target,to:result.revision}); return result;
  }
  requests() {return this.db.prepare('SELECT * FROM requests ORDER BY rowid DESC').all();}
  history() {return this.db.prepare('SELECT * FROM events ORDER BY id DESC LIMIT 200').all().map(r=>({...r,detail:JSON.parse(r.detail)}));}
}
