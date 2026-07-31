const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const outDir = path.join(process.env.LOCALAPPDATA || process.env.TEMP, "fix-tokyo-population-details");
const baseUrl = process.env.SCHOOL_DATABASE_BASE_URL || "http://127.0.0.1:8765";

const widths = [1280, 1024, 768, 375];
const representativeCards = [
  ["埼玉県", /\/tools\/school-database\/saitama\/?$/],
  ["千葉県", /\/tools\/school-database\/chiba\/?$/],
  ["新潟県", /\/tools\/school-database\/niigata\/?$/],
  ["長野県", /\/tools\/school-database\/nagano\/?$/],
  ["沖縄県", /\/tools\/school-database\/okinawa\/?$/],
];

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

async function gotoPortal(page) {
  const response = await page.goto(`${baseUrl}/tools/school-database/`, { waitUntil: "networkidle" });
  assert(response && response.status() === 200, `HTTP ${response && response.status()}`);
}

async function verifyCardBasics(page) {
  const cardAudit = await page.evaluate(() => {
    const cards = [...document.querySelectorAll(".pref-card.prefecture-card")];
    return cards.map((card) => {
      const link = card.matches("a[href]") ? card : card.querySelector("a[href]");
      return {
        name: card.querySelector("h2")?.textContent?.trim() || "",
        href: link?.getAttribute("href") || card.dataset.cardHref || "",
        tag: card.tagName,
        disabledButtons: card.querySelectorAll("button[disabled]").length,
        hasPopulation: Boolean(card.querySelector(".population-summary")),
        schoolMetaRows: card.querySelectorAll(".pref-meta-grid .meta-row").length,
      };
    });
  });

  assert(cardAudit.length === 47, `expected 47 prefecture cards, got ${cardAudit.length}`);
  assert(cardAudit.every((card) => card.href), "empty prefecture link found");
  assert(cardAudit.every((card) => card.disabledButtons === 0), "disabled transition button remains");
  assert(cardAudit.every((card) => card.schoolMetaRows === 4), "every card should keep 4 school database metadata rows");

  const populationCards = cardAudit.filter((card) => card.hasPopulation);
  assert(populationCards.length === 1 && populationCards[0].name === "東京都", `population should render only on Tokyo: ${JSON.stringify(populationCards)}`);
  assert(cardAudit[0].name === "東京都", `Tokyo should remain first, got ${cardAudit[0].name}`);
  assert(cardAudit[0].href === "/tools/school-database/tokyo/", `unexpected Tokyo href: ${cardAudit[0].href}`);
  assert(cardAudit[cardAudit.length - 1].name === "沖縄県", "Okinawa should remain the last card");

  const bodyText = await page.locator("body").innerText();
  for (const prohibited of [
    "全国他都道府県",
    "準備中",
    "順次拡張予定",
    "順次追加予定",
    "全国都道府県の学校データベースを順次追加予定です。",
    "詳しく見る",
  ]) {
    assert(!bodyText.includes(prohibited), `prohibited portal text remains: ${prohibited}`);
  }
}

async function verifyTokyoDefault(card) {
  const text = await card.innerText();
  for (const expected of [
    "収録校・園",
    "3,493件",
    "対象地域",
    "66",
    "設置区分",
    "公2,274・私1,219",
    "校種",
    "人口（日本国籍）",
    "13,293,851人",
    "3～17歳人口",
    "1,507,197人（11.3%）",
    "年齢別人口",
    "東京都の学校データベースを開く →",
  ]) {
    assert(text.includes(expected), `missing Tokyo default text: ${expected}`);
  }

  for (const prohibited of [
    "日本人人口",
    "日本人人口比",
    "総人口",
    "小学生人口",
    "中学生人口",
    "高校生人口",
    "外国籍の住民は含みません",
    "実際の在学者数ではありません",
    "分母として計算しています",
  ]) {
    assert(!text.includes(prohibited), `prohibited or expanded-only text in default card: ${prohibited}`);
  }
}

async function verifyNoPopulationPlaceholders(page) {
  for (const name of ["千葉県", "茨城県", "栃木県", "沖縄県"]) {
    const text = await page.locator(".pref-card.prefecture-card", { hasText: name }).innerText();
    for (const prohibited of ["人口（日本国籍）", "3～17歳人口", "0人", "準備中"]) {
      assert(!text.includes(prohibited), `${name} should not show unavailable population text: ${prohibited}`);
    }
  }
}

