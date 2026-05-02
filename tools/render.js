#!/usr/bin/env node
/**
 * Puppeteer レンダラ。
 *   node tools/render.js --workdir output/2026-05-03_横山直広
 *
 * 入力: workdir/kantei.json, workdir/modules.json, workdir/subject.json
 * 出力: workdir/kantei.html, workdir/kantei.pdf, workdir/kantei.png
 */
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

function arg(name, def) {
  const i = process.argv.indexOf('--' + name);
  return i >= 0 ? process.argv[i + 1] : def;
}

function esc(s) {
  return String(s ?? '').replace(/[&<>"]/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]
  ));
}

function renderItems(items) {
  if (!items || !items.length) return '<li>—</li>';
  return items.map(it =>
    `<li><b>${esc(it.title || '')}</b><br>${esc(it.body || '')}` +
    (it.sources ? ` <span class="warning">(${it.sources.join('・')})</span>` : '') +
    `</li>`
  ).join('');
}

function renderLifePhases(phases) {
  if (!phases || !phases.length) return '<tr><td colspan="2">—</td></tr>';
  return phases.map(p =>
    `<tr><th>${esc(p.age_range)}</th><td>${esc(p.summary)}</td></tr>`
  ).join('');
}

function renderLucky(lucky) {
  if (!lucky) return '';
  const items = [
    ['色', lucky.color],
    ['方位', lucky.direction],
    ['数', lucky.number],
    ['石', lucky.stone],
    ['曜日', lucky.day_of_week],
    ['縁する人', lucky.ally_type],
  ];
  return items.map(([k, v]) =>
    `<div><div class="label">${esc(k)}</div><div class="value">${esc(v ?? '—')}</div></div>`
  ).join('');
}

function renderModuleSection(mod) {
  if (!mod) return '';
  const findings = (mod.key_findings || [])
    .map(f => `<li>${esc(f)}</li>`).join('');
  return `
    <div class="section">
      <h3>${esc(mod.label)}</h3>
      <div class="module-summary">${esc(mod.summary)}</div>
      ${findings ? `<ul class="findings">${findings}</ul>` : ''}
    </div>`;
}

function fillTemplate(tpl, vars) {
  return tpl.replace(/\{\{(\w+)\}\}/g, (_, k) => vars[k] ?? '');
}

async function main() {
  const workdir = arg('workdir');
  const repoRoot = arg('repo-root', path.resolve(__dirname, '..'));
  if (!workdir) {
    console.error('--workdir required');
    process.exit(1);
  }

  const kantei = JSON.parse(fs.readFileSync(path.join(workdir, 'kantei.json'), 'utf-8'));
  const modules = JSON.parse(fs.readFileSync(path.join(workdir, 'modules.json'), 'utf-8'));
  const subject = JSON.parse(fs.readFileSync(path.join(workdir, 'subject.json'), 'utf-8'));

  const tplPath = path.join(repoRoot, 'templates', 'kantei_pdf.html');
  const tpl = fs.readFileSync(tplPath, 'utf-8');

  const moduleOrder = ['seimei', 'shichu', 'shibun', 'astrology', 'vedic',
    'numerology', 'kyusei', 'shukuyo', 'sanmei', 'biorhythm', 'maya',
    'ninsou', 'tesou'];
  const moduleSections = moduleOrder
    .map(id => renderModuleSection(modules.modules?.[id]))
    .filter(Boolean)
    .join('\n');

  const html = fillTemplate(tpl, {
    NAME_KANJI: esc(subject.name_kanji),
    BIRTH_DATE: esc(subject.birth_date),
    BIRTH_TIME: subject.birth_time_known ? esc(subject.birth_time) : '時刻不明',
    BIRTH_PLACE: esc(subject.birth_place),
    ISSUED_AT: esc(kantei.issued_at || new Date().toISOString().slice(0, 10)),
    HEADLINE: esc(kantei.headline),
    CONSTITUTION: esc(kantei.constitution),
    MISSION_ITEMS: renderItems(kantei.mission),
    TALENTS_ITEMS: renderItems(kantei.talents),
    TODO_ITEMS: renderItems(kantei.todo_now),
    WARNING_ITEMS: renderItems(kantei.warnings),
    MODULE_SECTIONS: moduleSections,
    LIFE_PHASES_ROWS: renderLifePhases(kantei.life_phases),
    BIORHYTHM_SUMMARY: esc(modules.modules?.biorhythm?.summary || '—'),
    LUCKY_GRID: renderLucky(kantei.lucky),
    CLOSING: esc(kantei.closing),
  });

  const htmlPath = path.join(workdir, 'kantei.html');
  fs.writeFileSync(htmlPath, html, 'utf-8');
  console.log(`HTML: ${htmlPath}`);

  const browser = await puppeteer.launch({ headless: 'new' });
  try {
    const page = await browser.newPage();
    await page.setContent(html, { waitUntil: 'networkidle0' });

    const pdfPath = path.join(workdir, 'kantei.pdf');
    await page.pdf({
      path: pdfPath,
      format: 'A4',
      printBackground: true,
      margin: { top: '18mm', bottom: '18mm', left: '16mm', right: '16mm' },
    });
    console.log(`PDF:  ${pdfPath}`);

    await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 2 });
    await page.setContent(html, { waitUntil: 'networkidle0' });
    const pngPath = path.join(workdir, 'kantei.png');
    await page.screenshot({ path: pngPath, fullPage: true });
    console.log(`PNG:  ${pngPath}`);
  } finally {
    await browser.close();
  }
}

main().catch(e => {
  console.error(e);
  process.exit(1);
});
