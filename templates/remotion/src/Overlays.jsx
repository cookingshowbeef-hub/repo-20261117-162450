// PAGPAG overlays: transparent graphics laid over the footage, timed to the narration.
// Every component gets {dur, at:[s...]} (beat times relative to its start) plus its own text props.
import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from 'remotion';
import {PAL, SANS, SERIF, MONO, OUT, INOUT, RISE, em, SH, GRAIN_K, SCRIM} from './style';

const FPS = 30;
const k = (t, a, b, from = 0, to = 1, e = OUT) => interpolate(t, [a, b], [from, to], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: e});
const BONE = PAL.text, DIM = PAL.dim, RUST = PAL.accent, RED = PAL.danger, ACC = PAL.accent_text, RED_T = PAL.danger_text;   // from the film's style (RUST = accent lines; ACC/RED_T = accent text on footage)
const useT = () => useCurrentFrame() / FPS;

// whole-overlay envelope
const Env = ({dur, children, fin = 0.35, fout = 0.5}) => {
  const t = useT();
  return <AbsoluteFill style={{opacity: Math.min(k(t, 0, fin, 0, 1, INOUT), 1 - k(t, dur - fout, dur, 0, 1, INOUT))}}>{children}</AbsoluteFill>;
};
const ScrimLeft = ({w = 64, o = 0.78 * SCRIM}) => (
  <AbsoluteFill style={{background: `linear-gradient(90deg, rgba(0,0,0,${o}) 0%, rgba(0,0,0,${o * 0.6}) ${w * 0.55}%, rgba(0,0,0,0) ${w}%)`}} />
);
const ScrimRight = ({o = 0.75 * SCRIM}) => (
  <AbsoluteFill style={{background: `linear-gradient(270deg, rgba(0,0,0,${o}) 0%, rgba(0,0,0,${o * 0.6}) 30%, rgba(0,0,0,0) 58%)`}} />
);
const ScrimTop = ({h = 330, o = 0.74 * SCRIM}) => (
  <AbsoluteFill style={{background: `linear-gradient(180deg, rgba(0,0,0,${o}) 0px, rgba(0,0,0,${o}) ${h * 0.58}px, rgba(0,0,0,${o * 0.35}) ${h * 0.8}px, rgba(0,0,0,0) ${h}px)`}} />
);
const ScrimCenter = ({o = 0.55 * SCRIM}) => (
  <AbsoluteFill style={{background: `radial-gradient(ellipse 70% 60% at 50% 50%, rgba(0,0,0,${o}) 0%, rgba(0,0,0,${o * 0.55}) 55%, rgba(0,0,0,${o * 0.25}) 100%)`}} />
);

// text that rises softly into place at time `at`
const Rise = ({at = 0, children, style, dy = RISE.dy, blur = RISE.blur, len = RISE.len}) => {
  const t = useT();
  const u = k(t, at, at + len);
  return <div style={{opacity: u, transform: `translateY(${(1 - u) * dy}px)`, filter: `blur(${(1 - u) * blur}px)`, textShadow: SH, ...style}}>{children}</div>;
};
const Rule = ({at = 0, w = 80, color = RUST, style}) => {
  const t = useT();
  return <div style={{width: w * k(t, at, at + 0.8), height: 2, background: color, boxShadow: '0 1px 6px rgba(0,0,0,0.5)', ...style}} />;
};
const Kicker = ({at = 0, children, color = ACC, size = 26}) => (
  <Rise at={at} style={{fontFamily: SANS, fontWeight: 500, fontSize: size, letterSpacing: em(0.42), color}}>{children}</Rise>
);