async function assertDetailsWithinCard(card) {
  const result = await card.evaluate((cardElement) => {
    const cardBox = cardElement.getBoundingClientRect();
    const details = cardElement.querySelector(".population-age-details");
    const visibleNodes = [...details.querySelectorAll("summary, dt, dd, p")].map((node) => {
      const rect = node.getBoundingClientRect();
      const style = getComputedStyle(node);
      return {
        text: node.textContent.trim(),
        top: rect.top,
        bottom: rect.bottom,
        left: rect.left,
        right: rect.right,
        width: rect.width,
        height: rect.height,
        display: style.display,
        visibility: style.visibility,
      };
    });
    return {
      card: {
        top: cardBox.top,
        bottom: cardBox.bottom,
        left: cardBox.left,
        right: cardBox.right,
        width: cardBox.width,
        height: cardBox.height,
      },
      visibleNodes,
      overflow: getComputedStyle(cardElement).overflow,
      maxHeight: getComputedStyle(cardElement).maxHeight,
      detailsOpen: details.open,
    };
  });

  assert(result.detailsOpen === true, "details should be open before checking bounds");
  assert(result.overflow !== "hidden", `population card should not clip expanded details: overflow=${result.overflow}`);
  assert(result.maxHeight === "none", `population card should not use max-height: ${result.maxHeight}`);

  for (const node of result.visibleNodes) {
    assert(node.display !== "none" && node.visibility !== "hidden", `detail node hidden: ${node.text}`);
    assert(node.height > 0, `detail node has no height: ${node.text}`);
    assert(node.top >= result.card.top - 1, `detail node above card: ${node.text}`);
    assert(node.bottom <= result.card.bottom + 1, `detail node below card: ${node.text}`);
    assert(node.left >= result.card.left - 1, `detail node left of card: ${node.text}`);
    assert(node.right <= result.card.right + 1, `detail node right of card: ${node.text}`);
  }

  return result.card.height;
}

async function verifyTokyoDetails(page, width, capture) {
  const card = page.locator(".pref-card.prefecture-card", { hasText: "東京都" });
  const summary = card.locator("summary", { hasText: "年齢別人口" });
  const details = card.locator(".population-age-details");
  const beforeUrl = page.url();

  const closedHeight = await card.evaluate((element) => Math.round(element.getBoundingClientRect().height));
  if (capture) {
    await card.screenshot({ path: path.join(outDir, `tokyo-card-closed-${width}.png`) });
  }

  await summary.click();
  assert(page.url() === beforeUrl, "summary click navigated unexpectedly");
  assert(await details.evaluate((element) => element.open) === true, "summary click should open details");

  const detailsText = await details.innerText();
  for (const expected of [
    "幼児期相当 3～5歳",
    "266,188人・2.0%",
    "小学校期相当 6～11歳",
    "610,624人・4.6%",
    "中学校期相当 12～14歳",
    "313,542人・2.4%",
    "高校期相当 15～17歳",
    "316,843人・2.4%",
    "基準日：2026-01-01",
    "外国籍の住民は含みません",
    "実際の在学者数ではありません",
    "人口（日本国籍）13,293,851人を分母",
  ]) {
    assert(detailsText.includes(expected), `missing opened detail text: ${expected}`);
    assert(await card.locator(".population-age-details", { hasText: expected }).isVisible(), `detail text is not visible: ${expected}`);
  }

  const openHeight = Math.round(await assertDetailsWithinCard(card));
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

async function verifyNavigation(page) {
  await gotoPortal(page);
  await page.locator(".pref-card.prefecture-card", { hasText: "東京都" }).locator("h2").click();
  await page.waitForURL(/\/tools\/school-database\/tokyo\/?$/);
  await page.goBack({ waitUntil: "networkidle" });

  await page.locator(".population-card-link").focus();
  await page.keyboard.press("Enter");
  await page.waitForURL(/\/tools\/school-database\/tokyo\/?$/);
  await page.goBack({ waitUntil: "networkidle" });

  for (const [name, urlPattern] of representativeCards) {
    await page.locator(".pref-card.prefecture-card", { hasText: name }).locator("h2").click();
    await page.waitForURL(urlPattern);
    await page.goBack({ waitUntil: "networkidle" });
  }

  await page.locator(".pref-card.prefecture-card", { hasText: "埼玉県" }).focus();
  await page.keyboard.press("Enter");
  await page.waitForURL(/\/tools\/school-database\/saitama\/?$/);
  await page.goBack({ waitUntil: "networkidle" });
}

async function verifyViewport(page, width) {
  await page.setViewportSize({ width, height: 900 });
  await gotoPortal(page);
  await verifyCardBasics(page);
  await verifyNoPopulationPlaceholders(page);
  const card = page.locator(".pref-card.prefecture-card", { hasText: "東京都" });
  await verifyTokyoDefault(card);
  const heights = await verifyTokyoDetails(page, width, width === 1280 || width === 375);
  const metrics = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    cardCount: document.querySelectorAll(".pref-card.prefecture-card").length,
  }));
  assert(metrics.scrollWidth <= metrics.clientWidth + 1, `horizontal overflow at ${width}: ${metrics.scrollWidth} > ${metrics.clientWidth}`);
  return { width, ...metrics, ...heights };
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
