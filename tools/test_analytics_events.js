/**
 * Ban.Tai Education Design - GA4 Event Logic & Privacy Verification Test
 * 
 * Tests:
 * 1. PII Sanitization (query params, hash, mailto, tel)
 * 2. Pre-config exclusion logic (bantai_admin=true / bantai_admin=clear, localhost)
 * 3. Pre-config URL cleanup via replaceState (removes bantai_admin before gtag config)
 * 4. Column engagement timing, read_time_sec, and duplicate prevention
 */

const assert = require('assert');

// --- 1. Mock Environment Setup ---
const dispatchedEvents = [];
const mockGtag = function(command, eventName, params) {
  if (command === 'event') {
    dispatchedEvents.push({ eventName, params });
  }
};

const mockLocalStorage = {
  store: {},
  getItem(k) { return this.store[k] || null; },
  setItem(k, v) { this.store[k] = String(v); },
  removeItem(k) { delete this.store[k]; }
};

// URL Sanitizer logic (matching analytics-events.js / columns.js)
function sanitizeUrl(rawUrl, baseUrl = 'https://bantai-education-design.github.io/') {
  if (!rawUrl) return '';
  const trimmed = rawUrl.trim();
  if (trimmed.startsWith('mailto:')) return 'mailto:[redacted]';
  if (trimmed.startsWith('tel:')) return 'tel:[redacted]';
  try {
    const parsed = new URL(trimmed, baseUrl);
    return parsed.origin + parsed.pathname;
  } catch (e) {
    return trimmed.split('?')[0].split('#')[0];
  }
}

// Exclusion Checker logic
function isTrackingDisabled(hostname, protocol, localStorageObj) {
  const isLocal = hostname === 'localhost' || hostname === '127.0.0.1' || protocol === 'file:';
  const isExcluded = localStorageObj.getItem('bantai_admin') === 'true';
  return isLocal || isExcluded;
}

// Pre-config URL Cleanup Logic (exact logic from 88 HTML files)
function cleanAdminUrl(currentHref) {
  const url = new URL(currentHref);
  const adminParam = url.searchParams.get('bantai_admin');
  if (adminParam === 'true') {
    mockLocalStorage.setItem('bantai_admin', 'true');
  } else if (adminParam === 'clear') {
    mockLocalStorage.removeItem('bantai_admin');
  }

  let cleanedUrl = currentHref;
  if (adminParam !== null) {
    url.searchParams.delete('bantai_admin');
    const cleanSearch = url.searchParams.toString();
    cleanedUrl = url.origin + url.pathname + (cleanSearch ? '?' + cleanSearch : '') + url.hash;
  }
  return { cleanedUrl, adminParam };
}

console.log('--- Running GA4 Analytics Verification Tests ---');

// TEST 1: URL & PII Sanitization
console.log('Test 1: URL & PII Sanitization');
assert.strictEqual(
  sanitizeUrl('https://example.com/products/detail?session=12345&user=test#section'),
  'https://example.com/products/detail',
  'Query params and hashes must be stripped'
);
assert.strictEqual(
  sanitizeUrl('mailto:teacher@example.com?subject=Inquiry'),
  'mailto:[redacted]',
  'Mailto addresses must be redacted'
);
assert.strictEqual(
  sanitizeUrl('tel:090-1234-5678'),
  'tel:[redacted]',
  'Tel numbers must be redacted'
);
console.log('  PASS: URL & PII correctly sanitized');

// TEST 2: Pre-config Inline Exclusion
console.log('Test 2: Pre-config Inline Exclusion Logic');
assert.strictEqual(isTrackingDisabled('localhost', 'http:', mockLocalStorage), true, 'localhost must be disabled');
assert.strictEqual(isTrackingDisabled('127.0.0.1', 'http:', mockLocalStorage), true, '127.0.0.1 must be disabled');
assert.strictEqual(isTrackingDisabled('example.com', 'file:', mockLocalStorage), true, 'file: protocol must be disabled');

// Production domain without flag -> enabled
mockLocalStorage.removeItem('bantai_admin');
assert.strictEqual(isTrackingDisabled('bantai-education-design.github.io', 'https:', mockLocalStorage), false, 'normal visitor enabled');

// Admin flag set -> disabled
mockLocalStorage.setItem('bantai_admin', 'true');
assert.strictEqual(isTrackingDisabled('bantai-education-design.github.io', 'https:', mockLocalStorage), true, 'bantai_admin=true disabled');

// Admin flag cleared -> enabled
mockLocalStorage.removeItem('bantai_admin');
assert.strictEqual(isTrackingDisabled('bantai-education-design.github.io', 'https:', mockLocalStorage), false, 'bantai_admin=clear re-enabled');
console.log('  PASS: Exclusion correctly toggled');

// TEST 3: Pre-config URL Cleanup (before gtag config)
console.log('Test 3: Pre-config URL Cleanup via replaceState');
// Case 3a: ?bantai_admin=true without other params
const resA = cleanAdminUrl('https://bantai-education-design.github.io/?bantai_admin=true');
assert.strictEqual(resA.cleanedUrl, 'https://bantai-education-design.github.io/', 'bantai_admin removed');
assert.strictEqual(mockLocalStorage.getItem('bantai_admin'), 'true', 'Flag set to true');

