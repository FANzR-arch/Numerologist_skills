// 用开源紫微斗数库 iztro 重新生成 iztro_cases.json 中每个盘例的期望值，用于独立核对。
//
//   npm install iztro@2.6.2
//   node gen_iztro_cases.cjs iztro_cases.json
//
// 只读取每个 case 的 input（公历出生时间 + 性别），覆盖写入 iztro 字段。
// 重新生成后 git diff 应为空；若有差异，说明脚本或 iztro 口径发生了变化。
// 闰月用 iztro 默认 fixLeap=true（闰月十五日及以前按本月，十六日起按下月），
// 对应 ziwei_cli.py 的 leap_month_rule=split_15。盘例不含 23 点（晚子时）出生。
const fs = require('fs');
const { astro } = require('iztro');

const BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];
const STARS = [
  '紫微', '天机', '太阳', '武曲', '天同', '廉贞', '天府', '太阴', '贪狼', '巨门', '天相', '天梁', '七杀', '破军',
  '文昌', '文曲', '左辅', '右弼', '天魁', '天钺', '禄存', '擎羊', '陀罗', '火星', '铃星', '地空', '地劫', '天马',
  '天刑', '天姚', '红鸾', '天喜', '天哭', '天虚',
];

const path = process.argv[2];
const fixture = JSON.parse(fs.readFileSync(path, 'utf8'));
fixture.generator = `iztro@${require('iztro/package.json').version}`;
for (const c of fixture.cases) {
  const [d, t] = c.input.birth_time.split(' ');
  const hour = Number(t.split(':')[0]);
  if (hour === 23) throw new Error('fixture 不收 23 点出生的盘例');
  const timeIndex = Math.floor((hour + 1) / 2);
  const [y, m, day] = d.split('-').map(Number);
  const a = astro.bySolar(`${y}-${m}-${day}`, timeIndex, c.input.gender, true, 'zh-CN');
  const stars = {};
  const sihua = {};
  const byBranch = {};
  for (const p of a.palaces) {
    byBranch[p.earthlyBranch] = p;
    for (const s of [...p.majorStars, ...p.minorStars, ...p.adjectiveStars]) {
      if (STARS.includes(s.name)) stars[s.name] = p.earthlyBranch;
      if (s.mutagen) sihua[s.name] = s.mutagen;
    }
  }
  c.iztro = {
    lunar: a.lunarDate,
    ming: a.earthlyBranchOfSoulPalace,
    shen: a.earthlyBranchOfBodyPalace,
    ju: a.fiveElementsClass,
    ming_zhu: a.soul,
    shen_zhu: a.body,
    stars: Object.fromEntries(STARS.map((s) => [s, stars[s]])),
    sihua,
    stems: BRANCHES.map((b) => byBranch[b].heavenlyStem).join(''),
    decadal_starts: BRANCHES.map((b) => byBranch[b].decadal.range[0]),
  };
}
// 一个盘例一行，便于 git diff 逐例比对
const { cases, ...meta } = fixture;
const head = Object.entries(meta).map(([k, v]) => `  ${JSON.stringify(k)}: ${JSON.stringify(v)}`).join(',\n');
const body = cases.map((c) => `    ${JSON.stringify(c)}`).join(',\n');
fs.writeFileSync(path, `{\n${head},\n  "cases": [\n${body}\n  ]\n}\n`);