// ---------------------------------------------------------------- dictionary entry
const Define = ({dur, at, word, pron, senses, lang = 'FILIPINO'}) => {
  const t = useT();
  return (
    <Env dur={dur}>
      <ScrimLeft w={66} />
      <div style={{position: 'absolute', left: 120, top: 300, width: 900}}>
        <Kicker at={at[0] - 0.15}>{lang}</Kicker>
        <Rise at={at[0]} style={{fontFamily: SERIF, fontSize: 132, color: BONE, lineHeight: 1.1, marginTop: 10}}>{word}</Rise>
        <Rise at={at[0] + 0.35} style={{fontFamily: SANS, fontSize: 30, color: DIM, letterSpacing: em(0.18)}}>/ {pron} /</Rise>
        <Rule at={at[0] + 0.5} w={90} style={{margin: '26px 0 26px'}} />
        {senses.map(([pos, txt], i) => {
          const a = (at[i] ?? at[0]) + (i === 0 ? 0.8 : 0.1);
          const dimmed = senses.length > 1 && i < senses.length - 1 ? 1 - 0.5 * k(t, at[i + 1], at[i + 1] + 0.6) : 1;
          return (
            <div key={i} style={{display: 'flex', gap: 22, marginBottom: 22, opacity: dimmed}}>
              <Rise at={a} style={{fontFamily: SANS, fontWeight: 500, fontSize: 30, color: ACC, minWidth: 26}}>{i + 1}</Rise>
              <div>
                <Rise at={a + 0.1} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 30, color: DIM}}>{pos}</Rise>
                <Rise at={a + 0.25} style={{fontFamily: SANS, fontSize: 40, color: BONE, lineHeight: 1.3, maxWidth: 780}}>{txt}</Rise>
              </div>
            </div>
          );
        })}
      </div>
    </Env>
  );
};

// ---------------------------------------------------------------- big number / phrase
const Stat = ({dur, at, big, sub, src, size = 150, red}) => (
  <Env dur={dur}>
    <ScrimLeft w={64} />
    <div style={{position: 'absolute', left: 120, top: 0, bottom: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center', width: 1100}}>
      <Rule at={at[0]} w={70} color={red ? RED : RUST} style={{marginBottom: 22}} />
      <Rise at={at[0] + 0.05} dy={30} blur={10} len={1.0}
        style={{fontFamily: SANS, fontWeight: 300, fontSize: size, color: red ? RED_T : BONE, lineHeight: 1.02, letterSpacing: em(0.03)}}>{big}</Rise>
      <Rise at={at[0] + 0.45} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 44, color: BONE, marginTop: 18, maxWidth: 980, lineHeight: 1.3}}>{sub}</Rise>
      {src && <Rise at={at[0] + 0.9} style={{fontFamily: SANS, fontSize: 22, color: DIM, letterSpacing: em(0.2), marginTop: 18}}>SOURCE: {src}</Rise>}
    </div>
  </Env>
);

// ---------------------------------------------------------------- act title
const Chapter = ({dur, at, part, title, small}) => {
  const t = useT();
  if (small) return (
    <Env dur={dur}>
      <ScrimTop h={330} o={0.5} />
      <div style={{position: 'absolute', left: 92, top: 70, padding: '22px 34px 26px 28px', background: 'rgba(13,12,11,0.8)', opacity: k(t, at[0], at[0] + 0.5)}}>
        <Kicker at={at[0]} size={24}>{part}</Kicker>
        <Rule at={at[0] + 0.25} w={60} style={{margin: '16px 0 14px'}} />
        <Rise at={at[0] + 0.4} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 52, color: BONE}}>{title}</Rise>
      </div>
    </Env>
  );
  const sp = k(t, at[0], dur, 0.42, 0.5, Easing.linear);
  return (
    <Env dur={dur} fin={0.6} fout={0.7}>
      <AbsoluteFill style={{background: 'rgba(0,0,0,0.42)'}} />
      <ScrimCenter o={0.35} />
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
        <Rise at={at[0]} style={{fontFamily: SANS, fontWeight: 500, fontSize: 28, letterSpacing: `${sp}em`, color: ACC, paddingLeft: `${sp}em`}}>{part}</Rise>
        <Rule at={at[0] + 0.35} w={110} style={{margin: '26px 0 30px'}} />
        <Rise at={at[0] + 0.6} dy={26} blur={10} len={1.3} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 92, color: BONE, textAlign: 'center'}}>{title}</Rise>
      </AbsoluteFill>
    </Env>
  );
};

