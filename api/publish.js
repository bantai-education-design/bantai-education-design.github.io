const crypto = require('node:crypto');
const sharp = require('sharp');

const REPOSITORY = process.env.OWNER_PUBLISH_REPOSITORY || 'bantai-education-design/bantai-education-design.github.io';
const REGISTRY_PATH = 'tools/university-database/tokyo/data/user-photo-overrides.json';
const UNIVERSITY_PATH = 'tools/university-database/tokyo/data/universities_tokyo_all.generated.json';
const IMAGE_PREFIX = 'tools/university-database/tokyo/assets/card-images/';
const MAX_PHOTOS = 9;
const MAX_IMAGE_BYTES = 2 * 1024 * 1024;
const MAX_TOTAL_BYTES = 10 * 1024 * 1024;
const IMAGE_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp']);

function reply(res, status, body) {
  res.status(status).json(body);
}

function cors(req, res) {
  const allowed = (process.env.OWNER_PUBLISH_ALLOWED_ORIGIN || 'https://bantai-education-design.github.io')
    .split(',').map(value => value.trim()).filter(Boolean);
  const origin = req.headers.origin;
  if (!origin || !allowed.includes(origin)) return false;
  res.setHeader('Access-Control-Allow-Origin', origin);
  res.setHeader('Vary', 'Origin');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-Owner-Publish-Key');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  return true;
}

function sameSecret(value, expected) {
  if (!value || !expected) return false;
  const left = Buffer.from(value);
  const right = Buffer.from(expected);
  return left.length === right.length && crypto.timingSafeEqual(left, right);
}

function github(path, options = {}) {
  const token = process.env.OWNER_PUBLISH_GITHUB_TOKEN;
  if (!token) throw new Error('GitHub publish credential is not configured');
  return fetch(`https://api.github.com/repos/${REPOSITORY}${path}`, {
    ...options,
    headers: {
      Accept: 'application/vnd.github+json',
      Authorization: `Bearer ${token}`,
      'X-GitHub-Api-Version': '2022-11-28',
      ...(options.headers || {})
    }
  }).then(async response => {
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      const error = new Error(body.message || `GitHub API request failed (${response.status})`);
      error.status = response.status;
      error.body = body;
      throw error;
    }
    return body;
  });
}

async function mainFile(path) {
  const file = await github(`/contents/${path}?ref=main`);
  if (Array.isArray(file) || file.encoding !== 'base64') throw new Error(`Unable to read ${path} from main`);
  return { sha: file.sha, text: Buffer.from(file.content.replace(/\n/g, ''), 'base64').toString('utf8') };
}

function parseJson(text, label) {
  try { return JSON.parse(text); } catch { throw new Error(`${label} is not valid JSON`); }
}

function contentFile(payload, path) {
  const file = (payload.files || []).find(item => item?.path === path);
  if (!file || file.encoding !== 'utf-8' || typeof file.content !== 'string') throw new Error(`Missing ${path}`);
  return file.content;
}

function requestId(value) {
  if (!/^[a-f0-9-]{16,64}$/i.test(String(value || ''))) throw new Error('Invalid publish request ID');
  return String(value).toLowerCase();
}

function imageFile(file, universityId) {
  if (!file || typeof file.path !== 'string' || file.encoding !== 'base64' || typeof file.content !== 'string') throw new Error('Invalid image file');
  if (!file.path.startsWith(`${IMAGE_PREFIX}${universityId}-`) || !file.path.endsWith('.jpg') || file.path.slice(IMAGE_PREFIX.length).includes('/') || file.path.includes('\\')) throw new Error('Image path is not allowed');
  if (file.content_type !== 'image/jpeg') throw new Error('Published card images must be JPEG');
  const bytes = Buffer.from(file.content, 'base64');
  if (!bytes.length || bytes.length > MAX_IMAGE_BYTES) throw new Error('Image file size is outside the allowed limit');
  return { ...file, bytes };
}

async function validateImages(files, universityId) {
  if (files.length > MAX_PHOTOS) throw new Error(`A maximum of ${MAX_PHOTOS} photos is allowed`);
  let total = 0;
  const seen = new Set();
  for (const raw of files) {
    const file = imageFile(raw, universityId);
    if (seen.has(file.path)) throw new Error('Duplicate image path');
    seen.add(file.path);
    total += file.bytes.length;
    if (total > MAX_TOTAL_BYTES) throw new Error('Total image size exceeds the allowed limit');
    const metadata = await sharp(file.bytes, { failOn: 'error', limitInputPixels: 40_000_000 }).metadata();
    if (!IMAGE_TYPES.has(metadata.format === 'jpeg' ? 'image/jpeg' : `image/${metadata.format}`)) throw new Error('Only JPEG, PNG, and WebP are accepted');
    if (metadata.format !== 'jpeg' || metadata.width !== 720 || metadata.height !== 405) throw new Error('Published card images must decode as 720×405 JPEG');
    await sharp(file.bytes, { failOn: 'error', limitInputPixels: 40_000_000 }).toBuffer();
  }
  return files.map(file => ({ path: file.path, bytes: Buffer.from(file.content, 'base64') }));
}

