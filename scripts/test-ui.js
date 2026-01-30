const fs = require('fs');
const path = require('path');

function readText(p) {
  return fs.readFileSync(p, 'utf8');
}

function getSpecArg() {
  const argv = process.argv.slice(2);
  for (const item of argv) {
    if (item.startsWith('--spec=')) return item.slice('--spec='.length);
  }
  return '';
}

function assert(cond, msg) {
  if (!cond) {
    console.error(`[test:ui] ${msg}`);
    process.exit(1);
  }
}

function main() {
  const spec = getSpecArg();
  assert(spec === 'review_record_detail', '仅支持 --spec=review_record_detail');

  const root = path.resolve(__dirname, '..');
  const htmlPath = path.join(root, 'templates', 'web_patient', 'review_record_detail.html');
  const cssPath = path.join(root, 'static', 'web_patient', 'review_record_detail.css');
  const jsPath = path.join(root, 'static', 'web_patient', 'review_record_detail.js');

  const html = readText(htmlPath);
  const css = readText(cssPath);
  const js = readText(jsPath);

  assert(!/rrd-skeleton/.test(html), '页面不得包含骨架屏 DOM（rrd-skeleton）');
  assert(!/rrd-skeleton-card/.test(css), '页面不得包含骨架屏样式（rrd-skeleton-card）');
  assert(/grid-cols-3/.test(js) || /grid-cols-3/.test(html), '图片栅格需为三列（grid-cols-3）');
  assert(/gap-2/.test(js) || /gap-2/.test(html), '图片间距需为 8px（gap-2）');
  assert(/loading="lazy"/.test(js) || /loading="lazy"/.test(html), '首屏图片需启用懒加载（loading="lazy"）');
  assert(/PerformanceObserver/.test(js), '需包含 PerformanceObserver 上报逻辑');
  assert(!/\?\./.test(js), '为兼容性要求禁止使用可选链（?.）');

  console.log('[test:ui] OK');
}

main();