// ---------------------------------------------------------------- history timeline along the top
// steps: [where the marker starts, where it is after beat 0, after beat 1, ...]
const Timeline = ({dur, at, marks, steps}) => {
  const t = useT();
  const x0 = 200, x1 = 1720, y = 128, n = marks.length;
  const X = (i) => x0 + ((x1 - x0) * i) / (n - 1);
  let pos = steps[0], cur = steps[0];
  at.forEach((a, i) => { const u = k(t, a, a + 1.1, 0, 1, INOUT); pos = pos + (steps[i + 1] - pos) * u; if (t >= a + 0.35) cur = steps[i + 1]; });
  const draw = k(t, 0, 0.9, 0, 1, INOUT);
  const lastChange = Math.max(0, ...at.filter((a) => t >= a + 0.35).map((a) => a + 0.35));
  const lab = k(t, lastChange, lastChange + 0.7);
  return (
    <Env dur={dur}>
      <ScrimTop h={330} />
      <svg width="1920" height="300" style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
        <line x1={x0} y1={y} x2={x0 + (x1 - x0) * draw} y2={y} stroke="rgba(238,231,219,0.55)" strokeWidth="2" />
        {marks.map(([yr], i) => {
          const o = k(t, 0.2 + i * 0.06, 0.6 + i * 0.06);
          const near = Math.max(0, 1 - Math.abs(pos - i));
          return (
            <g key={i} opacity={o}>
              <line x1={X(i)} y1={y - 9} x2={X(i)} y2={y + 9} stroke="rgba(238,231,219,0.7)" strokeWidth="2" />
              <text x={X(i)} y={y - 24} textAnchor="middle" fontFamily={SANS} fontSize={24 + 4 * near} fill={near > 0.5 ? BONE : 'rgba(238,231,219,0.6)'}
                letterSpacing="2" style={{filter: 'drop-shadow(0 1px 4px rgba(0,0,0,0.8))'}}>{yr}</text>
            </g>
          );
        })}
        <circle cx={X(pos)} cy={y} r={11} fill={RUST} opacity={k(t, 0.3, 0.7)} />
        <circle cx={X(pos)} cy={y} r={11 + 14 * ((t * 0.9) % 1)} fill="none" stroke={RUST} strokeWidth="2" opacity={k(t, 0.3, 0.7) * (1 - ((t * 0.9) % 1))} />
      </svg>
      <div style={{position: 'absolute', top: y + 34, left: Math.max(100, Math.min(1260, X(pos) - 280)), width: 560, textAlign: 'center', opacity: lab,
        transform: `translateY(${(1 - lab) * 10}px)`}}>
        <div style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 34, color: BONE, textShadow: SH}}>{marks[cur][1]}</div>
      </div>
    </Env>
  );
};

// ---------------------------------------------------------------- lines of type, centre
const Words = ({dur, at, lines, accent_last}) => (
  <Env dur={dur}>
    <ScrimCenter o={0.66} />
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
      {lines.map((l, i) => (
        <Rise key={i} at={at[i] ?? at[0] + i * 1.0} dy={26} blur={9} len={1.0}
          style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 84, lineHeight: 1.3, color: accent_last && i === lines.length - 1 ? ACC : BONE, textAlign: 'center'}}>{l}</Rise>
      ))}
    </AbsoluteFill>
  </Env>
);

const Quote = ({dur, at, lines, by}) => (
  <Env dur={dur}>
    <ScrimCenter o={0.68} />
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', padding: '0 180px'}}>
      <Rule at={at[0]} w={70} style={{marginBottom: 34}} />
      {lines.map((l, i) => (
        <Rise key={i} at={at[i] ?? at[0] + 0.5 + i * 0.9} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 62, lineHeight: 1.35, color: BONE, textAlign: 'center'}}>{l}</Rise>
      ))}
      {by && <Rise at={at[0] + 1.6} style={{fontFamily: SANS, fontSize: 22, letterSpacing: em(0.3), color: DIM, marginTop: 30}}>{by}</Rise>}
    </AbsoluteFill>
  </Env>
);