function validateRecord(record, universityId, newPaths) {
  if (record === null) return;
  if (!record || record.university_id !== universityId || record.rights_status !== 'verified' || record.rights_basis !== 'photographer_permission') throw new Error('Owner rights metadata is invalid');
  if (record.ai_redraw !== false || record.scene_integrity !== 'scene_unchanged') throw new Error('Only unaltered real-scene photos may be published');
  const photos = [record.image_url, ...(record.gallery || []).map(item => item?.image_url)];
  if (!record.image_url || !Array.isArray(record.gallery) || photos.length > MAX_PHOTOS || new Set(photos).size !== photos.length) throw new Error('Owner photo set is invalid');
  for (const path of photos) {
    if (typeof path !== 'string' || (!path.startsWith('assets/card-images/') && !newPaths.has(`tools/university-database/tokyo/${path}`))) throw new Error('Owner photo path is invalid');
  }
  for (const entry of [record, ...(record.gallery || [])]) {
    if (entry?.image_url?.startsWith('assets/card-images/') && !entry.source_url) throw new Error('Photo source metadata is missing');
  }
}

async function branchExists(branch) {
  try { await github(`/git/ref/heads/${branch}`); return true; }
  catch (error) { if (error.status === 404) return false; throw error; }
}

async function existingPull(branch) {
  const pulls = await github(`/pulls?state=open&head=${encodeURIComponent(`${REPOSITORY.split('/')[0]}:${branch}`)}`);
  return pulls[0] || null;
}

async function ownerPhotoPublish(req, res) {
  if (!cors(req, res)) return reply(res, 403, { ok: false, message: 'Origin is not permitted' });
  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return reply(res, 405, { ok: false, message: 'POST is required' });
  if (!sameSecret(req.headers['x-owner-publish-key'], process.env.OWNER_PUBLISH_KEY)) return reply(res, 401, { ok: false, message: 'Authorization failed' });

  try {
    const payload = req.body;
    if (!payload || payload.kind !== 'bantai_university_owner_publish' || payload.schema_version !== 1) throw new Error('Invalid publish payload');
    const universityId = String(payload.university_id || '');
    if (!/^u\d{6}$/.test(universityId)) throw new Error('University ID format is invalid');
    const id = requestId(payload.request_id);
    const branch = `owner-photo/${universityId}-${id}`;
    const oldPr = await existingPull(branch);
    if (oldPr) return reply(res, 200, { ok: true, duplicate: true, pull_request_url: oldPr.html_url, branch });

    const [universityFile, registryFile] = await Promise.all([mainFile(UNIVERSITY_PATH), mainFile(REGISTRY_PATH)]);
    const universities = parseJson(universityFile.text, 'University allowlist');
    const university = universities.find(item => item?.id === universityId);
    if (!university) throw new Error('University ID is not on the allowed list');
    const submittedRegistry = parseJson(contentFile(payload, REGISTRY_PATH), 'Submitted registry');
    const submittedRecord = submittedRegistry?.records?.[universityId] || null;
    const currentRegistry = parseJson(registryFile.text, 'Current registry');
    const baseRecord = payload.manifest?.base_owner_record ?? null;
    if (JSON.stringify(currentRegistry?.records?.[universityId] || null) !== JSON.stringify(baseRecord)) throw new Error('This university photo set changed. Reload the page before publishing.');
    const imageInputs = (payload.files || []).filter(file => typeof file?.path === 'string' && file.path.startsWith(IMAGE_PREFIX));
    const images = await validateImages(imageInputs, universityId);
    const newPaths = new Set(images.map(file => file.path));
    validateRecord(submittedRecord, universityId, newPaths);
    if (submittedRecord?.university_name !== university.name || payload.university_name !== university.name) throw new Error('University name does not match the allowlist');
    if (!submittedRecord && images.length) throw new Error('Images require an owner photo record');

    const currentRecords = { ...(currentRegistry.records || {}) };
    if (submittedRecord) currentRecords[universityId] = submittedRecord;
    else delete currentRecords[universityId];
    const nextRegistry = { ...currentRegistry, records: currentRecords };
    const mainRef = await github('/git/ref/heads/main');
    const mainCommit = await github(`/git/commits/${mainRef.object.sha}`);
    const blobs = await Promise.all(images.map(file => github('/git/blobs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ content: file.bytes.toString('base64'), encoding: 'base64' }) })));
    const registryBlob = await github('/git/blobs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ content: `${JSON.stringify(nextRegistry, null, 2)}\n`, encoding: 'utf-8' }) });
    const tree = await github('/git/trees', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ base_tree: mainCommit.tree.sha, tree: [...images.map((file, index) => ({ path: file.path, mode: '100644', type: 'blob', sha: blobs[index].sha })), { path: REGISTRY_PATH, mode: '100644', type: 'blob', sha: registryBlob.sha }] }) });
    const commit = await github('/git/commits', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: `feat(owner-photo): update ${university.name} photo set`, tree: tree.sha, parents: [mainRef.object.sha] }) });
    if (await branchExists(branch)) throw new Error('A publish request with this ID is already being created');
    await github('/git/refs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ref: `refs/heads/${branch}`, sha: commit.sha }) });
    const pull = await github('/pulls', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: `Owner photo publish: ${university.name}`, head: branch, base: 'main', draft: true, body: `Automated owner-photo publication request.\n\n- University: ${university.name} (${universityId})\n- Photos: ${submittedRecord ? 1 + submittedRecord.gallery.length : 0}\n- Request ID: ${id}\n- No AI-generated image content.\n\nThis draft must remain unmerged until all required CI checks pass and a human reviews it.` }) });
    return reply(res, 201, { ok: true, branch, pull_request_url: pull.html_url, pull_request_number: pull.number });
  } catch (error) {
    console.error('owner photo publish failed', error);
    return reply(res, 400, { ok: false, message: error.message || 'Publish failed. The public database was not changed.' });
  }
}

module.exports = ownerPhotoPublish;
module.exports.config = { api: { bodyParser: { sizeLimit: '14mb' } } };
