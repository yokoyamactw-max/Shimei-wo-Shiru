#!/usr/bin/env node
/**
 * やさしい版レンダラ。SVG図解 + 平易な鑑定文を組み合わせて PDF/PNG/HTML を出力する。
 *   node tools/render_plain.js --workdir output/2026-05-03_横山直広
 *
 * 入力:
 *   - workdir/kantei_plain.json  (kanteishi が平易日本語で書いた鑑定)
 *   - workdir/modules.json       (各占術の生データ)
 *   - workdir/subject.json
 *   - workdir/images/cover.png   (任意)
 * 出力:
 *   - workdir/kantei_plain.{html,pdf,png}
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
    `<li>` +
    `<b>${esc(it.title || '')}</b>` +
    `<span class="body">${esc(it.body || '')}</span>` +
    (it.plain_explanation ? `<span class="why">${esc(it.plain_explanation)}</span>` : '') +
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

function renderFourPillars(shichu) {
  if (!shichu || !shichu.details) return '';
  const d = shichu.details;
  const labels = { year: '年柱(祖先)', month: '月柱(両親)', day: '日柱(自分)', hour: '時柱(子孫)' };
  const elementMap = {
    '甲': '木陽', '乙': '木陰', '丙': '火陽', '丁': '火陰',
    '戊': '土陽', '己': '土陰', '庚': '金陽', '辛': '金陰',
    '壬': '水陽', '癸': '水陰',
  };
  const cells = [];
  for (const k of ['year', 'month', 'day', 'hour']) {
    const p = d[k];
    if (!p) continue;
    const stem = p.stem || p.gz_str?.[0] || '';
    const branch = p.branch || p.gz_str?.[1] || '';
    const meaning = elementMap[stem] || '';
    cells.push(
      `<div class="pillar">` +
      `<div class="label">${esc(labels[k] || k)}</div>` +
      `<div class="gz">${esc(stem)}${esc(branch)}</div>` +
      `<div class="meta">${esc(meaning)}</div>` +
      `</div>`
    );
  }
  return cells.join('');
}

function renderKyuseiGrid(kyusei) {
  if (!kyusei || !kyusei.details || !kyusei.details.honmei) return '';
  const honmei = kyusei.details.honmei.index;
  // 後天定位盤 (3x3) — 数字配置
  // 4 9 2
  // 3 5 7
  // 8 1 6
  const layout = [4, 9, 2, 3, 5, 7, 8, 1, 6];
  const names = {
    1: '一白', 2: '二黒', 3: '三碧', 4: '四緑', 5: '五黄',
    6: '六白', 7: '七赤', 8: '八白', 9: '九紫',
  };
  return layout.map(n =>
    `<div class="cell ${n === honmei ? 'honmei' : ''}">` +
    `<span class="num">${n}</span>${esc(names[n])}` +
    `</div>`
  ).join('');
}

function renderMayaBlock(maya) {
  if (!maya || !maya.details) return '';
  const d = maya.details;
  const kin = d.birth_kin || '';
  const seal = d.solar_seal || {};
  const tone = d.galactic_tone || {};
  const ws = d.wavespell || {};
  return (
    `<div class="maya-kin-badge">` +
    `<div class="kin">KIN</div>` +
    `<div class="num">${esc(kin)}</div>` +
    `</div>` +
    `<div class="maya-text">` +
    `<div class="seal">${esc(tone.name || '')}の${esc(seal.name || '')}</div>` +
    `<div>銀河の音 ${esc(tone.index || '')}：${esc((tone.keyword || '').replace(/^\d+：/, ''))}</div>` +
    `<div>太陽の紋章 ${esc(seal.index || '')}：${esc(seal.name || '')}</div>` +
    `<div>所属ウェイブスペル：${esc(ws.name || '')}</div>` +
    `</div>`
  );
}

function renderBiorhythmSVG(biorhythm) {
  if (!biorhythm || !biorhythm.details || !biorhythm.details.forecast_31d) {
    return '<svg viewBox="0 0 600 200"><text x="300" y="100" text-anchor="middle">データなし</text></svg>';
  }
  const f = biorhythm.details.forecast_31d;
  const W = 600, H = 220, PAD_X = 30, PAD_Y = 20;
  const xStep = (W - 2 * PAD_X) / (f.length - 1);
  const yMid = H / 2;
  const yScale = (H - 2 * PAD_Y) / 2;
  const xToPx = i => PAD_X + i * xStep;
  const yToPx = v => yMid - v * yScale;

  const colors = {
    physical: '#c0392b', emotional: '#2980b9',
    intellectual: '#27ae60', intuitive: '#8e44ad',
  };

  const lines = Object.entries(colors).map(([k, color]) => {
    const pts = f.map((d, i) => `${xToPx(i).toFixed(1)},${yToPx(d[k]).toFixed(1)}`).join(' ');
    return `<polyline fill="none" stroke="${color}" stroke-width="2" points="${pts}"/>`;
  }).join('\n  ');

  // 中央線(0%)、当日マーカー(中央 = i=15)
  const todayX = xToPx(15);
  const ticks = [];
  for (let i = 0; i < f.length; i += 5) {
    const x = xToPx(i);
    const day = f[i].offset >= 0 ? `+${f[i].offset}` : `${f[i].offset}`;
    ticks.push(`<text x="${x.toFixed(1)}" y="${(H - 4).toFixed(1)}" font-size="9" fill="#5a4a30" text-anchor="middle">${day}日</text>`);
  }

  return `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">
  <line x1="${PAD_X}" y1="${yMid}" x2="${W - PAD_X}" y2="${yMid}" stroke="#c8b88a" stroke-dasharray="3,3"/>
  <line x1="${todayX}" y1="${PAD_Y}" x2="${todayX}" y2="${H - PAD_Y - 8}" stroke="#a07a2a" stroke-width="1"/>
  <text x="${todayX}" y="${PAD_Y - 4}" font-size="9" fill="#a07a2a" text-anchor="middle">本日</text>
  <text x="${PAD_X - 4}" y="${PAD_Y + 4}" font-size="8" fill="#5a4a30" text-anchor="end">+100%</text>
  <text x="${PAD_X - 4}" y="${(H - PAD_Y).toFixed(1)}" font-size="8" fill="#5a4a30" text-anchor="end">-100%</text>
  ${lines}
</svg>`;
}

function renderOtherModuleCards(modules, exclude) {
  // 第四章で個別表示しない占術をカード化
  const labels = {
    seimei: '姓名判断', shibun: '紫微斗数', astrology: '西洋占星術',
    vedic: 'インド占星術', numerology: '数秘術', shukuyo: '宿曜占星術',
    sanmei: '算命学', ninsou: '人相', tesou: '手相',
  };
  return Object.entries(labels)
    .filter(([k]) => !exclude.includes(k) && modules[k])
    .map(([k, label]) => {
      const m = modules[k];
      return `<div class="module-card">` +
        `<h3>${esc(label)}</h3>` +
        `<div class="summary">${esc(m.summary || '')}</div>` +
        `</div>`;
    }).join('');
}

function renderGlossary() {
  const terms = [
    ['五行', '木・火・土・金・水の5要素で世界を分類する考え方。あなたの持つ性質を読み解く道具です。'],
    ['四柱推命', '生年月日と時刻から「年柱・月柱・日柱・時柱」の4つの干支を導き、性格と運勢を読む占い。'],
    ['紫微斗数', '中国の伝統的な占術。星の配置から人生の各分野（仕事・恋愛・財・健康など）を読みます。'],
    ['九星気学', '生まれ年から「本命星」を導き、方位や時期の吉凶を読む占い。'],
    ['天中殺', '12年に2年ある「種まきより整理に向く時期」。本鑑定では現在の星の暗示として記載。'],
    ['神秘十字', '手相で知能線と感情線の間に十字が現れる相。霊的素質や直観の鋭さの徴とされる。'],
    ['印堂(いんどう)', '人相用語で眉と眉の間。明るく開いていると判断力と運の良さの徴とされる。'],
  ];
  return terms.map(([k, v]) =>
    `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`
  ).join('');
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

  const planPath = path.join(workdir, 'kantei_plain.json');
  if (!fs.existsSync(planPath)) {
    console.error(`kantei_plain.json not found at ${planPath}`);
    process.exit(1);
  }
  const kantei = JSON.parse(fs.readFileSync(planPath, 'utf-8'));
  const modules = JSON.parse(fs.readFileSync(path.join(workdir, 'modules.json'), 'utf-8'));
  const subject = JSON.parse(fs.readFileSync(path.join(workdir, 'subject.json'), 'utf-8'));

  const tpl = fs.readFileSync(path.join(repoRoot, 'templates', 'kantei_plain.html'), 'utf-8');

  const coverPath = path.join(workdir, 'images', 'cover.png');
  const coverUri = fs.existsSync(coverPath)
    ? 'data:image/png;base64,' + fs.readFileSync(coverPath).toString('base64')
    : '';

  const m = modules.modules || {};
  const html = fillTemplate(tpl, {
    COVER_IMAGE: coverUri,
    NAME_KANJI: esc(subject.name_kanji),
    BIRTH_DATE: esc(subject.birth_date),
    BIRTH_TIME: subject.birth_time_known ? esc(subject.birth_time) : '時刻不明',
    BIRTH_PLACE: esc(subject.birth_place),
    ISSUED_AT: esc(kantei.issued_at || new Date().toISOString().slice(0, 10)),
    INTRO: esc(kantei.intro || ''),
    HEADLINE: esc(kantei.headline || ''),
    CONSTITUTION: esc(kantei.constitution || ''),
    VISION_SUMMARY: esc(kantei.vision_summary || '（人相・手相のデータがありません）'),
    MISSION_ITEMS: renderItems(kantei.mission),
    TALENTS_ITEMS: renderItems(kantei.talents),
    TODO_ITEMS: renderItems(kantei.todo_now),
    WARNING_ITEMS: renderItems(kantei.warnings),
    FOUR_PILLARS: renderFourPillars(m.shichu),
    SHICHU_SUMMARY: esc(m.shichu?.summary || '—'),
    KYUSEI_GRID: renderKyuseiGrid(m.kyusei),
    KYUSEI_SUMMARY: esc(m.kyusei?.summary || '—'),
    MAYA_BLOCK: renderMayaBlock(m.maya),
    OTHER_MODULE_SECTIONS: renderOtherModuleCards(m, ['shichu', 'kyusei', 'maya', 'biorhythm']),
    LIFE_PHASES_ROWS: renderLifePhases(kantei.life_phases),
    BIORHYTHM_SVG: renderBiorhythmSVG(m.biorhythm),
    LUCKY_GRID: renderLucky(kantei.lucky),
    GLOSSARY: renderGlossary(),
    CLOSING: esc(kantei.closing || ''),
  });

  fs.writeFileSync(path.join(workdir, 'kantei_plain.html'), html, 'utf-8');
  console.log(`HTML: ${path.join(workdir, 'kantei_plain.html')}`);

  const browser = await puppeteer.launch({ headless: 'new' });
  try {
    const page = await browser.newPage();
    await page.setContent(html, { waitUntil: 'networkidle0' });

    const pdfPath = path.join(workdir, 'kantei_plain.pdf');
    await page.pdf({
      path: pdfPath,
      format: 'A4',
      printBackground: true,
      margin: { top: 0, bottom: 0, left: 0, right: 0 },
    });
    console.log(`PDF:  ${pdfPath}`);

    await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 2 });
    await page.setContent(html, { waitUntil: 'networkidle0' });
    const pngPath = path.join(workdir, 'kantei_plain.png');
    await page.screenshot({ path: pngPath, fullPage: true });
    console.log(`PNG:  ${pngPath}`);
  } finally {
    await browser.close();
  }
}

main().catch(e => { console.error(e); process.exit(1); });