// ---------------------------------------------------------------- list that builds on the words
const List = ({dur, at, head, items, accent_last, red}) => {
  const t = useT();
  const big = items.length <= 4 ? 54 : 48;
  return (
    <Env dur={dur}>
      <ScrimLeft w={60} />
      <div style={{position: 'absolute', left: 120, top: 0, bottom: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center'}}>
        <Kicker at={at[0] - 0.2} color={red ? RED_T : ACC}>{head}</Kicker>
        <Rule at={at[0]} w={80} color={red ? RED : RUST} style={{margin: '18px 0 26px'}} />
        {items.map((it, i) => {
          const a = at[i] ?? at[at.length - 1] + 0.4 * (i - at.length + 1);
          const last = accent_last && i === items.length - 1;
          const settle = i < items.length - 1 && at[i + 1] !== undefined ? 1 - 0.35 * k(t, at[i + 1], at[i + 1] + 0.5) : 1;
          return (
            <div key={i} style={{display: 'flex', alignItems: 'center', gap: 24, marginBottom: 14, opacity: settle}}>
              <div style={{width: 22 * k(t, a, a + 0.5), height: 3, background: red ? RED : RUST, boxShadow: '0 1px 6px rgba(0,0,0,0.5)'}} />
              <Rise at={a} dy={0} style={{fontFamily: last ? SERIF : SANS, fontStyle: last ? 'italic' : 'normal', fontWeight: last ? 400 : 400, fontSize: last ? big + 4 : big,
                color: last ? ACC : red ? '#F1D5C9' : BONE, transform: `translateX(${(1 - k(t, a, a + 0.8)) * -24}px)`}}>{it}</Rise>
            </div>
          );
        })}
      </div>
    </Env>
  );
};

// ---------------------------------------------------------------- hapilan -> HAPPYLAND
const Etym = ({dur, at, src, lang, gloss, dst}) => {
  const t = useT();
  const m = k(t, at[2], at[3] + 0.5, 0, 1, INOUT);
  return (
    <Env dur={dur}>
      <ScrimLeft w={64} />
      <div style={{position: 'absolute', left: 120, top: 330, width: 1100}}>
        <Kicker at={at[0] - 0.2}>{lang.toUpperCase()}</Kicker>
        <div style={{position: 'relative', height: 160, marginTop: 8}}>
          <div style={{position: 'absolute', opacity: 1 - m, filter: `blur(${m * 12}px)`, transform: `translateY(${-m * 20}px)`}}>
            <Rise at={at[0]} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 140, color: BONE, lineHeight: 1.1}}>{src}</Rise>
          </div>
          <div style={{position: 'absolute', display: 'flex', top: 18}}>
            {[...dst].map((c, i) => {
              const u = k(t, at[2] + 0.25 + i * 0.07, at[2] + 0.85 + i * 0.07);
              return <span key={i} style={{fontFamily: SANS, fontWeight: 300, fontSize: 124, color: ACC, letterSpacing: em(0.12), opacity: u, textShadow: SH,
                filter: `blur(${(1 - u) * 10}px)`, display: 'inline-block', transform: `translateY(${(1 - u) * 24}px)`}}>{c}</span>;
            })}
          </div>
        </div>
        <Rule at={at[0] + 0.4} w={90} style={{margin: '26px 0 22px'}} />
        <div style={{position: 'relative', height: 60}}>
          <div style={{position: 'absolute', opacity: 1 - m}}>
            <Rise at={at[1]} style={{fontFamily: SANS, fontSize: 44, color: BONE}}>“{gloss}”</Rise>
          </div>
          <div style={{position: 'absolute', opacity: k(t, at[3] + 0.3, at[3] + 1.0)}}>
            <Rise at={at[3] + 0.3} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 40, color: DIM}}>{src}  →  {gloss}  →  {dst.toLowerCase().replace(/^./, (c) => c.toUpperCase())}</Rise>
          </div>
        </div>
      </div>
    </Env>
  );
};

