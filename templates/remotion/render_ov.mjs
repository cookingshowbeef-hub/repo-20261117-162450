// Render the graphics in 05_Renders/overlays.json (or $DOC_OUT/overlays.json) -> ../render/ov/<id>_<kind>.mov (ProRes 4444, alpha)
//   node render_ov.mjs              all
//   node render_ov.mjs stills       one test frame each (after its last beat), over a grey checker -> ../render/ov/stills/
//   node render_ov.mjs O03 O14 ...  only these
import {bundle} from '@remotion/bundler';
import {renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PRJ = path.join(HERE, '..', '..');
const OUT = path.join(HERE, '..', 'render', 'ov');
fs.mkdirSync(path.join(OUT, 'stills'), {recursive: true});
const ovs = JSON.parse(fs.readFileSync(path.join(process.env.DOC_OUT || path.join(PRJ, '05_Renders'), 'overlays.json'), 'utf8'));
const args = process.argv.slice(2);
const stills = args[0] === 'stills';
const pick = ovs.filter((o) => !args.length || stills ? (args.length < 2 || args.includes(o.id)) : args.includes(o.id));
const serveUrl = await bundle({entryPoint: path.join(HERE, 'src', 'index.jsx')});
let done = 0;
for (const o of pick) {
  const comp = await selectComposition({serveUrl, id: 'Gfx', inputProps: o.p});
  const name = `${o.id}_${o.kind}`;
  if (stills) {
    const f = Math.min(comp.durationInFrames - 20, Math.round((Math.max(...o.p.at) + 1.6) * 30));
    await renderStill({serveUrl, composition: comp, inputProps: o.p, frame: Math.max(0, f), imageFormat: 'png', output: path.join(OUT, 'stills', `${name}.png`)});
    continue;
  }
  const t0 = Date.now();
  await renderMedia({serveUrl, composition: comp, inputProps: o.p, outputLocation: path.join(OUT, name + '.mov'), concurrency: 6,
    codec: 'prores', proResProfile: '4444', imageFormat: 'png', pixelFormat: 'yuva444p10le'});
  console.log(`${name} ${comp.durationInFrames}f ${((Date.now() - t0) / 1000).toFixed(0)}s  (${++done}/${pick.length})`);
}
console.log(`${pick.length} overlays done`);
