#!/usr/bin/env node
/**
 * IncidentMind — scripted screen recorder.
 *
 * Drives the verified demo flow against a running deployment and writes a
 * 1920x1080 WebM. This is a submission asset, not product code: it imports
 * nothing from the app and lives outside frontend/ and backend/.
 *
 *   npm run record              reset memory, record, clean up afterwards
 *   npm run record -- --no-reset   record against the current memory state
 *   npm run record -- --keep       leave the created incident and memory in place
 *   HEADED=1 npm run record        watch it run in a real window
 *
 * Two things are deliberate and worth understanding before changing them:
 *
 * 1. The memory bank is reset first. The flow ends by retaining INC-005, so a
 *    second run would open on an incident whose closest match is itself. The
 *    reset re-retains exactly INC-001..INC-004, which makes every run produce
 *    the same video.
 *
 * 2. Every wait is on a real condition, never a fixed sleep. The analysis is a
 *    live LLM behind a free-tier cold start. Timers either cut the result off
 *    or pad the video with dead air; waiting for the recalled incident ID is
 *    self-correcting.
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const VIDEO_DIR = path.resolve(HERE, "video");
const ENV_FILE = path.resolve(HERE, "..", "..", "backend", ".env");

const BASE = (process.env.DEMO_BASE_URL ?? "https://incidentmind-eight.vercel.app").replace(/\/+$/, "");
const API = `${BASE}/backend`;
const VIEW = { width: 1920, height: 1080 };

/** The incident the cold open investigates. Must NOT be pre-retained. */
const SOURCE = "INC-005";
/** The reference history re-retained by the reset. */
const HISTORY = ["INC-001", "INC-002", "INC-003", "INC-004"];

const RESET = !process.argv.includes("--no-reset");
const KEEP = process.argv.includes("--keep");
const HEADED = process.env.HEADED === "1";

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

let n = 0;
const log = (msg) => console.log(`  ${String(++n).padStart(2, "0")}  ${msg}`);
const note = (msg) => console.log(`      ${msg}`);
const warn = (msg) => console.log(`      ! ${msg}`);