// ---------------------------------------------------------------- a good day / a bad day
const Daybook = ({dur, at, rows}) => {
  const t = useT();
  return (
    <Env dur={dur}>
      <ScrimLeft w={60} />
      <div style={{position: 'absolute', left: 120, top: 0, bottom: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 40}}>
        {rows.map(([amt, lab, sub], i) => {
          const a = at[i];
          const bad = i === rows.length - 1 && rows.length > 1;
          const fade = i < rows.length - 1 ? 1 - 0.55 * k(t, at[i + 1], at[i + 1] + 0.6) : 1;
          return (
            <div key={i} style={{display: 'flex', alignItems: 'center', gap: 44, opacity: fade}}>
              <Rise at={a} dy={30} blur={10} style={{fontFamily: SANS, fontWeight: 300, fontSize: 168, color: bad ? RED_T : BONE, minWidth: 380, lineHeight: 1}}>{amt}</Rise>
              <div>
                <Rise at={a + 0.3} style={{fontFamily: SANS, fontWeight: 500, fontSize: 30, letterSpacing: em(0.38), color: bad ? RED_T : ACC}}>{lab}</Rise>
                <Rise at={a + 0.6} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 38, color: BONE, marginTop: 10}}>{sub}</Rise>
              </div>
            </div>
          );
        })}
      </div>
    </Env>
  );
};

// ---------------------------------------------------------------- a room smaller than a parking space
const Parking = ({dur, at}) => {
  const t = useT();
  const s = 92;                                         // px per metre
  const W = 2.5 * s, H = 5 * s, x = 190, y = 300;
  const d = k(t, at[0], at[0] + 1.2, 0, 1, INOUT);
  const per = 2 * (W + H);
  const r = k(t, at[1], at[1] + 1.2, 0, 1, INOUT);
  const rw = 1.9 * s, rh = 3.4 * s;
  return (
    <Env dur={dur}>
      <ScrimLeft w={68} o={0.84} />
      <svg width="1920" height="1080" style={{position: 'absolute', left: 0, top: 0}}>
        <rect x={x} y={y} width={W} height={H} fill="none" stroke={BONE} strokeWidth="4" strokeDasharray={`${per * d} ${per}`} />
        <g opacity={k(t, at[0] + 0.8, at[0] + 1.4)} fontFamily={SANS} fill={DIM} fontSize="26">
          <text x={x + W / 2} y={y - 22} textAnchor="middle">2.5 m</text>
          <text x={x - 22} y={y + H / 2} textAnchor="end" dominantBaseline="middle">5 m</text>
        </g>
        <rect x={x + (W - rw) / 2} y={y + H - rh - 30} width={rw} height={rh * r} fill={RUST} fillOpacity="0.5" stroke={RUST} strokeWidth="3" opacity={r > 0 ? 1 : 0} />
      </svg>
      <div style={{position: 'absolute', left: x + W + 60, top: y + 10, width: 560}}>
        <Rise at={at[0] + 0.5} style={{fontFamily: SANS, fontWeight: 500, fontSize: 26, letterSpacing: em(0.35), color: BONE}}>A PARKING SPACE</Rise>
        <Rise at={at[0] + 0.8} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 34, color: DIM, marginTop: 8}}>about 12.5 m²</Rise>
        <Rise at={at[1] + 0.6} style={{fontFamily: SANS, fontWeight: 500, fontSize: 26, letterSpacing: em(0.35), color: ACC, marginTop: 150}}>ONE ROOM</Rise>
        <Rise at={at[1] + 0.9} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 34, color: BONE, marginTop: 8}}>a whole family, smaller still</Rise>
      </div>
    </Env>
  );
};

