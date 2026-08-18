const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const puppeteer = require("puppeteer-core");

const dir = __dirname;
const htmlPath = path.join(dir, "CalTrack_Interview_Preparation.html");
const pdfPath = path.join(dir, "..", "CalTrack_Interview_Preparation.pdf");
const chrome =
  process.env.CHROME_PATH ||
  "/usr/bin/google-chrome-stable";

async function main() {
  if (!fs.existsSync(htmlPath)) {
    throw new Error(`Missing ${htmlPath}`);
  }
  const browser = await puppeteer.launch({
    executablePath: chrome,
    headless: true,
    args: ["--no-sandbox", "--disable-gpu", "--font-render-hinting=medium"],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1200, height: 1600, deviceScaleFactor: 2 });
  await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "networkidle0", timeout: 120000 });
  await page.evaluate(async () => {
    if (typeof mermaid === "undefined") {
      throw new Error("mermaid failed to load");
    }
    await mermaid.run({ querySelector: ".mermaid" });
  });
  await page.waitForFunction(
    () => document.querySelectorAll(".mermaid svg").length >= 5,
    { timeout: 60000 },
  );
  const svgCount = await page.evaluate(() => document.querySelectorAll(".mermaid svg").length);
  await page.pdf({
    path: pdfPath,
    format: "Letter",
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: `
      <div style="width:100%;font-size:8px;color:#5a6e66;padding:0 18mm;font-family:system-ui,sans-serif;display:flex;justify-content:space-between;">
        <span>CalTrack · Technical &amp; Interview Preparation Guide</span>
        <span>Confidential study notes · no secrets</span>
      </div>`,
    footerTemplate: `
      <div style="width:100%;font-size:8px;color:#5a6e66;padding:0 18mm;font-family:system-ui,sans-serif;display:flex;justify-content:space-between;">
        <span>Based on repository inspection of Prudhvi-60/CalTrack</span>
        <span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
      </div>`,
    margin: { top: "16mm", bottom: "16mm", left: "14mm", right: "14mm" },
  });
  await browser.close();
  const stat = fs.statSync(pdfPath);
  console.log(JSON.stringify({ pdfPath, bytes: stat.size, mermaidSvgs: svgCount }));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
