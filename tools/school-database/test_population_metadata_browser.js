const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const outDir = path.join(process.env.LOCALAPPDATA || process.env.TEMP, "remove-tokyo-card-visible-link");
const baseUrl = process.env.SCHOOL_DATABASE_BASE_URL || "http://127.0.0.1:8765";
const widths = [1280, 1024, 768, 375];

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

async function gotoPortal(page) {
  const response = await page.goto(`${baseUrl}/tools/school-database/`, { waitUntil: "networkidle" });
  assert(response && response.status() === 200, `HTTP ${response && response.status()}`);
  await page.waitForFunction(() => document.querySelectorAll(".pref-card.prefecture-card").length === 47);
}

async function verifyCardBasics(page) {
  const audit = await page.evaluate(() => {
    const cards = [...document.querySelectorAll(".pref-card.prefecture-card")];
    return {
      count: cards.length,
      first: {
        tag: cards[0]?.tagName,
        role: cards[0]?.getAttribute("role"),
        tabIndex: cards[0]?.tabIndex,
        dataCardHref: cards[0]?.dataset.cardHref || "",
        visibleLinkCount: cards[0]?.querySelectorAll("a[href]").length || 0,
        populationLinkCount: cards[0]?.querySelectorAll(".population-card-link").length || 0,
        detailsCount: cards[0]?.querySelectorAll(".population-age-details").length || 0,
        metaRows: cards[0]?.querySelectorAll(".pref-meta-grid .meta-row").length || 0,
        hasPopulation: Boolean(cards[0]?.querySelector(".population-summary")),
        text: cards[0]?.innerText || "",
      },
      allHaveHref: cards.every((card) => Boolean(card.matches("a[href]") ? card.getAttribute("href") : card.dataset.cardHref)),
      populationCards: cards.filter((card) => card.querySelector(".population-summary")).length,
      disabledButtons: cards.reduce((sum, card) => sum + card.querySelectorAll("button[disabled]").length, 0),
      schoolMetaRows: cards.map((card) => card.querySelectorAll(".pref-meta-grid .meta-row").length),
      lastHref: cards[cards.length - 1]?.matches("a[href]") ? cards[cards.length - 1].getAttribute("href") : "",
      bodyText: document.body.innerText,
    };
  });

  assert(audit.count === 47, `expected 47 cards, got ${audit.count}`);
  assert(audit.first.tag === "ARTICLE", `Tokyo card should stay article, got ${audit.first.tag}`);
  assert(audit.first.role === "link", `Tokyo card should expose link role, got ${audit.first.role}`);
  assert(audit.first.tabIndex === 0, `Tokyo card should be focusable, got tabIndex ${audit.first.tabIndex}`);
  assert(audit.first.dataCardHref === "/tools/school-database/tokyo/", `unexpected Tokyo data-card-href: ${audit.first.dataCardHref}`);
  assert(audit.first.visibleLinkCount === 0, `Tokyo visible links should be removed, got ${audit.first.visibleLinkCount}`);
  assert(audit.first.populationLinkCount === 0, "population-card-link should not exist");
  assert(audit.first.detailsCount === 1, "Tokyo details should remain");
  assert(audit.first.metaRows === 4, "Tokyo school database rows should remain");
  assert(audit.first.hasPopulation === true, "Tokyo population summary should remain");
  assert(audit.allHaveHref, "every card should keep a link target via href or data-card-href");
  assert(audit.populationCards === 1, `population should render only on Tokyo, got ${audit.populationCards}`);
  assert(audit.disabledButtons === 0, "disabled transition button remains");
  assert(audit.schoolMetaRows.every((count) => count === 4), "every card should keep 4 school metadata rows");
  assert(audit.lastHref === "/tools/school-database/okinawa/", `unexpected last card href: ${audit.lastHref}`);

  for (const prohibited of [
    "詳しく見る",
    "東京都の学校データベースを開く",
    "全国他都道府県",
    "準備中",
    "順次拡張予定",
    "順次追加予定",
  ]) {
    assert(!audit.bodyText.includes(prohibited), `prohibited visible text remains: ${prohibited}`);
  }
}

