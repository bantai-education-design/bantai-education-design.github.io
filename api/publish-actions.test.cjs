const assert = require('node:assert/strict');
const publish = require('./publish.js');

process.env.OWNER_PUBLISH_KEY = 'test-owner-key';
process.env.OWNER_PUBLISH_GITHUB_TOKEN = 'test-github-token';
process.env.OWNER_PUBLISH_ALLOWED_ORIGIN = 'https://bantai-education-design.github.io';

const json = (status, body) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
const requestId = '12345678-1234-1234-1234-123456789abc';

function mockResponse() {
  return {
    headers: {},
    setHeader(name, value) { this.headers[name.toLowerCase()] = value; },
    status(code) { this.code = code; return this; },
    json(body) { this.body = body; return this; },
    end() { this.ended = true; return this; }
  };
}

async function statusFor(mode, headers = {}) {
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
  const response = mockResponse();
  await publish({ method: 'GET', query: { university_id: 'u000094', request_id: requestId }, headers: { origin: 'https://bantai-education-design.github.io', 'x-owner-publish-key': 'test-owner-key', ...headers } }, response);
  assert.equal(response.code, 200);
  return response.body.publication_state;
}

async function request(method, headers = {}, query = {}) {
  const response = mockResponse();
  await publish({ method, query, headers }, response);
  return response;
}

(async () => {
  let response = await request('POST', { origin: 'https://bantai-education-design.github.io' });
  assert.equal(response.code, 401);
  assert.equal(response.headers['access-control-allow-origin'], 'https://bantai-education-design.github.io');

  response = await request('POST', { origin: 'https://evil.example' });
  assert.equal(response.code, 403);

  response = await request('POST', { host: 'bantai-education-design.github.io', 'x-forwarded-proto': 'https' });
  assert.equal(response.code, 401);
  assert.equal(response.headers['access-control-allow-origin'], 'https://bantai-education-design.github.io');

  response = await request('POST', { 'x-forwarded-host': 'bantai-education-design.github.io', 'x-forwarded-proto': 'https' });
  assert.equal(response.code, 401);
  assert.equal(response.headers['access-control-allow-origin'], 'https://bantai-education-design.github.io');

  response = await request('POST', { host: 'evil.example', 'x-forwarded-proto': 'https' });
  assert.equal(response.code, 403);

  assert.equal(await statusFor('review', { origin: undefined, host: 'bantai-education-design.github.io', 'x-forwarded-proto': 'https' }), 'review_required');

  response = await request('GET', { origin: 'https://bantai-education-design.github.io' }, { university_id: 'u000094', request_id: requestId });
  assert.equal(response.code, 401);

  assert.equal(await statusFor('review'), 'review_required');
  assert.equal(await statusFor('failed'), 'ci_failed');
  assert.equal(await statusFor('running'), 'awaiting_merge');
  assert.equal(await statusFor('success'), 'awaiting_merge');
  assert.equal(await statusFor('merged'), 'merged');
  console.log('owner publish Actions API status tests passed');
})().catch(error => { console.error(error); process.exit(1); });
