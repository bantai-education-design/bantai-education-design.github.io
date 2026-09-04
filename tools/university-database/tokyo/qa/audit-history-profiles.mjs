import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const tokyoDir = path.resolve(here, '..');
const dataDir = path.join(tokyoDir, 'data');
const profileDir = path.join(dataDir, 'verified_profiles');
const strict = process.env.TOKYO_HISTORY_EXPECT_COMPLETE === '1';

const requiredFields = [
  'founded_year',
  'opened_year',
  'founder',
  'operator',
  'university_goal',
  'philosophy',
  'sources',
];

const master = JSON.parse(
  fs.readFileSync(path.join(dataDir, 'universities_tokyo_all.generated.json'), 'utf8'),
);

if (!Array.isArray(master) || master.length !== 144) {
  throw new Error(`Expected 144 universities, got ${Array.isArray(master) ? master.length : 'non-array'}`);
}

const masterById = new Map(master.map((row) => [row.id, row]));
const profileFiles = fs
  .readdirSync(profileDir)
  .filter((name) => /^tokyo_history_batch\d+\.json$/.test(name))
  .sort((a, b) => {
    const an = Number(a.match(/batch(\d+)/)?.[1] ?? 0);
    const bn = Number(b.match(/batch(\d+)/)?.[1] ?? 0);
    return an - bn;
  });

if (profileFiles.length < 14) {
  throw new Error(`Expected at least 14 staged history profile batches, got ${profileFiles.length}`);
}
if (strict && profileFiles.length !== 29) {
  throw new Error(`Strict completion audit expected 29 history profile batches, got ${profileFiles.length}`);
}

const seen = new Map();
const problems = [];
const warnings = [];

for (const file of profileFiles) {
  const payload = JSON.parse(fs.readFileSync(path.join(profileDir, file), 'utf8'));
  const records = payload.records ?? {};

  for (const [id, record] of Object.entries(records)) {
    if (!masterById.has(id)) {
      problems.push(`${file}: unknown university id ${id}`);
      continue;
    }

    const previous = seen.get(id);
    if (previous) problems.push(`${id}: duplicate profile in ${previous} and ${file}`);
    seen.set(id, file);

    for (const field of requiredFields) {
      const value = record[field];
      if (value === undefined || value === null || value === '' || (Array.isArray(value) && value.length === 0)) {
        problems.push(`${file} ${id}: missing ${field}`);
      }
    }

    if (Array.isArray(record.sources)) {
      let primaryCount = 0;
      for (const [index, source] of record.sources.entries()) {
        for (const field of ['source_name', 'source_url', 'verified_at', 'role']) {
          if (!source?.[field]) problems.push(`${file} ${id}: source[${index}] missing ${field}`);
        }
        if (source?.role === 'primary' || source?.role === 'official-public') primaryCount += 1;
        else if (source?.role === 'secondary') warnings.push(`${file} ${id}: source[${index}] is secondary`);
        else if (source?.role) problems.push(`${file} ${id}: source[${index}] unexpected role ${source.role}`);
        if (source?.source_url && !/^https:\/\//.test(source.source_url)) {
          problems.push(`${file} ${id}: source[${index}] is not https: ${source.source_url}`);
        }
      }
      if (primaryCount === 0) problems.push(`${file} ${id}: no primary or official-public source`);
    }
  }
}

const allIds = master.map((row) => row.id);
const missing = allIds.filter((id) => !seen.has(id));
const privateIds = master.filter((row) => row.establishment_type === 'private').map((row) => row.id);
const missingPrivate = privateIds.filter((id) => !seen.has(id));
const coveredPrivate = privateIds.length - missingPrivate.length;

console.log(`Tokyo university master: ${master.length}`);
console.log(`History profile batches: ${profileFiles.length}`);
console.log(`Unique history profiles: ${seen.size}`);
console.log(`Private universities covered: ${coveredPrivate}/${privateIds.length}`);
console.log(`Missing profiles: ${missing.length}`);

if (missing.length) {
  console.log('Missing university profiles:');
  for (const id of missing) console.log(`- ${id} ${masterById.get(id)?.name ?? ''}`);
}

if (warnings.length) {
  console.warn('Audit warnings:');
  for (const warning of warnings) console.warn(`- ${warning}`);
}

if (strict && missing.length) {
  problems.push(`Strict completion audit: ${missing.length} university profiles are still missing`);
}

if (problems.length) {
  console.error('Audit problems:');
  for (const problem of problems) console.error(`- ${problem}`);
  process.exitCode = 1;
}
