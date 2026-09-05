const assert = require('node:assert/strict');
const publish = require('./publish.js');

process.env.OWNER_PUBLISH_KEY = 'test-owner-key';
process.env.OWNER_PUBLISH_GITHUB_TOKEN = 'test-github-token';
process.env.OWNER_PUBLISH_ALLOWED_ORIGIN = 'https://bantai-education-design.github.io';

const json = (status, body) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
const requestId = '12345678-1234-1234-1234-123456789abc';

async function statusFor(mode) {
  global.fetch = async url => {
    const value = String(url);
    if (value.includes('/branches/main/protection')) {
      return mode === 'review' ? json(404, { message: 'Not Found' }) : json(200, { required_status_checks: { contexts: ['owner-overlap'] } });
    }
    if (value.includes('/rules/branches/main')) return json(404, { message: 'Not Found' });
    if (value.includes('/pulls?')) return json(200, [{
      number: 7,
      html_url: 'https://example.test/pull/7',
      merged_at: mode === 'merged' ? '2026-09-05T00:00:00Z' : null,
      auto_merge: mode === 'review' ? null : { enabled_at: '2026-09-05T00:00:00Z' },
      head: { sha: 'owner-head-sha' }
    }]);
    if (value.includes('/actions/runs?head_sha=owner-head-sha')) return json(200, { workflow_runs: [{ id: 88, name: 'Owner photo publish', status: mode === 'running' ? 'in_progress' : 'completed', conclusion: null }] });
    if (value.includes('/actions/runs/88/jobs')) return json(200, { jobs: [{ name: 'owner-overlap', status: mode === 'running' ? 'in_progress' : 'completed', conclusion: mode === 'failed' ? 'failure' : mode === 'success' ? 'success' : null }] });
    throw new Error(`Unexpected GitHub API call: ${value}`);
  };
  const response = { setHeader() {}, status(code) { this.code = code; return this; }, json(body) { this.body = body; return this; }, end() {} };
  await publish({ method: 'GET', query: { university_id: 'u000094', request_id: requestId }, headers: { origin: 'https://bantai-education-design.github.io', 'x-owner-publish-key': 'test-owner-key' } }, response);
  assert.equal(response.code, 200);
  return response.body.publication_state;
}

(async () => {
  assert.equal(await statusFor('review'), 'review_required');
  assert.equal(await statusFor('failed'), 'ci_failed');
  assert.equal(await statusFor('running'), 'awaiting_merge');
  assert.equal(await statusFor('success'), 'awaiting_merge');
  assert.equal(await statusFor('merged'), 'merged');
  console.log('owner publish Actions API status tests passed');
})().catch(error => { console.error(error); process.exit(1); });