// ---------------------------------------------------------------- utilities checklist
const Checks = ({dur, at, rows}) => (
  <Env dur={dur}>
    <ScrimLeft w={60} />
    <div style={{position: 'absolute', left: 120, top: 0, bottom: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 34}}>
      {rows.map(([lab, txt], i) => (
        <div key={i}>
          <Rise at={at[i]} style={{fontFamily: SANS, fontWeight: 500, fontSize: 30, letterSpacing: em(0.38), color: ACC}}>{lab}</Rise>
          <Rule at={at[i] + 0.15} w={60} color="rgba(238,231,219,0.5)" style={{margin: '10px 0 10px'}} />
          <Rise at={at[i] + 0.3} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 46, color: BONE}}>{txt}</Rise>
        </div>
      ))}
    </div>
  </Env>
);

// ---------------------------------------------------------------- the chain from bin to plate, along the top
const Process = ({dur, at, steps, at_step}) => {
  const t = useT();
  const x0 = 210, x1 = 1710, y = 120, n = steps.length;
  const X = (i) => x0 + ((x1 - x0) * i) / (n - 1);
  const p = at_step - 1 + k(t, at[0], at[0] + 0.9, 0, 1, INOUT);
  return (
    <Env dur={dur}>
      <ScrimTop h={300} />
      <svg width="1920" height="260" style={{position: 'absolute', left: 0, top: 0}}>
        <line x1={x0} y1={y} x2={x1} y2={y} stroke="rgba(238,231,219,0.28)" strokeWidth="2" />
        {p > 0 && <line x1={x0} y1={y} x2={X(Math.max(0, p))} y2={y} stroke={RUST} strokeWidth="3" />}
        {steps.map((s, i) => {
          const done = i <= p + 0.001;
          const cur = i === at_step;
          const on = cur ? k(t, at[0] + 0.5, at[0] + 1.0) : done ? 1 : 0;
          return (
            <g key={i}>
              <circle cx={X(i)} cy={y} r={cur ? 9 + 4 * on : 7} fill={on > 0.5 ? RUST : '#1a1816'} stroke={on > 0.5 ? RUST : 'rgba(238,231,219,0.55)'} strokeWidth="2" />
              {cur && <circle cx={X(i)} cy={y} r={13 + 16 * ((t * 0.9) % 1)} fill="none" stroke={RUST} strokeWidth="2" opacity={on * (1 - ((t * 0.9) % 1))} />}
              <text x={X(i)} y={y + 52} textAnchor="middle" fontFamily={SANS} fontWeight={cur ? 500 : 400} fontSize={cur ? 30 : 22} letterSpacing={cur ? 6 : 4}
                fill={cur ? BONE : done ? 'rgba(238,231,219,0.7)' : 'rgba(238,231,219,0.35)'} opacity={cur ? 0.35 + 0.65 * on : 1}
                style={{filter: 'drop-shadow(0 1px 4px rgba(0,0,0,0.85))'}}>{s}</text>
            </g>
          );
        })}
      </svg>
    </Env>
  );
};

// ---------------------------------------------------------------- 1 bag + 1 cup of rice = 1 child
const Equation = ({dur, at, rows}) => (
  <Env dur={dur}>
    <ScrimLeft w={66} />
    <div style={{position: 'absolute', left: 110, top: 0, bottom: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 44, width: 540}}>
      {rows.map((r, i) => (
        <div key={i}>
          {r.map((c, j) => c && (
            <Rise key={j} at={at[i] + j * 0.55} style={{fontFamily: j === 2 ? SERIF : SANS, fontStyle: j === 2 ? 'italic' : 'normal', fontWeight: j === 0 ? 300 : 400,
              fontSize: j === 0 ? 96 : 46, lineHeight: 1.15, color: j === 2 ? ACC : BONE, whiteSpace: 'nowrap'}}>{c}</Rise>
          ))}
        </div>
      ))}
    </div>
  </Env>
);

