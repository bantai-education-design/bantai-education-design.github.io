const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const outDir = path.join(process.env.LOCALAPPDATA || process.env.TEMP, "tokyo-population-pilot-v2");
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
  const pilotCount = await page.locator(".population-pilot-card").count();
  if (cardCount !== 47) throw new Error(`expected 47 prefecture cards, got ${cardCount}`);
  if (pilotCount !== 1) throw new Error(`expected 1 pilot card, got ${pilotCount}`);
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

  const card = page.locator(".population-pilot-card");
  const defaultText = await card.innerText();
  for (const expected of [
    "人口（日本国籍）",
    "13,293,851人",
    "3～17歳人口",
    "1,507,197人",
    "人口に占める割合 11.3%",
    "収録校・園",
    "外国籍の住民は含みません。",
    "実際の在学者数ではありません。",
  ]) {
    if (!defaultText.includes(expected)) throw new Error(`missing default text: ${expected}`);
  }
  for (const prohibited of ["総人口", "日本人人口", "日本人人口比", "学齢人口", "教育年齢人口"]) {
    if (defaultText.includes(prohibited)) throw new Error(`prohibited text in card: ${prohibited}`);
  }
  await card.screenshot({ path: path.join(outDir, "tokyo-card-proposal-a-1280.png") });

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
  await card.screenshot({ path: path.join(outDir, "tokyo-card-proposal-b-1280.png") });
  await page.keyboard.press("Space");
  if (page.url() !== beforeUrl) throw new Error("summary Space navigated unexpectedly");

  const results = [];
  for (const width of [1280, 1024, 768, 375]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto(`${baseUrl}/tools/school-database/`, { waitUntil: "networkidle" });
    const metrics = await page.evaluate(() => {
      const grid = document.querySelector(".prefectures-grid");
      const cards = [...document.querySelectorAll(".pref-card.prefecture-card")];
      const firstTop = cards[0].getBoundingClientRect().top;
      const firstRow = cards.filter((card) => Math.abs(card.getBoundingClientRect().top - firstTop) < 2).length;
      return {
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
        firstRow,
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

  await browser.close();
  console.log(JSON.stringify({ outDir, results }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