async function getJson(url, init) {
  const res = await fetch(url, init);
  const body = await res.text();
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText} — ${url} :: ${body.slice(0, 240)}`);
  }
  try {
    return body ? JSON.parse(body) : null;
  } catch {
    return body;
  }
}

function readEnv(file) {
  const out = {};
  if (!fs.existsSync(file)) return out;
  for (const raw of fs.readFileSync(file, "utf8").split(/\r?\n/)) {
    const m = /^\s*([A-Za-z0-9_]+)\s*=\s*(.*?)\s*$/.exec(raw);
    if (m) out[m[1]] = m[2].replace(/^["'](.*)["']$/, "$1");
  }
  return out;
}

function hindsight() {
  const env = readEnv(ENV_FILE);
  const base = (env.HINDSIGHT_BASE_URL ?? "").replace(/\/+$/, "");
  const prefix = env.HINDSIGHT_API_PREFIX || "/v1/default";
  const bank = env.HINDSIGHT_BANK_ID || "incidentmind-demo";
  if (!env.HINDSIGHT_API_KEY || !base) return null;
  return {
    url: `${base}${prefix}/banks/${bank}/memories`,
    headers: { authorization: `Bearer ${env.HINDSIGHT_API_KEY}` },
    bank,
  };
}

async function warm() {
  const deadline = Date.now() + 240_000;
  let last = "no response";
  process.stdout.write("      waking the API (a free-tier cold start takes 30-50s) ");
  while (Date.now() < deadline) {
    try {
      const h = await getJson(`${API}/api/health`);
      if (h?.memory?.mode === "live" && h?.database?.mode === "live") {
        process.stdout.write("\n");
        log(`API ready — memory=${h.memory.mode} llm=${h.llm.mode} database=${h.database.mode}`);
        return h;
      }
      last = `memory=${h?.memory?.mode} llm=${h?.llm?.mode}`;
    } catch (err) {
      last = err.message.slice(0, 120);
    }
    process.stdout.write(".");
    await sleep(3000);
  }
  process.stdout.write("\n");
  throw new Error(`API never became ready (last: ${last})`);
}

async function clearBank() {
  const h = hindsight();
  if (!h) {
    warn("no Hindsight credentials in backend/.env — skipping the memory reset");
    return false;
  }
  await getJson(h.url, { method: "DELETE", headers: h.headers });
  note(`cleared bank "${h.bank}"`);
  return true;
}

async function retain(id) {
  const r = await getJson(`${API}/api/incidents/${id}/retain`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: "{}",
  });
  note(`retained ${id} — ${r?.detail ?? r?.status ?? "ok"}`);
}

async function resetMemory() {
  if (!(await clearBank())) return;
  for (const id of HISTORY) await retain(id);
  note("waiting for the memory service to index…");
  await sleep(9000);
}

/**
 * The recorded run.
 *
 * Act 1 gives the product 15 seconds of context.
 * Act 2 is the cold open: an incident whose memory panel already holds three
 *        real prior incidents, before anything is retained today.
 * Act 3 is the live loop, and it has to happen on a NEW incident: every seeded
 *        incident ships already resolved, so approve/resolve/retain are only
 *        available on one created during the session.
 */
async function record(page) {
  log("landing page — the memory loop");
  await page.goto(BASE, { waitUntil: "load" });
  await page
    .getByText(/API connected/i)
    .first()
    .waitFor({ state: "visible", timeout: 60_000 })
    .catch(() => warn("status line not visible — continuing"));
  await sleep(4500);
  await page
    .getByText(/Hindsight/i)
    .first()
    .scrollIntoViewIfNeeded()
    .catch(() => {});
  await sleep(3500);

  log("dashboard — the backlog of retained experience");
  await page.goto(`${BASE}/dashboard`, { waitUntil: "load" });
  await page
    .getByText(/Experiences in memory/i)
    .first()
    .waitFor({ state: "visible", timeout: 60_000 })
    .catch(() => warn("memory KPI not visible — continuing"));
  await sleep(6000);

  log(`cold open — ${SOURCE}, already resolved, nothing retained today`);
  await page.goto(`${BASE}/incidents/${SOURCE}`, { waitUntil: "load" });
  await page
    .getByRole("button", { name: /^Investigate with memory$/i })
    .first()
    .waitFor({ state: "visible", timeout: 60_000 });
  await sleep(6000);

  log("investigate with memory");
  await page.getByRole("button", { name: /^Investigate with memory$/i }).first().click();
  const recalled = page.getByRole("link", { name: /^INC-00[1-4]$/ }).first();
  await recalled.waitFor({ state: "visible", timeout: 150_000 });
  note(`recall landed — the panel cites ${await recalled.innerText()}`);
  await page
    .getByText("Relevant memory")
    .first()
    .scrollIntoViewIfNeeded()
    .catch(() => {});
  await sleep(8000);

  log("retain the experience");
  const retainBtn = page.getByRole("button", { name: /Retain experience to memory/i }).first();
  await retainBtn.scrollIntoViewIfNeeded();
  await sleep(1500);
  await retainBtn.click();
  const retainedText = page.getByText(/Experience added to organizational memory/i).first();
  await retainedText.waitFor({ state: "visible", timeout: 120_000 });
  await retainedText.scrollIntoViewIfNeeded().catch(() => {});
  await sleep(5000);

  log("trigger a similar incident");
  await page.getByRole("button", { name: /Trigger a similar incident/i }).first().click();
  const dialog = page.getByRole("dialog");
  await dialog.waitFor({ state: "visible", timeout: 30_000 });
  await sleep(3500); // the dialog states the wording is deliberately different — let it be read
  await Promise.all([
    page.waitForURL(
      (u) => /\/incidents\/INC-\d+/.test(u.pathname) && !u.pathname.endsWith(SOURCE),
      { timeout: 90_000 },
    ),
    page.getByRole("button", { name: /Create and investigate/i }).click(),
  ]);
  const created = page.url().split("/").filter(Boolean).pop();
  note(`created ${created}`);
  await sleep(5000);

  log(`investigate ${created} — the payoff`);
  await page
    .getByRole("button", { name: /Investigate with memory/i })
    .first()
    .waitFor({ state: "visible", timeout: 60_000 });
  await page.getByRole("button", { name: /Investigate with memory/i }).first().click();
  const payoff = page.getByRole("link", { name: SOURCE, exact: true }).first();
  await payoff.waitFor({ state: "visible", timeout: 150_000 });
  note(`${created} recalled ${SOURCE} — the experience retained one step ago`);
  await page
    .getByText("Relevant memory")
    .first()
    .scrollIntoViewIfNeeded()
    .catch(() => {});
  await sleep(8000);

  log("approve the simulated action");
  const approveBtn = page.getByRole("button", { name: /Approve simulated action/i }).first();
  await approveBtn.scrollIntoViewIfNeeded();
  await sleep(1500);
  await approveBtn.click();
  await dialog.waitFor({ state: "visible", timeout: 30_000 });
  await page.locator("#approver").fill("Vishal Mudhiraj");
  await sleep(1500);
  await page.getByRole("button", { name: /Approve and simulate/i }).click();
  const outcome = page.getByText(/Simulated action/i).first();
  await outcome.waitFor({ state: "visible", timeout: 90_000 });
  await outcome.scrollIntoViewIfNeeded().catch(() => {});
  await sleep(5000);

  log("resolve and retain the outcome");
  const cause = page.getByPlaceholder("What actually caused this?");
  if (await cause.count()) {
    if (!(await cause.first().inputValue()).trim()) {
      await cause
        .first()
        .fill("Cache invalidation produced stale reads and a thundering herd against the backend.");
      warn("the prefilled root cause was empty — filled it so the record is complete");
    }
  }
  const resolveBtn = page.getByRole("button", { name: /Resolve and retain|Resolve incident/i }).first();
  await resolveBtn.scrollIntoViewIfNeeded();
  await sleep(1500);
  await resolveBtn.click();
  await page
    .getByText(/Experience added to organizational memory/i)
    .first()
    .waitFor({ state: "visible", timeout: 120_000 });
  await sleep(6000);

  log("the loop is closed — holding the final frame");
  await sleep(1500);
  return created;
}

async function cleanup(created) {
  log("cleaning up so the app matches DEMO.md for a manual take");
  if (created) {
    await getJson(`${API}/api/incidents/${created}`, { method: "DELETE" }).catch(() =>
      warn(`could not delete ${created}`),
    );
    note(`deleted ${created}`);
  }
  await resetMemory();
}

async function main() {
  console.log(`\n  IncidentMind demo recorder\n  target: ${BASE}\n`);
  await warm();

  if (RESET) {
    log("resetting organisational memory to the reference history");
    await resetMemory();
  } else {
    note("--no-reset: recording against the current memory state");
  }

  fs.mkdirSync(VIDEO_DIR, { recursive: true });

  const browser = await chromium.launch({ headless: !HEADED });
  const context = await browser.newContext({
    viewport: VIEW,
    deviceScaleFactor: 1,
    recordVideo: { dir: VIDEO_DIR, size: VIEW },
  });
  const page = await context.newPage();
  page.setDefaultTimeout(90_000);

  const video = page.video();
  let created = null;
  let failed = null;

  try {
    created = await record(page);
  } catch (err) {
    failed = err;
    warn(`run stopped: ${err.message.slice(0, 200)}`);
  } finally {
    // The video is only flushed when the context closes, so this must happen
    // before the path is read — and it must happen even on failure, otherwise
    // a broken run leaves nothing to look at.
    await context.close().catch(() => {});
    await browser.close().catch(() => {});
  }

  let outPath = null;
  try {
    const src = await video.path();
    outPath = path.join(VIDEO_DIR, "incidentmind-demo.webm");
    fs.rmSync(outPath, { force: true });
    fs.renameSync(src, outPath);
  } catch (err) {
    warn(`could not collect the video: ${err.message.slice(0, 160)}`);
  }

  if (!KEEP) {
    await cleanup(created).catch((err) => warn(`cleanup failed: ${err.message.slice(0, 160)}`));
  } else {
    note(`--keep: left ${created ?? "nothing"} and the retained memory in place`);
  }

  console.log("");
  if (outPath) {
    const mb = (fs.statSync(outPath).size / 1024 / 1024).toFixed(1);
    console.log(`  video   ${outPath}  (${mb} MB, 1920x1080, silent)`);
  }
  if (failed) {
    console.log(`  result  INCOMPLETE — ${failed.message.slice(0, 160)}`);
    process.exitCode = 1;
  } else {
    console.log(`  result  complete`);
    console.log(`  note    silent by design. Add narration, or talk over it.`);
  }
  console.log("");
}

main().catch((err) => {
  console.error(`\n  fatal: ${err.message}\n`);
  process.exitCode = 1;
});