// ---------------------------------------------------------------- hours out in the heat
const Clock = ({dur, at, items, big, sub}) => {
  const t = useT();
  const r = 92, cx = 240, cy = 360;
  const sweep = k(t, at[0], at[4] + 0.8, 0, 0.999, Easing.bezier(0.4, 0, 0.6, 1));
  const ang = sweep * 2 * Math.PI * 1.0;
  const ex = cx + r * Math.sin(ang), ey = cy - r * Math.cos(ang);
  const hand = k(t, at[0], at[4] + 0.8, 0, 6 * 360, Easing.bezier(0.4, 0, 0.6, 1));
  return (
    <Env dur={dur}>
      <ScrimLeft w={62} />
      <svg width="600" height="600" style={{position: 'absolute', left: 0, top: 0, opacity: k(t, 0.1, 0.6)}}>
        <circle cx={cx} cy={cy} r={r} fill="rgba(0,0,0,0.35)" stroke="rgba(238,231,219,0.6)" strokeWidth="3" />
        {sweep > 0.002 && <path d={`M${cx},${cy} L${cx},${cy - r} A${r},${r} 0 ${sweep > 0.5 ? 1 : 0} 1 ${ex},${ey} Z`} fill={RUST} opacity="0.75" />}
        {Array.from({length: 12}, (_, i) => { const a = (i / 12) * 2 * Math.PI; return <line key={i} x1={cx + (r - 12) * Math.sin(a)} y1={cy - (r - 12) * Math.cos(a)}
          x2={cx + r * Math.sin(a)} y2={cy - r * Math.cos(a)} stroke={BONE} strokeWidth="2" />; })}
        <line x1={cx} y1={cy} x2={cx + (r - 22) * Math.sin((hand * Math.PI) / 180)} y2={cy - (r - 22) * Math.cos((hand * Math.PI) / 180)} stroke={BONE} strokeWidth="4" strokeLinecap="round" />
        <circle cx={cx} cy={cy} r={6} fill={BONE} />
      </svg>
      <div style={{position: 'absolute', left: 400, top: 262}}>
        {items.map((it, i) => (
          <Rise key={i} at={at[i]} style={{fontFamily: SANS, fontSize: 40, color: i < items.length - 1 ? 'rgba(238,231,219,0.8)' : BONE, marginBottom: 6}}>
            <span style={{color: ACC, marginRight: 16}}>{i ? '→' : '·'}</span>{it}</Rise>
        ))}
      </div>
      <div style={{position: 'absolute', left: 120, top: 560}}>
        <Rise at={at[4]} dy={30} blur={10} style={{fontFamily: SANS, fontWeight: 300, fontSize: 150, color: ACC, letterSpacing: em(0.12)}}>{big}</Rise>
        <Rise at={at[4] + 0.4} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 44, color: BONE}}>{sub}</Rise>
      </div>
    </Env>
  );
};

// ---------------------------------------------------------------- food | hunger
const Split = ({dur, at, left, right, mid}) => {
  const t = useT();
  const g = k(t, at[1], at[1] + 1.2, 0, 1, INOUT);
  const L = (x) => ({position: 'absolute', top: 420, width: 700, textAlign: 'center', left: x});
  return (
    <Env dur={dur}>
      <AbsoluteFill style={{background: 'rgba(0,0,0,0.45)'}} />
      <div style={{...L(260 - g * 60)}}><Rise at={at[0]} style={{fontFamily: SANS, fontWeight: 300, fontSize: 130, letterSpacing: em(0.2), color: BONE}}>{left}</Rise></div>
      <div style={{...L(960 + g * 60)}}><Rise at={at[0] + 0.5} style={{fontFamily: SANS, fontWeight: 300, fontSize: 130, letterSpacing: em(0.2), color: ACC}}>{right}</Rise></div>
      <div style={{position: 'absolute', left: 959, top: 380 + 120 * (1 - k(t, at[0] + 0.3, at[0] + 1.1)), width: 2, height: 240 * k(t, at[0] + 0.3, at[0] + 1.1),
        background: 'rgba(238,231,219,0.7)'}} />
      <div style={{position: 'absolute', top: 660, width: 1920, textAlign: 'center'}}>
        <Rise at={at[1]} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 44, color: DIM}}>{mid}, and they don't meet</Rise>
      </div>
    </Env>
  );
};

