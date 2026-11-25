// The film's edit style for the graphics: src/style.json is written by the engine from styles/<film.json "style">.json
// (doc.py <prj> gfx / new). Change the look in the style or in film.json "gfx", not here.
import {Easing} from 'remotion';
import S from './style.json';

const P = S.palette || {};
const fam = (f, d) => (f ? `"${f.family}", ${f.fallback || d}` : d);
export const PAL = {text: '#EEF1F4', dim: '#AEB8C2', accent: '#6FAEDB', accent_text: '#A9D6F5', danger: '#E0563F', danger_text: '#EE6A50',
  warm: '#E8A15A', bg: '#0B0E12', land: '#1E252D', sea: '#0B0E12', ...P};
const F = S.fonts || {};
export const SANS = fam(F.sans, 'sans-serif'), SERIF = fam(F.serif, 'Georgia, serif'), MONO = fam(F.mono, '"Courier New", monospace');
export const FONT_FILES = Object.values(F).flatMap((f) => (f.files || []).map((x) => ({family: f.family, ...x})));
const M = S.motion || {};
export const OUT = Easing.bezier(...(M.ease_out || [0.16, 1, 0.3, 1]));
export const INOUT = Easing.bezier(...(M.ease_inout || [0.65, 0, 0.35, 1]));
export const RISE = {dy: 22, blur: 7, len: 0.9, ...(M.rise || {})};
const TRACK = M.tracking ?? 1;
export const em = (x) => `${(x * TRACK).toFixed(3)}em`;            // letter-spacing scaled by the style's tracking
export const SH = S.text_shadow ?? '0 2px 22px rgba(0,0,0,0.75), 0 1px 3px rgba(0,0,0,0.6)';
export const GRAIN_K = (S.grain ?? 0.06) / 0.06;                    // film grain relative to the house default
export const SCRIM = S.scrim ?? 1;                                    // darkness of the scrims behind text on footage
