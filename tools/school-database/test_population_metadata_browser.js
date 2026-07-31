const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const outDir = path.join(process.env.LOCALAPPDATA || process.env.TEMP, "prefecture-card-data-rendering");
const baseUrl = process.env.SCHOOL_DATABASE_BASE_URL || "http://127.0.0.1:8765";

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const response = await page.goto(`${baseUrl}/tools/school-database/`, { waitUntil: "networkidle" });
  if (!response || response.status() !== 200) {
    throw new Error(`HTTP ${response && response.status()}`);
  }

  const cardCount = await page.locator(".pref-card.prefecture-card").count();
  if (cardCount !== 47) throw new Error(`expected 47 prefecture cards, got ${cardCount}`);
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
  if (cardAudit.length !== 47) throw new Error(`expected 47 audited cards, got ${cardAudit.length}`);
  if (cardAudit.some((card) => !card.href)) throw new Error("empty prefecture link found");
  if (cardAudit.some((card) => card.disabledButtons > 0)) throw new Error("disabled transition button remains");
  if (cardAudit.some((card) => card.schoolMetaRows !== 4)) throw new Error("every card should keep 4 school database metadata rows");
  const cardsWithPopulation = cardAudit.filter((card) => card.hasPopulation);
  if (cardsWithPopulation.length !== 1 || cardsWithPopulation[0].name !== "東京都") {
    throw new Error(`population should render only on Tokyo card: ${JSON.stringify(cardsWithPopulation)}`);
  }
  const expectedOrder = ["東京都", "神奈川県", "埼玉県", "千葉県"];
  for (const [index, name] of expectedOrder.entries()) {
    if (cardAudit[index].name !== name) throw new Error(`unexpected card order at ${index}: ${cardAudit[index].name}`);
  }
  if (cardAudit[0].href !== "/tools/school-database/tokyo/") throw new Error(`unexpected Tokyo href: ${cardAudit[0].href}`);
  if (cardAudit[cardAudit.length - 1].name !== "沖縄県") throw new Error("Okinawa should remain the last card");
  const bodyText = await page.locator("body").innerText();
  for (const prohibited of [
    "全国他都道府県",
    "準備中",
    "順次拡張予定",
    "順次追加予定",
    "全国都道府県の学校データベースを順次追加予定です。",
  ]) {
    if (bodyText.includes(prohibited)) throw new Error(`placeholder text remains: ${prohibited}`);
  }

  const card = page.locator(".pref-card.prefecture-card", { hasText: "東京都" });
  const defaultText = await card.innerText();
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
    "1,507,197人",
    "人口に占める割合 11.3%",
    "実際の在学者数ではありません。",
  ]) {
    if (!defaultText.includes(expected)) throw new Error(`missing default text: ${expected}`);
  }
  for (const prohibited of ["総人口", "日本人人口", "日本人人口比", "学齢人口", "教育年齢人口"]) {
    if (defaultText.includes(prohibited)) throw new Error(`prohibited text in card: ${prohibited}`);
  }
  for (const name of ["千葉県", "茨城県", "栃木県"]) {
    const text = await page.locator(".pref-card.prefecture-card", { hasText: name }).innerText();
    if (text.includes("人口（日本国籍）") || text.includes("3～17歳人口") || text.includes("0人") || text.includes("準備中")) {
      throw new Error(`${name} should not show unavailable population placeholders`);
    }
  }
  await card.screenshot({ path: path.join(outDir, "tokyo-card-default-1280.png") });

  const beforeUrl = page.url();
  await card.locator("summary").focus();
  await page.keyboard.press("Enter");
  if (page.url() !== beforeUrl) throw new Error("summary Enter navigated unexpectedly");
  const detailsText = await card.locator(".population-age-details").innerText();
  for (const expected of [
    "年齢別人口",
    "幼児期相当 3～5歳",
    "266,188人・2.0%",
    "小学校期相当 6～11歳",
    "610,624人・4.6%",
    "中学校期相当 12～14歳",
    "313,542人・2.4%",
    "高校期相当 15～17歳",
    "316,843人・2.4%",
  ]) {
    if (!detailsText.includes(expected)) throw new Error(`missing detail text: ${expected}`);
  }
  for (const expected of [
    "外国籍の住民は含みません。",
    "実際の在学者数ではありません。",
    "人口（日本国籍）13,293,851人を分母として計算しています。",
  ]) {
    if (!detailsText.includes(expected)) throw new Error(`missing note text: ${expected}`);
  }
  await card.screenshot({ path: path.join(outDir, "tokyo-card-details-1280.png") });
  await card.locator("dd").first().click();
  if (page.url() !== beforeUrl) throw new Error("details content click navigated unexpectedly");
  await page.keyboard.press("Space");
  if (page.url() !== beforeUrl) throw new Error("summary Space navigated unexpectedly");

  await page.goto(`${baseUrl}/tools/school-database/`, { waitUntil: "networkidle" });
  await page.locator(".pref-card.prefecture-card", { hasText: "東京都" }).locator("h2").click();
  await page.waitForURL(/\/tools\/school-database\/tokyo\/?$/);
  await page.goBack({ waitUntil: "networkidle" });

  await page.locator(".population-card-link").focus();
  await page.keyboard.press("Enter");
  await page.waitForURL(/\/tools\/school-database\/tokyo\/?$/);
  await page.goBack({ waitUntil: "networkidle" });

  for (const [name, urlPattern] of [
    ["埼玉県", /\/tools\/school-database\/saitama\/?$/],
    ["千葉県", /\/tools\/school-database\/chiba\/?$/],
    ["新潟県", /\/tools\/school-database\/niigata\/?$/],
    ["長野県", /\/tools\/school-database\/nagano\/?$/],
    ["沖縄県", /\/tools\/school-database\/okinawa\/?$/],
  ]) {
    await page.locator(".pref-card.prefecture-card", { hasText: name }).locator("h2").click();
    await page.waitForURL(urlPattern);
    await page.goBack({ waitUntil: "networkidle" });
  }

  await page.locator(".pref-card.prefecture-card", { hasText: "埼玉県" }).focus();
  await page.keyboard.press("Enter");
  await page.waitForURL(/\/tools\/school-database\/saitama\/?$/);
  await page.goBack({ waitUntil: "networkidle" });

  const results = [];
  for (const width of [1280, 1024, 768, 375]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto(`${baseUrl}/tools/school-database/`, { waitUntil: "networkidle" });
    const metrics = await page.evaluate(() => {
      const grid = document.querySelector(".prefectures-grid");
      const cards = [...document.querySelectorAll(".pref-card.prefecture-card")];
      const firstTop = cards[0].getBoundingClientRect().top;
      const firstRowCards = cards.filter((card) => Math.abs(card.getBoundingClientRect().top - firstTop) < 2);
      const firstRowHeights = firstRowCards.map((card) => Math.round(card.getBoundingClientRect().height));
      return {
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
        firstRow: firstRowCards.length,
        firstRowHeights,
        gridTemplateColumns: getComputedStyle(grid).gridTemplateColumns,
      };
    });
    const screenshot = path.join(outDir, `portal-${width}.png`);
    await page.screenshot({ path: screenshot, fullPage: true });
    if (metrics.scrollWidth > metrics.clientWidth + 1) {
      throw new Error(`horizontal overflow at ${width}: ${metrics.scrollWidth} > ${metrics.clientWidth}`);
    }
    results.push({ width, ...metrics, screenshot });
  }

  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto(`${baseUrl}/tools/school-database/`, { waitUntil: "networkidle" });
  await page.screenshot({ path: path.join(outDir, "comparison-tokyo-chiba-ibaraki-1280.png"), fullPage: true });
  await page.setViewportSize({ width: 375, height: 900 });
  await page.goto(`${baseUrl}/tools/school-database/`, { waitUntil: "networkidle" });
  await page.locator(".pref-card.prefecture-card", { hasText: "東京都" }).screenshot({
    path: path.join(outDir, "tokyo-card-375.png"),
  });
  await page.locator(".pref-card.prefecture-card", { hasText: "東京都" }).locator("summary").click();
  await page.locator(".pref-card.prefecture-card", { hasText: "東京都" }).screenshot({
    path: path.join(outDir, "tokyo-card-details-375.png"),
  });

  await browser.close();
  console.log(JSON.stringify({ outDir, results }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