// ---------------------------------------------------------------- relocation: out, too far, back
const Reloc = ({dur, at, a, a_sub, b, b_sub}) => {
  const t = useT();
  const ax = 420, bx = 1500, y = 470;
  const go = k(t, at[1], at[1] + 1.6, 0, 1, INOUT);
  const back = k(t, at[3], at[3] + 1.4, 0, 1, INOUT);
  const far = k(t, at[2], at[2] + 0.6);
  const Pin = ({x, o, col}) => (
    <g opacity={o}><circle cx={x} cy={y} r={14} fill={col} /><circle cx={x} cy={y} r={28} fill="none" stroke={col} strokeWidth="2" opacity="0.6" /></g>
  );
  return (
    <Env dur={dur}>
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,0) 22%, rgba(0,0,0,0.7) 36%, rgba(0,0,0,0.7) 68%, rgba(0,0,0,0) 82%)'}} />
      <svg width="1920" height="1080" style={{position: 'absolute', left: 0, top: 0}}>
        <line x1={ax} y1={y} x2={ax + (bx - ax) * go} y2={y} stroke={BONE} strokeWidth="3" strokeDasharray="14 12" opacity="0.8" />
        <Pin x={ax} o={k(t, at[0], at[0] + 0.6)} col={RUST} />
        <Pin x={bx} o={k(t, at[1] + 1.2, at[1] + 1.8)} col={BONE} />
        {back > 0 && back < 1 && <circle cx={bx - (bx - ax) * back} cy={y - 46} r={10} fill={RUST} />}
        {back > 0 && <path d={`M${bx},${y - 46} L${bx - (bx - ax) * back},${y - 46}`} stroke={RUST} strokeWidth="3" fill="none" />}
        {back > 0.98 && <path d={`M${ax + 22},${y - 58} L${ax},${y - 46} L${ax + 22},${y - 34}`} stroke={RUST} strokeWidth="3" fill="none" />}
      </svg>
      <div style={{position: 'absolute', left: ax - 250, top: y + 50, width: 500, textAlign: 'center'}}>
        <Rise at={at[0] + 0.2} style={{fontFamily: SANS, fontWeight: 500, fontSize: 34, letterSpacing: em(0.35), color: BONE}}>{a}</Rise>
        <Rise at={at[0] + 0.5} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 32, color: DIM, marginTop: 6}}>{a_sub}</Rise>
      </div>
      <div style={{position: 'absolute', left: bx - 250, top: y + 50, width: 500, textAlign: 'center'}}>
        <Rise at={at[1] + 1.3} style={{fontFamily: SANS, fontWeight: 500, fontSize: 34, letterSpacing: em(0.35), color: BONE}}>{b}</Rise>
        <Rise at={at[1] + 1.6} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 32, color: DIM, marginTop: 6}}>{b_sub}</Rise>
      </div>
      <div style={{position: 'absolute', left: 660, width: 600, top: y + 40, textAlign: 'center', opacity: far * (1 - k(t, at[3] - 0.2, at[3] + 0.3))}}>
        <Rise at={at[2]} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 40, color: RED_T}}>too far from any job</Rise>
      </div>
      <div style={{position: 'absolute', left: 660, width: 600, top: y - 130, textAlign: 'center'}}>
        <Rise at={at[3] + 0.6} style={{fontFamily: SANS, fontWeight: 500, fontSize: 30, letterSpacing: em(0.38), color: ACC}}>AND CAME BACK</Rise>
      </div>
    </Env>
  );
};

export const OVERLAYS = {define: Define, stat: Stat, chapter: Chapter, timeline: Timeline, words: Words, quote: Quote, list: List, etym: Etym,
  daybook: Daybook, parking: Parking, checks: Checks, process: Process, equation: Equation, clock: Clock, split: Split, reloc: Reloc};
