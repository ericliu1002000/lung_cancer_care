const fs = require('fs');
const path = require('path');

function readText(p) {
  return fs.readFileSync(p, 'utf8');
}

function fail(msg) {
  console.error(msg);
  process.exitCode = 1;
}

function main() {
  const root = path.resolve(__dirname, '..');
  const htmlPath = path.join(root, 'templates', 'web_patient', 'review_record_detail.html');
  const cssPath = path.join(root, 'static', 'web_patient', 'review_record_detail.css');
  const jsPath = path.join(root, 'static', 'web_patient', 'review_record_detail.js');

  const html = readText(htmlPath);
  const css = readText(cssPath);
  const js = readText(jsPath);

  if (/rrd-skeleton/.test(html) || /rrd-skeleton/.test(css) || /rrd-skeleton/.test(js)) {
    fail('[lint:html] 禁止包含骨架屏相关标识 rrd-skeleton');
  }

  if (/rrd-skeleton-card/.test(html) || /rrd-skeleton-card/.test(css) || /rrd-skeleton-card/.test(js)) {
    fail('[lint:html] 禁止包含骨架屏相关样式 rrd-skeleton-card');
  }

  if (/rrd-shimmer/.test(css) || /shimmer/.test(css)) {
    fail('[lint:html] 禁止包含骨架屏 shimmer 动画');
  }

  if (!/grid-cols-3/.test(js) && !/grid-cols-3/.test(html)) {
    fail('[lint:html] 复查详情图片栅格需为三列（grid-cols-3）');
  }

  if (/class="[^"]*p-4[^"]*pb-20/.test(html)) {
    fail('[lint:html] 列表容器不应包含额外左右外边距（p-4）');
  }

  if (!process.exitCode) {
    console.log('[lint:html] OK');
  }
}

main();