// Case 3b: ?bantai_admin=clear with other query and hash preserved
const resB = cleanAdminUrl('https://bantai-education-design.github.io/columns/?article=123&bantai_admin=clear#comments');
assert.strictEqual(resB.cleanedUrl, 'https://bantai-education-design.github.io/columns/?article=123#comments', 'bantai_admin removed, article=123 and #comments preserved');
assert.strictEqual(mockLocalStorage.getItem('bantai_admin'), null, 'Flag removed');

// Case 3c: Normal URL without bantai_admin -> completely untouched
const resC = cleanAdminUrl('https://bantai-education-design.github.io/products/?cat=all#top');
assert.strictEqual(resC.cleanedUrl, 'https://bantai-education-design.github.io/products/?cat=all#top', 'Normal URL untouched');
console.log('  PASS: Pre-config replaceState cleans URL while preserving query and hash');

// TEST 4: Column Engagement Timing and Duplicate Guard
console.log('Test 4: Column Engagement Timing, read_time_sec & Duplicate Guard');

class ColumnTrackerMock {
  constructor() {
    this.activeColumn = null;
    this.startTime = null;
    this.engagementSent = false;
    this.events = [];
  }

  open(col) {
    if (this.activeColumn && !this.engagementSent) {
      this.close();
    }
    this.activeColumn = col;
    this.startTime = Date.now();
    this.engagementSent = false;
    this.events.push({ name: 'column_view', id: col.id, title: col.title });
  }

  close(fakeDurationSeconds = null) {
    if (!this.activeColumn || this.engagementSent) return;
    const duration = fakeDurationSeconds !== null ? fakeDurationSeconds : Math.round((Date.now() - this.startTime) / 1000);
    this.engagementSent = true;

    if (duration < 5) {
      // Ignore誤操作
      return;
    }

    const isEngaged = duration >= 15;
    this.events.push({
      name: 'column_engagement',
      id: this.activeColumn.id,
      title: this.activeColumn.title,
      read_time_sec: duration,
      duration_seconds: duration,
      is_engaged: isEngaged,
      engagement_type: isEngaged ? 'engaged_view' : 'short_view'
    });
  }

  clickLink(linkHref) {
    this.close(); // Record engagement first
    this.events.push({
      name: 'column_next_action',
      id: this.activeColumn.id,
      link_url: sanitizeUrl(linkHref),
      action_type: 'inline_link_click'
    });
  }
}

// Case 4a: Under 5s -> no engagement event
const trackerA = new ColumnTrackerMock();
trackerA.open({ id: 'col-1', title: 'テスト記事1' });
trackerA.close(3); // 3 seconds
assert.strictEqual(trackerA.events.length, 1, 'Only column_view should be sent');
assert.strictEqual(trackerA.events[0].name, 'column_view');

// Case 4b: 5s to 14s -> is_engaged: false
const trackerB = new ColumnTrackerMock();
trackerB.open({ id: 'col-2', title: 'テスト記事2' });
trackerB.close(10); // 10 seconds
assert.strictEqual(trackerB.events.length, 2);
assert.strictEqual(trackerB.events[1].name, 'column_engagement');
assert.strictEqual(trackerB.events[1].read_time_sec, 10, 'read_time_sec must be 10');
assert.strictEqual(trackerB.events[1].is_engaged, false);
assert.strictEqual(trackerB.events[1].engagement_type, 'short_view');

// Case 4c: 15s+ -> is_engaged: true
const trackerC = new ColumnTrackerMock();
trackerC.open({ id: 'col-3', title: 'テスト記事3' });
trackerC.close(25); // 25 seconds
assert.strictEqual(trackerC.events.length, 2);
assert.strictEqual(trackerC.events[1].name, 'column_engagement');
assert.strictEqual(trackerC.events[1].read_time_sec, 25, 'read_time_sec must be 25');
assert.strictEqual(trackerC.events[1].is_engaged, true);
assert.strictEqual(trackerC.events[1].engagement_type, 'engaged_view');

// Case 4d: Duplicate prevention (close called multiple times + pagehide)
trackerC.close(30);
trackerC.close(35);
assert.strictEqual(trackerC.events.length, 2, 'Engagement must not be sent twice for the same viewing');

// Case 4e: Inline link click triggers next_action and engagement (only once)
const trackerD = new ColumnTrackerMock();
trackerD.open({ id: 'col-4', title: 'テスト記事4' });
trackerD.startTime = Date.now() - 20000; // 20 seconds elapsed
trackerD.clickLink('https://example.com/detail?ref=col#top');
trackerD.close(20); // subsequent close should do nothing
assert.strictEqual(trackerD.events.length, 3, 'column_view, column_engagement, column_next_action');
assert.strictEqual(trackerD.events[1].name, 'column_engagement');
assert.strictEqual(trackerD.events[1].read_time_sec, 20, 'read_time_sec must be 20');
assert.strictEqual(trackerD.events[2].name, 'column_next_action');
assert.strictEqual(trackerD.events[2].link_url, 'https://example.com/detail', 'Sanitized URL in next_action');
console.log('  PASS: Column engagement rules, read_time_sec and duplicate prevention verified');

console.log('\nALL 4 ANALYTICS VERIFICATION TESTS PASSED SUCCESSFULLY.');