async function verifyTokyoDetails(page, width, capture) {
  const card = page.locator(".pref-card.prefecture-card").first();
  const summary = card.locator("summary");
  const details = card.locator(".population-age-details");
  const beforeUrl = page.url();
  const closedHeight = await card.evaluate((element) => Math.round(element.getBoundingClientRect().height));

  if (capture) {
    await card.screenshot({ path: path.join(outDir, `tokyo-card-closed-${width}.png`) });
  }

  await summary.click();
  assert(page.url() === beforeUrl, "summary click navigated unexpectedly");
  assert(await details.evaluate((element) => element.open) === true, "summary click should open details");

  const audit = await card.evaluate((element) => {
    const detailsElement = element.querySelector(".population-age-details");
    const text = detailsElement.innerText;
    const cardBox = element.getBoundingClientRect();
    const nodes = [...detailsElement.querySelectorAll("summary, dt, dd, p")].map((node) => {
      const rect = node.getBoundingClientRect();
      const style = getComputedStyle(node);
      return {
        top: rect.top,
        bottom: rect.bottom,
        left: rect.left,
        right: rect.right,
        height: rect.height,
        display: style.display,
        visibility: style.visibility,
      };
    });
    return {
      open: detailsElement.open,
      dtCount: detailsElement.querySelectorAll("dt").length,
      ddCount: detailsElement.querySelectorAll("dd").length,
      noteCount: detailsElement.querySelectorAll("p.population-note").length,
      hasValues: ["266,188", "610,624", "313,542", "316,843", "2026-01-01", "13,293,851"].every((value) => text.includes(value)),
      overflow: getComputedStyle(element).overflow,
      maxHeight: getComputedStyle(element).maxHeight,
      card: {
        top: cardBox.top,
        bottom: cardBox.bottom,
        left: cardBox.left,
        right: cardBox.right,
        height: cardBox.height,
      },
      nodes,
    };
  });

  assert(audit.open === true, "details should be open");
  assert(audit.dtCount === 4 && audit.ddCount === 4, `expected 4 age groups, got ${audit.dtCount}/${audit.ddCount}`);
  assert(audit.noteCount >= 4, `expected notes to remain, got ${audit.noteCount}`);
  assert(audit.hasValues, "age group values, reference date, or denominator are missing");
  assert(audit.overflow !== "hidden", `population card should not clip details: overflow=${audit.overflow}`);
  assert(audit.maxHeight === "none", `population card should not use max-height: ${audit.maxHeight}`);
  for (const node of audit.nodes) {
    assert(node.display !== "none" && node.visibility !== "hidden", "detail node hidden");
    assert(node.height > 0, "detail node has no height");
    assert(node.top >= audit.card.top - 1 && node.bottom <= audit.card.bottom + 1, "detail node clipped vertically");
    assert(node.left >= audit.card.left - 1 && node.right <= audit.card.right + 1, "detail node clipped horizontally");
  }

  const openHeight = Math.round(audit.card.height);
  assert(openHeight > closedHeight, `card should grow when details open: closed=${closedHeight}, open=${openHeight}`);

  if (capture) {
    await card.screenshot({ path: path.join(outDir, `tokyo-card-open-${width}.png`) });
  }

  await card.locator("dd").first().click();
  assert(page.url() === beforeUrl, "details content click navigated unexpectedly");

  await summary.click();
  assert(await details.evaluate((element) => element.open) === false, "summary second click should close details");

  await summary.focus();
  await page.keyboard.press("Enter");
  assert(page.url() === beforeUrl, "summary Enter navigated unexpectedly");
  assert(await details.evaluate((element) => element.open) === true, "Enter should open details");
  await page.keyboard.press("Enter");
  assert(await details.evaluate((element) => element.open) === false, "Enter should close details");
  await page.keyboard.press("Space");
  assert(page.url() === beforeUrl, "summary Space navigated unexpectedly");
  assert(await details.evaluate((element) => element.open) === true, "Space should open details");
  await page.keyboard.press("Space");
  assert(await details.evaluate((element) => element.open) === false, "Space should close details");

  return { closedHeight, openHeight };
}

async function verifyViewport(page, width) {
  await page.setViewportSize({ width, height: 900 });
  await gotoPortal(page);
  await verifyCardBasics(page);
  const heights = await verifyTokyoDetails(page, width, width === 1280 || width === 375);
  const metrics = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    cardCount: document.querySelectorAll(".pref-card.prefecture-card").length,
  }));
  assert(metrics.scrollWidth <= metrics.clientWidth + 1, `horizontal overflow at ${width}: ${metrics.scrollWidth} > ${metrics.clientWidth}`);
  return { width, ...metrics, ...heights };
}

async function verifyNavigation(page) {
  await gotoPortal(page);
  const tokyoCard = page.locator(".pref-card.prefecture-card").first();
  await tokyoCard.locator("h2").click();
  await page.waitForURL(/\/tools\/school-database\/tokyo\/?$/);
  await page.goBack({ waitUntil: "networkidle" });

  await page.locator(".pref-card.prefecture-card").first().focus();
  await page.keyboard.press("Enter");
  await page.waitForURL(/\/tools\/school-database\/tokyo\/?$/);
  await page.goBack({ waitUntil: "networkidle" });

  for (const [href, urlPattern] of [
    ["/tools/school-database/saitama/", /\/tools\/school-database\/saitama\/?$/],
    ["/tools/school-database/chiba/", /\/tools\/school-database\/chiba\/?$/],
    ["/tools/school-database/niigata/", /\/tools\/school-database\/niigata\/?$/],
    ["/tools/school-database/nagano/", /\/tools\/school-database\/nagano\/?$/],
    ["/tools/school-database/okinawa/", /\/tools\/school-database\/okinawa\/?$/],
  ]) {
    await page.locator(`a.pref-card.prefecture-card[href="${href}"]`).locator("h2").click();
    await page.waitForURL(urlPattern);
    await page.goBack({ waitUntil: "networkidle" });
  }
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const consoleMessages = [];
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  page.on("console", (message) => {
    if (message.type() === "error") {
      const text = message.text();
      if (
        text.startsWith("Failed to load resource:") ||
        text.startsWith("Error fetching school data:") ||
        /^Error fetching .+ school data:/.test(text)
      ) {
        return;
      }
      consoleMessages.push(text);
    }
  });

  const results = [];
  for (const width of widths) {
    results.push(await verifyViewport(page, width));
  }
  await verifyNavigation(page);

  assert(consoleMessages.length === 0, `unexpected console errors: ${consoleMessages.join("\n")}`);

  await browser.close();
  console.log(JSON.stringify({ outDir, results }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
