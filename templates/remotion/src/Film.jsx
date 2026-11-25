// Film graphics (library from POLE OF COLD; palette, fonts and motion come from the film's style via ./style), 1920x1080 @30. Bone-white type, ice-blue accent, red for danger, film grain on full-frame cards.
// Every component gets {dur, at:[s...]} (beat times from its start, pinned to the narration) plus its own props.
import React, {useEffect, useState} from 'react';
import {AbsoluteFill, Easing, Img, Sequence, continueRender, delayRender, interpolate, random, staticFile, useCurrentFrame} from 'remotion';
import {PAL, SANS, SERIF, MONO, OUT, INOUT, RISE, em, SH, GRAIN_K, SCRIM} from './style';

const FPS = 30;
const k = (t, a, b, from = 0, to = 1, e = OUT) => interpolate(t, [a, b], [from, to], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: e});
export const BONE = PAL.text, DIM = PAL.dim, ICE = PAL.accent, ICE_T = PAL.accent_text, RED = PAL.danger, WARM = PAL.warm, BG = PAL.bg, LAND = PAL.land, SEA = PAL.sea;   // from the film's style
const useT = () => useCurrentFrame() / FPS;
const fadeOut = (t, dur, len = 0.6) => 1 - k(t, dur - len, dur, 0, 1, INOUT);

const Grain = ({o: o0 = 0.06}) => {
  const o = o0 * GRAIN_K;
  const seed = Math.floor(useCurrentFrame() / 2);
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <svg width="1920" height="1080" style={{position: 'absolute', opacity: o, mixBlendMode: 'screen'}}>
        <filter id={`g${seed}`}><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed={seed} /><feColorMatrix type="saturate" values="0" /></filter>
        <rect width="1920" height="1080" filter={`url(#g${seed})`} />
      </svg>
      <AbsoluteFill style={{background: 'radial-gradient(ellipse 75% 70% at 50% 50%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 100%)'}} />
    </AbsoluteFill>
  );
};
const Rise = ({at = 0, children, style, dy = RISE.dy, blur = RISE.blur, len = RISE.len}) => {
  const u = k(useT(), at, at + len);
  return <div style={{opacity: u, transform: `translateY(${(1 - u) * dy}px)`, filter: `blur(${(1 - u) * blur}px)`, textShadow: SH, ...style}}>{children}</div>;
};
const Rule = ({at = 0, w = 80, color = ICE, style}) => <div style={{width: w * k(useT(), at, at + 0.8), height: 2, background: color, ...style}} />;
const Kicker = ({at = 0, children, color = ICE_T, size = 26}) => (
  <Rise at={at} style={{fontFamily: SANS, fontWeight: 500, fontSize: size, letterSpacing: em(0.42), color}}>{children}</Rise>
);
const Env = ({dur, children, fin = 0.4, fout = 0.5, bg}) => {
  const t = useT();
  return <AbsoluteFill style={{background: bg, opacity: Math.min(k(t, 0, fin, 0, 1, INOUT), 1 - k(t, dur - fout, dur, 0, 1, INOUT))}}>{children}</AbsoluteFill>;
};
const ScrimLeft = ({w = 62, o = 0.78 * SCRIM}) => (
  <AbsoluteFill style={{background: `linear-gradient(90deg, rgba(0,0,0,${o}) 0%, rgba(0,0,0,${o * 0.6}) ${w * 0.55}%, rgba(0,0,0,0) ${w}%)`}} />
);
const ScrimRight = ({o = 0.78 * SCRIM}) => (
  <AbsoluteFill style={{background: `linear-gradient(270deg, rgba(0,0,0,${o}) 0%, rgba(0,0,0,${o * 0.6}) 32%, rgba(0,0,0,0) 60%)`}} />
);
const ScrimTop = ({o = 0.7 * SCRIM}) => (
  <AbsoluteFill style={{background: `linear-gradient(180deg, rgba(0,0,0,${o}) 0px, rgba(0,0,0,${o}) 160px, rgba(0,0,0,0) 330px)`}} />
);

// ---------------------------------------------------------------- title card + end text
const Title = ({dur, bg = BG, title = 'FILM TITLE', subtitle = ''}) => {
  const t = useT();
  const word = title;
  return (
    <AbsoluteFill style={{background: bg, opacity: fadeOut(t, dur, 0.8), justifyContent: 'center', alignItems: 'center'}}>
      <div style={{display: 'flex', paddingLeft: '0.45em'}}>
        {[...word].map((c, i) => {
          const u = k(t, 0.3 + i * 0.09, 1.6 + i * 0.09);
          return <span key={i} style={{fontFamily: SANS, fontWeight: 300, fontSize: 128, color: BONE, letterSpacing: `${0.45 + (1 - u) * 0.3}em`, opacity: u,
            filter: `blur(${(1 - u) * 12}px)`, whiteSpace: 'pre'}}>{c}</span>;
        })}
      </div>
      <Rule at={1.4} w={100} style={{margin: '28px 0 30px'}} />
      <Rise at={1.8} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 46, color: DIM}}>{subtitle}</Rise>
      <Grain />
    </AbsoluteFill>
  );
};
const EndText = ({dur, lines, title, subtitle}) => {
  const t = useT();
  const tt = dur - 5.0;
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', opacity: 1 - k(t, tt - 1.0, tt - 0.2, 0, 1, INOUT)}}>
        {lines.map((l, i) => <Rise key={i} at={0.8 + i * 3.6} style={{fontFamily: SANS, fontSize: 44, color: BONE, marginBottom: 46, textAlign: 'center'}}>{l}</Rise>)}
      </AbsoluteFill>
      <Sequence from={Math.round(tt * FPS)} layout="none"><Title dur={dur - tt} bg="#000" title={title} subtitle={subtitle} /></Sequence>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- lower third (with an optional second line)
const Lower = ({dur, at, text, sub, side = 'right'}) => (                                   // right: the counter owns the bottom-left
  <Env dur={dur}>
    <AbsoluteFill style={{background: `radial-gradient(ellipse 58% 36% at ${side === 'left' ? '10%' : '90%'} 100%, rgba(0,0,0,0.78) 0%, rgba(0,0,0,0.45) 50%, rgba(0,0,0,0) 100%)`}} />
    <div style={{position: 'absolute', [side]: 110, bottom: 100, textAlign: side}}>
      <Rule at={at[0]} w={56} style={{marginBottom: 14, marginLeft: side === 'right' ? 'auto' : 0}} />
      <Rise at={at[0] + 0.15} style={{fontFamily: SANS, fontSize: 42, color: BONE, whiteSpace: 'nowrap'}}>{text}</Rise>
      {sub && <Rise at={at[0] + 0.45} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 34, color: '#D6DEE6', marginTop: 6, whiteSpace: 'nowrap'}}>{sub}</Rise>}
    </div>
  </Env>
);

// archival date stamp, top left, typewriter
const Stamp = ({dur, at, text}) => {
  const t = useT();
  const n = Math.floor(k(t, at[0], at[0] + 1.2, 0, text.length, Easing.linear));
  return (
    <Env dur={dur}>
      <div style={{position: 'absolute', left: 96, top: 82, padding: '12px 22px', border: `2px solid rgba(238,241,244,0.7)`, background: 'rgba(0,0,0,0.55)',
        fontFamily: MONO, fontSize: 30, letterSpacing: em(0.12), color: BONE, opacity: k(t, at[0] - 0.2, at[0] + 0.2)}}>
        {text.slice(0, n)}<span style={{opacity: (t * 2) % 1 < 0.5 ? 1 : 0}}>▍</span>
      </div>
    </Env>
  );
};

// ---------------------------------------------------------------- maps
const useJson = (file) => {
  const [data, setData] = useState(null);
  const [h] = useState(() => delayRender(file));
  useEffect(() => { fetch(staticFile(file)).then((r) => r.json()).then((j) => { setData(j); continueRender(h); }); }, [file, h]);
  return data;
};
const keyed = (t, keys) => {                 // keys: [[t, a, b, c], ...] -> interpolated [a, b, c]
  if (t <= keys[0][0]) return keys[0].slice(1);
  for (let i = 1; i < keys.length; i++) {
    if (t <= keys[i][0]) {
      const u = k(t, keys[i - 1][0], keys[i][0], 0, 1, INOUT);
      return keys[i].slice(1).map((v, j) => keys[i - 1][j + 1] + (v - keys[i - 1][j + 1]) * u);
    }
  }
  return keys[keys.length - 1].slice(1);
};
const plen = (pts) => pts.reduce((s, p, i) => (i ? s + Math.hypot(p[0] - pts[i - 1][0], p[1] - pts[i - 1][1]) : 0), 0);
const MapView = ({dur, at, map, cam, region, overlay, lines = [], pts = [], caption, counter, isobars, fullframe = true}) => {
  const t = useT();
  const g = useJson(`geo/${map}.json`);
  if (!g) return null;
  const A = (i) => at[i] ?? at[at.length - 1];
  const [cx, cy, z0] = keyed(t, cam.map((c) => [typeof c[0] === 'string' ? A(+c[0].slice(1)) + (c[4] || 0) : c[0], c[1], c[2], c[3]]));
  const z = z0 * (1 + 0.07 * Math.min(1, t / Math.max(dur, 1)));     // slow continuous push: a map is never a still frame
  const tf = `translate(${960 - cx * z},${540 - cy * z}) scale(${z})`;
  const sw = (w) => w / z;
  return (
    <Env dur={dur} bg={fullframe ? SEA : undefined} fin={0.6}>
      <svg width="1920" height="1080" style={{position: 'absolute'}}>
        <g transform={tf}>
          {g.land.map((d, i) => <path key={i} d={d} fill={LAND} stroke="rgba(174,184,194,0.28)" strokeWidth={sw(1)} />)}
          {region && g.region && <path d={g.region} fill="rgba(111,174,219,0.16)" stroke={ICE} strokeWidth={sw(2.5)} opacity={k(t, A(region.at ?? 0), A(region.at ?? 0) + 1)} />}
          {g.rivers.map((d, i) => <path key={i} d={d} fill="none" stroke="rgba(111,174,219,0.55)" strokeWidth={sw(1.4)} />)}
          {isobars && [0, 1, 2, 3, 4].map((i) => {
            const [x, y] = g.pts[isobars.center];
            return <ellipse key={i} cx={x} cy={y} rx={(120 + i * 95) * k(t, A(isobars.at) + i * 0.25, A(isobars.at) + i * 0.25 + 1.2)} ry={(80 + i * 66) * k(t, A(isobars.at) + i * 0.25, A(isobars.at) + i * 0.25 + 1.2)}
              fill="none" stroke={ICE_T} strokeWidth={sw(2)} opacity={0.75 - i * 0.12} />;
          })}
          {isobars && <text x={g.pts[isobars.center][0]} y={g.pts[isobars.center][1] + 30 / z} textAnchor="middle" fontFamily={SANS} fontWeight="500"
            fontSize={84 / z} fill={ICE_T} opacity={k(t, A(isobars.at), A(isobars.at) + 0.8)}>H</text>}
          {overlay && g.overlay && (() => {                          // slide: the outline travels in from the east and settles
            const u = overlay.slide ? k(t, A(overlay.at), A(overlay.at) + 2.0, 0, 1, Easing.bezier(0.2, 0, 0.1, 1)) : 1;
            return <path d={g.overlay} transform={`translate(${(1 - u) * 1100},${(1 - u) * -120})`} fill={`rgba(111,174,219,${0.22 * (overlay.slide ? u : 1)})`}
              stroke={ICE_T} strokeWidth={sw(3)} strokeDasharray="20000"
              strokeDashoffset={overlay.slide ? 0 : 20000 * (1 - k(t, A(overlay.at), A(overlay.at) + 2.2, 0, 1, INOUT))} opacity={overlay.slide ? k(t, A(overlay.at), A(overlay.at) + 0.5) : 1} />;
          })()}
          {lines.map((l, i) => {
            const P = g.lines[l.name]; if (!P) return null;
            const L = plen(P); const u = k(t, A(l.at), A(l.at) + (l.len || 2.5), 0, 1, INOUT);
            return <polyline key={i} points={P.map((p) => p.join(',')).join(' ')} fill="none" stroke={l.color || WARM} strokeWidth={sw(l.w || 4)}
              strokeLinecap="round" strokeLinejoin="round" strokeDasharray={l.dash ? `${sw(10)} ${sw(9)}` : `${L} ${L}`} strokeDashoffset={l.dash ? 0 : L * (1 - u)}
              opacity={l.dash ? u : 1} />;
          })}
          {pts.map((p, i) => {
            const [x, y] = g.pts[p.name]; const u = k(t, A(p.at), A(p.at) + 0.6);
            return <g key={i} opacity={u}><circle cx={x} cy={y} r={sw(p.big ? 11 : 7)} fill={p.color || BONE} />
              {p.big && <circle cx={x} cy={y} r={sw(11 + 18 * ((t * 0.8) % 1))} fill="none" stroke={p.color || BONE} strokeWidth={sw(2)} opacity={1 - ((t * 0.8) % 1)} />}</g>;
          })}
        </g>
      </svg>
      {pts.map((p, i) => {
        const [x, y] = g.pts[p.name]; const sx = 960 + (x - cx) * z, sy = 540 + (y - cy) * z;
        const [dx, dy] = p.off || [18, -40];
        return <div key={i} style={{position: 'absolute', left: sx + dx, top: sy + dy, opacity: k(t, A(p.at) + 0.2, A(p.at) + 0.8), whiteSpace: 'nowrap',
          fontFamily: SANS, fontWeight: p.big ? 500 : 400, fontSize: p.big ? 36 : 28, letterSpacing: p.big ? '0.2em' : '0.06em', color: BONE, textShadow: SH,
          transform: p.right === false ? 'translateX(-100%)' : undefined}}>{p.label || p.name}</div>;
      })}
      {counter && (() => {
        const u = k(t, A(counter.at), A(counter.at) + (counter.len || 2.5), 0, 1, INOUT);
        return <div style={{position: 'absolute', right: 120, bottom: 110, textAlign: 'right', opacity: k(t, A(counter.at) - 0.2, A(counter.at) + 0.3)}}>
          <div style={{fontFamily: SANS, fontWeight: 300, fontSize: 110, color: BONE, textShadow: SH, fontVariantNumeric: 'tabular-nums'}}>
            {counter.prefix || ''}{Math.round(counter.to * u).toLocaleString('en-US')} {counter.unit}</div>
          <div style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 36, color: DIM, textShadow: SH}}>{counter.sub}</div></div>;
      })()}
      {caption && <div style={{position: 'absolute', left: 110, ...(caption.pos === 'bottom' ? {bottom: 110} : {top: 90})}}>
        {caption.kicker && <Kicker at={A(caption.at ?? 0)}>{caption.kicker}</Kicker>}
        <Rule at={A(caption.at ?? 0) + 0.2} w={70} style={{margin: '16px 0 16px'}} />
        <Rise at={A(caption.at ?? 0) + 0.35} style={{fontFamily: SANS, fontSize: 52, color: BONE}}>{caption.title}</Rise>
        {caption.sub && <Rise at={A(caption.sub_at ?? caption.at ?? 0) + 0.6} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 36, color: DIM, marginTop: 8, maxWidth: 900}}>{caption.sub}</Rise>}
      </div>}
      {fullframe && <Grain o={0.05} />}
    </Env>
  );
};

// ---------------------------------------------------------------- diagrams
// ration loop: four nodes on a circle, an arrow travelling round
const Loop = ({dur, at, nodes, head}) => {
  const t = useT();
  const R = 210, cx = 1380, cy = 560;
  const P = (i) => [cx + R * Math.sin((i / nodes.length) * 2 * Math.PI), cy - R * Math.cos((i / nodes.length) * 2 * Math.PI)];
  const spin = k(t, at[0] + 0.8, dur, 0, 1.6, Easing.linear);
  const a = spin * 2 * Math.PI;
  return (
    <Env dur={dur}>
      <ScrimRight o={0.82} />
      <svg width="1920" height="1080" style={{position: 'absolute'}}>
        <circle cx={cx} cy={cy} r={R} fill="none" stroke="rgba(238,241,244,0.35)" strokeWidth="2" strokeDasharray="8 10" opacity={k(t, at[0], at[0] + 0.6)} />
        <circle cx={cx + R * Math.sin(a)} cy={cy - R * Math.cos(a)} r="9" fill={RED} opacity={k(t, at[0] + 0.8, at[0] + 1.2)} />
      </svg>
      {nodes.map((n, i) => { const [x, y] = P(i); return (
        <div key={i} style={{position: 'absolute', left: x - 150, top: y - 26, width: 300, textAlign: 'center'}}>
          <Rise at={at[0] + 0.2 + i * 0.35} style={{display: 'inline-block', padding: '8px 18px', background: 'rgba(11,14,18,0.85)', border: `1.5px solid ${i === 2 ? RED : ICE}`,
            fontFamily: SANS, fontSize: 30, color: BONE}}>{n}</Rise></div>); })}
      {head && <div style={{position: 'absolute', left: cx - 260, top: cy + R + 70, width: 520, textAlign: 'center'}}>
        <Rise at={at[0] + 1.6} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 34, color: DIM}}>{head}</Rise></div>}
    </Env>
  );
};

// two labels on a split screen
const SplitLabels = ({dur, at, left, right}) => (
  <Env dur={dur}>
    <ScrimTop o={0.55} />
    <div style={{position: 'absolute', left: 0, width: 958, top: 70, textAlign: 'center'}}><Kicker at={at[0]} color={WARM}>{left[0]}</Kicker>
      <Rise at={at[0] + 0.3} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 38, color: BONE, marginTop: 10}}>{left[1]}</Rise></div>
    <div style={{position: 'absolute', left: 962, width: 958, top: 70, textAlign: 'center'}}><Kicker at={at[1] ?? at[0] + 0.6}>{right[0]}</Kicker>
      <Rise at={(at[1] ?? at[0] + 0.6) + 0.3} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 38, color: BONE, marginTop: 10}}>{right[1]}</Rise></div>
    <div style={{position: 'absolute', left: 958, top: 0, width: 4, height: 1080 * k(useT(), 0, 0.8), background: BONE, opacity: 0.85}} />
  </Env>
);

// 24-hour dial with the daylight arc
const Daylight = ({dur, at, hours, label, sub, warm}) => {
  const t = useT();
  const cx = 1460, cy = 520, r = 190;
  const h = k(t, at[0] + 0.3, at[0] + 2.2, 0, hours, INOUT);
  const pt = (a) => [cx + r * Math.sin(a), cy - r * Math.cos(a)];                  // angle 0 = top = noon, PI = bottom = midnight
  const half = (h / 24) * Math.PI;
  const [x0, y0] = pt(-half), [x1, y1] = pt(half);
  return (
    <Env dur={dur}>
      <ScrimRight o={0.8} />
      <svg width="1920" height="1080" style={{position: 'absolute'}}>
        <circle cx={cx} cy={cy} r={r} fill="rgba(5,8,12,0.75)" stroke="rgba(238,241,244,0.4)" strokeWidth="2" />
        {h > 0.05 && <path d={`M${cx},${cy} L${x0},${y0} A${r},${r} 0 ${h > 12 ? 1 : 0} 1 ${x1},${y1} Z`} fill={warm ? WARM : '#F2D58A'} opacity="0.85" />}
        {[0, 6, 12, 18].map((q) => { const a = ((q - 12) / 24) * 2 * Math.PI; const [x, y] = [cx + (r + 40) * Math.sin(a), cy - (r + 40) * Math.cos(a)];
          return <text key={q} x={x} y={y + 9} textAnchor="middle" fontFamily={SANS} fontSize="24" fill={DIM}>{['midnight', '6 am', 'noon', '6 pm'][q / 6]}</text>; })}
      </svg>
      <div style={{position: 'absolute', left: cx - 300, width: 600, top: cy + r + 70, textAlign: 'center'}}>
        <Rise at={at[0] + 0.4} style={{fontFamily: SANS, fontWeight: 300, fontSize: 72, color: BONE}}>{label}</Rise>
        <Rise at={at[0] + 0.8} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 32, color: DIM}}>{sub}</Rise>
      </div>
    </Env>
  );
};

// cold-air bowl: valley cross-section, cold air sliding down and pooling, village at the bottom
const Bowl = ({dur, at, label, elev}) => {
  const t = useT();
  const prof = (x) => 860 - 330 * Math.exp(-Math.pow((x - 260) / 230, 2)) - 380 * Math.exp(-Math.pow((x - 1680) / 260, 2)) - 70 * Math.sin(x / 90) * 0.3;
  const top = Array.from({length: 97}, (_, i) => { const x = i * 20; return [x, prof(x)]; });
  const fill = k(t, at[1] ?? at[0] + 2, (at[3] ?? at[0] + 8) + 1, 0, 1, Easing.bezier(0.3, 0, 0.3, 1));
  const lake = 860 - 250 * fill;
  return (
    <Env dur={dur} bg={BG} fin={0.6}>
      <svg width="1920" height="1080" style={{position: 'absolute', transform: `scale(${1 + 0.06 * t / dur})`, transformOrigin: '50% 55%'}}>
        <defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#101826" /><stop offset="1" stopColor="#1b2735" /></linearGradient></defs>
        <rect width="1920" height="1080" fill="url(#sky)" />
        {Array.from({length: 70}, (_, i) => <circle key={i} cx={random(`s${i}`) * 1920} cy={random(`y${i}`) * 420} r={random(`r${i}`) * 1.6 + 0.4} fill="#fff" opacity={0.5 * k(t, 0, 1)} />)}
        <clipPath id="valley"><path d={`M0,1080 L${top.map((p) => p.join(',')).join(' L')} L1920,1080 Z`} /></clipPath>
        <path d={`M0,1080 L${top.map((p) => p.join(',')).join(' L')} L1920,1080 Z`} fill="#0d1218" stroke="rgba(238,241,244,0.55)" strokeWidth="2" />
        <clipPath id="valleyAir"><path d={`M0,0 L${top.map((p) => p.join(',')).join(' L')} L1920,0 Z`} /></clipPath>
        <g clipPath="url(#valleyAir)"><rect x="300" y={lake} width="1340" height={1080 - lake} fill="rgba(111,174,219,0.35)" /></g>
        {Array.from({length: 26}, (_, i) => {           // cold-air particles sliding down both slopes
          const side = i % 2, ph = ((t * 0.22 + random(`p${i}`)) % 1);
          const x = side ? 1680 - ph * 600 : 260 + ph * 560;
          return <circle key={i} cx={x} cy={prof(x) - 14 - random(`h${i}`) * 40} r="5" fill={ICE_T} opacity={k(t, at[1] ?? 1.5, (at[1] ?? 1.5) + 1) * (1 - ph * 0.6)} />;
        })}
        {[[960, 'Oymyakon']].map(([x, n]) => <g key={n} opacity={k(t, at[0] + 0.5, at[0] + 1.2)}>
          <rect x={x - 46} y={prof(x) - 26} width="20" height="26" fill="#C9A15A" /><rect x={x - 16} y={prof(x) - 34} width="26" height="34" fill="#C9A15A" />
          <rect x={x + 18} y={prof(x) - 22} width="18" height="22" fill="#C9A15A" />
          <line x1={x - 6} y1={prof(x) - 34} x2={x - 6} y2={prof(x) - 120} stroke="rgba(238,241,244,0.5)" strokeWidth="5" strokeLinecap="round" /></g>)}
      </svg>
      <div style={{position: 'absolute', left: 820, top: prof(960) + 24, width: 280, textAlign: 'center'}}>
        <Rise at={at[0] + 0.8} style={{fontFamily: SANS, fontWeight: 500, fontSize: 28, letterSpacing: em(0.3), color: BONE}}>{label}</Rise>
        <Rise at={at[0] + 1.1} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 28, color: DIM}}>{elev}</Rise></div>
      <div style={{position: 'absolute', left: 110, top: 90}}>
        <Rise at={at[1] ?? 2} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 40, color: BONE}}>cold air is heavy</Rise>
        <Rise at={at[2] ?? 4} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 40, color: ICE_T, marginTop: 8}}>it slides down and pools</Rise>
        <Rise at={at[3] ?? 7} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 40, color: BONE, marginTop: 8}}>the mountains keep the wind out</Rise>
      </div>
      <Grain o={0.05} />
    </Env>
  );
};

// record boards: rows that build on the words
const Records = ({dur, at, rows, note}) => (
  <Env dur={dur}>
    <ScrimRight o={0.85} />
    <div style={{position: 'absolute', right: 120, top: 0, bottom: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 34, width: 760}}>
      {rows.map(([place, temp, date, color], i) => (
        <div key={i} style={{display: 'flex', alignItems: 'baseline', justifyContent: 'flex-end', gap: 30}}>
          <div style={{textAlign: 'right'}}>
            <Rise at={at[i]} style={{fontFamily: SANS, fontWeight: 500, fontSize: 30, letterSpacing: em(0.32), color: color || ICE_T}}>{place}</Rise>
            <Rise at={at[i] + 0.2} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 28, color: DIM}}>{date}</Rise></div>
          <Rise at={at[i] + 0.1} dy={30} blur={10} style={{fontFamily: SANS, fontWeight: 300, fontSize: 104, color: BONE, minWidth: 330, textAlign: 'right'}}>{temp}</Rise>
        </div>))}
      {note && <Rise at={at[rows.length] ?? at[rows.length - 1] + 1.5} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 32, color: BONE, textAlign: 'right'}}>{note}</Rise>}
    </div>
  </Env>
);

// vertical temperature scale: freezer, Oymyakon record, Mars night band
const Thermo = ({dur, at, marks, band}) => {
  const t = useT();
  const y = (c) => 200 + (0 - c) * 7.2;          // 0 °C at y=200, -100 at y=920
  const x = 1320;
  return (
    <Env dur={dur}>
      <ScrimRight o={0.85} />
      <svg width="1920" height="1080" style={{position: 'absolute'}}>
        <line x1={x} y1={y(0)} x2={x} y2={y(0) + (y(-100) - y(0)) * k(t, 0, 1.2, 0, 1, INOUT)} stroke={BONE} strokeWidth="3" />
        {[0, -20, -40, -60, -80, -100].map((c) => <g key={c} opacity={k(t, 0.4, 1)}><line x1={x - 14} y1={y(c)} x2={x} y2={y(c)} stroke={BONE} strokeWidth="2" />
          <text x={x - 24} y={y(c) + 8} textAnchor="end" fontFamily={SANS} fontSize="24" fill={DIM}>{c}°</text></g>)}
        {band && <rect x={x + 6} y={y(band.from)} width="26" height={(y(band.to) - y(band.from)) * k(t, at[band.i], at[band.i] + 0.8)} fill={WARM} opacity="0.75" />}
        {marks.map((m, i) => <g key={i} opacity={k(t, at[m.i], at[m.i] + 0.5)}><circle cx={x} cy={y(m.c)} r="11" fill={m.color || ICE_T} />
          <line x1={x + 16} y1={y(m.c)} x2={x + 70} y2={y(m.c)} stroke={m.color || ICE_T} strokeWidth="2" /></g>)}
      </svg>
      {[...marks, ...(band ? [{c: (band.from + band.to) / 2, label: band.label, value: band.value, i: band.i, color: WARM}] : [])].map((m, j) => (
        <div key={j} style={{position: 'absolute', left: x + 86, top: y(m.c) - 34}}>
          <Rise at={at[m.i] + 0.1} style={{fontFamily: SANS, fontWeight: 300, fontSize: 46, color: BONE}}>{m.value}</Rise>
          <Rise at={at[m.i] + 0.3} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 28, color: DIM, marginTop: -4}}>{m.label}</Rise></div>))}
    </Env>
  );
};

// corner time-of-day clock for "a day at minus fifty"
const Tod = ({dur, at, time, label}) => {
  const t = useT();
  const [hh, mm] = time.split(':').map(Number);
  const ang = ((hh % 12) + mm / 60) / 12 * 360 - k(t, at[0], at[0] + 1.2, 30, 0, OUT);
  return (
    <Env dur={dur}>
      <div style={{position: 'absolute', right: 96, top: 76, display: 'flex', alignItems: 'center', gap: 22, padding: '14px 24px', background: 'rgba(0,0,0,0.5)'}}>
        <svg width="74" height="74"><circle cx="37" cy="37" r="33" fill="none" stroke={BONE} strokeWidth="2.5" />
          <line x1="37" y1="37" x2={37 + 18 * Math.sin((ang * Math.PI) / 180)} y2={37 - 18 * Math.cos((ang * Math.PI) / 180)} stroke={BONE} strokeWidth="4" strokeLinecap="round" />
          <line x1="37" y1="37" x2={37 + 26 * Math.sin((mm / 60) * 2 * Math.PI)} y2={37 - 26 * Math.cos((mm / 60) * 2 * Math.PI)} stroke={ICE_T} strokeWidth="2.5" strokeLinecap="round" /></svg>
        <div><Rise at={at[0]} dy={8} style={{fontFamily: SANS, fontWeight: 400, fontSize: 46, color: BONE, lineHeight: 1}}>{label}</Rise></div>
      </div>
    </Env>
  );
};

// engine cutaway with three failure labels
const Engine = ({dur, at, labels}) => {
  const t = useT();
  return (
    <Env dur={dur}>
      <AbsoluteFill style={{background: 'linear-gradient(270deg, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.82) 45%, rgba(0,0,0,0.2) 75%, rgba(0,0,0,0) 90%)'}} />
      <svg width="1920" height="1080" style={{position: 'absolute'}} opacity={k(t, 0, 0.8)}>
        <g fill="none" stroke={BONE} strokeWidth="3" opacity="0.85">
          <rect x="1120" y="420" width="420" height="230" rx="18" /><rect x="1160" y="360" width="340" height="60" rx="10" />
          {[0, 1, 2, 3].map((i) => <rect key={i} x={1170 + i * 85} y="300" width="40" height="60" rx="6" />)}
          <circle cx="1210" cy="700" r="46" /><rect x="1440" y="660" width="120" height="80" rx="8" />
          <path d="M1120,520 L1040,520 L1040,600 L980,600" /><path d="M1540,480 L1620,480" />
        </g>
        <rect x="1446" y="666" width="108" height={68 * (1 - k(t, at[2], at[2] + 1.5))} y2="0" fill={ICE_T} opacity="0.6" />
      </svg>
      {labels.map((l, i) => (
        <div key={i} style={{position: 'absolute', left: [700, 1590, 1600][i], top: [330, 430, 690][i]}}>
          <Rise at={at[i]} style={{fontFamily: SANS, fontWeight: 500, fontSize: 32, letterSpacing: em(0.18), color: i === 2 ? RED : ICE_T}}>{l[0]}</Rise>
          <Rise at={at[i] + 0.25} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 28, color: BONE}}>{l[1]}</Rise></div>))}
    </Env>
  );
};

// permafrost cross-section; mode "thaw" melts the ice lenses and tilts the house
const Permafrost = ({dur, at, labels, mode}) => {
  const t = useT();
  const melt = mode === 'thaw' ? k(t, at[1] ?? 1.5, (at[2] ?? 5) + 1, 0, 1, INOUT) : 0;
  const tilt = mode === 'thaw' ? k(t, at[2] ?? 4, (at[2] ?? 4) + 2.5, 0, 9, INOUT) : 0;
  const ground = 430, active = 520;
  return (
    <Env dur={dur} bg={BG} fin={0.6}>
      <svg width="1920" height="1080" style={{position: 'absolute', transform: `scale(${1 + 0.06 * t / dur})`, transformOrigin: '50% 55%'}}>
        <rect x="0" y="0" width="1920" height={ground} fill={mode === 'thaw' ? '#1d2b22' : '#141c26'} />
        <rect x="0" y={ground} width="1920" height={active - ground} fill="#4a3a2a" />
        <rect x="0" y={active} width="1920" height={1080 - active} fill="#26323f" />
        {Array.from({length: 22}, (_, i) => <ellipse key={i} cx={80 + (i % 11) * 175 + (i > 10 ? 80 : 0)} cy={active + 90 + (i > 10 ? 190 : 0)}
          rx={60 * (1 - melt)} ry={14 * (1 - melt)} fill={ICE_T} opacity="0.7" />)}
        <g transform={`translate(960,${ground + melt * 40}) rotate(${tilt})`}>
          <rect x="-110" y="-150" width="220" height="150" fill="#5a4632" stroke={BONE} strokeWidth="2" />
          <path d="M-130,-150 L0,-240 L130,-150 Z" fill="#3d2f22" stroke={BONE} strokeWidth="2" />
          <rect x="-30" y="-80" width="60" height="80" fill="#2a2018" /><rect x="40" y="-120" width="44" height="36" fill="#F2D58A" opacity="0.8" />
          {[-90, -30, 30, 90].map((x) => <rect key={x} x={x - 6} y="0" width="12" height={70 - melt * 30} fill="#8a7a66" />)}
        </g>
        <line x1="0" y1={ground} x2="1920" y2={ground} stroke={BONE} strokeWidth="2" opacity="0.6" />
      </svg>
      <div style={{position: 'absolute', left: 110, top: ground + 20}}><Rise at={at[0]} style={{fontFamily: SANS, fontWeight: 500, fontSize: 28, letterSpacing: em(0.3), color: WARM}}>{labels[0]}</Rise></div>
      <div style={{position: 'absolute', left: 110, top: active + 30}}><Rise at={at[0] + 0.6} style={{fontFamily: SANS, fontWeight: 500, fontSize: 28, letterSpacing: em(0.3), color: ICE_T}}>{labels[1]}</Rise></div>
      {labels[2] && <div style={{position: 'absolute', left: 110, top: 90}}><Rise at={at[1] ?? 2} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 44, color: BONE}}>{labels[2]}</Rise></div>}
      <Grain o={0.05} />
    </Env>
  );
};

// school threshold chart: two bars against the scale, the counter value as a line
const Threshold = ({dur, at, rows, now}) => {
  const t = useT();
  const x = (c) => 980 + (-c - 40) * 38;        // -40 at x=980 ... -60 at x=1740
  return (
    <Env dur={dur}>
      <ScrimRight o={0.88} />
      <div style={{position: 'absolute', left: 980, top: 300}}><Kicker at={at[0]}>THE SCHOOL STAYS OPEN UNTIL</Kicker></div>
      <svg width="1920" height="1080" style={{position: 'absolute'}}>
        {[-40, -45, -50, -55, -60].map((c) => <g key={c} opacity={k(t, at[0], at[0] + 0.6)}><line x1={x(c)} y1="400" x2={x(c)} y2="700" stroke="rgba(238,241,244,0.2)" />
          <text x={x(c)} y="740" textAnchor="middle" fontFamily={SANS} fontSize="24" fill={DIM}>{c}°</text></g>)}
        {rows.map(([lab, c], i) => <rect key={i} x={x(-40)} y={440 + i * 120} height="64" width={(x(c) - x(-40)) * k(t, at[i] + 0.2, at[i] + 1.2, 0, 1, INOUT)} fill={i ? ICE : ICE_T} opacity="0.85" />)}
        {now != null && <line x1={x(now)} y1="400" x2={x(now)} y2="700" stroke={RED} strokeWidth="3" strokeDasharray="8 8" opacity={k(t, at[rows.length] ?? at[0] + 2, (at[rows.length] ?? at[0] + 2) + 0.5)} />}
      </svg>
      {rows.map(([lab, c], i) => <div key={i} style={{position: 'absolute', left: x(c) + 18, top: 446 + i * 120}}>
        <Rise at={at[i] + 1.0} style={{fontFamily: SANS, fontSize: 40, color: BONE}}>{c}°C</Rise></div>)}
      {rows.map(([lab], i) => <div key={i} style={{position: 'absolute', left: x(-40), top: 412 + i * 120}}>
        <Rise at={at[i]} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 30, color: BONE}}>{lab}</Rise></div>)}
    </Env>
  );
};

// body silhouette, core warm, hands and feet fading to blue
const Body = ({dur, at, label}) => {
  const t = useT();
  const c = k(t, at[0] + 0.3, at[0] + 3, 0, 1, INOUT);
  return (
    <Env dur={dur}>
      <ScrimRight o={0.85} />
      <svg width="1920" height="1080" style={{position: 'absolute'}}>
        <defs><radialGradient id="heat" cx="50%" cy="42%" r={`${70 - 35 * c}%`}>
          <stop offset="0" stopColor="#F2B35A" /><stop offset="0.55" stopColor={RED} /><stop offset="1" stopColor="#3D7FC0" /></radialGradient></defs>
        <g transform="translate(1420,140)" fill="url(#heat)" opacity={k(t, 0, 0.8)}>
          <circle cx="0" cy="60" r="56" /><rect x="-90" y="130" width="180" height="300" rx="70" />
          <rect x="-170" y="150" width="62" height="300" rx="30" transform="rotate(10,-140,150)" /><rect x="108" y="150" width="62" height="300" rx="30" transform="rotate(-10,140,150)" />
          <rect x="-80" y="410" width="72" height="380" rx="34" /><rect x="8" y="410" width="72" height="380" rx="34" />
        </g>
      </svg>
      <div style={{position: 'absolute', left: 1180, width: 480, top: 960, textAlign: 'center'}}>
        <Rise at={at[0] + 1.2} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 36, color: BONE}}>{label}</Rise></div>
    </Env>
  );
};

// annual range bar: record low to record high
const Range = ({dur, at, lo, hi, label}) => {
  const t = useT();
  const x = (c) => 240 + (c + 70) * 13.6;       // -70..+40 across 240..1736
  const u = k(t, at[0] + 0.4, at[0] + 2.4, 0, 1, INOUT);
  return (
    <Env dur={dur}>
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,0) 40%, rgba(0,0,0,0.75) 60%, rgba(0,0,0,0.75) 85%, rgba(0,0,0,0) 100%)'}} />
      <svg width="1920" height="1080" style={{position: 'absolute'}}>
        <defs><linearGradient id="rng" x1="0" x2="1"><stop offset="0" stopColor="#3D7FC0" /><stop offset="0.62" stopColor="#B9C7D3" /><stop offset="1" stopColor={RED} /></linearGradient></defs>
        <rect x={x(lo[0])} y="760" height="26" width={(x(hi[0]) - x(lo[0])) * u} fill="url(#rng)" rx="13" />
        <line x1={x(0)} y1="740" x2={x(0)} y2="806" stroke={BONE} strokeWidth="2" opacity={k(t, at[0], at[0] + 0.5)} />
        <text x={x(0)} y="842" textAnchor="middle" fontFamily={SANS} fontSize="24" fill={DIM} opacity={k(t, at[0], at[0] + 0.5)}>0°</text>
      </svg>
      <div style={{position: 'absolute', left: x(lo[0]) - 10, top: 650}}><Rise at={at[0]} style={{fontFamily: SANS, fontWeight: 300, fontSize: 64, color: ICE_T}}>{lo[1]}</Rise></div>
      <div style={{position: 'absolute', left: x(hi[0]) - 220, width: 260, textAlign: 'right', top: 650}}><Rise at={at[0] + 2.2} style={{fontFamily: SANS, fontWeight: 300, fontSize: 64, color: WARM}}>{hi[1]}</Rise></div>
      <div style={{position: 'absolute', left: 0, width: 1920, top: 860, textAlign: 'center'}}><Rise at={at[1] ?? at[0] + 2.8} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 40, color: BONE}}>{label}</Rise></div>
    </Env>
  );
};

// two bars: Arctic vs the whole globe
const Bars = ({dur, at, rows, sub}) => {
  const t = useT();
  const mx = Math.max(...rows.map((r) => r[1]));
  return (
    <Env dur={dur}>
      <ScrimLeft w={66} o={0.85} />
      <div style={{position: 'absolute', left: 120, top: 330, width: 900}}>
        {rows.map(([lab, v, txt], i) => (
          <div key={i} style={{marginBottom: 44}}>
            <Rise at={at[i]} style={{fontFamily: SANS, fontWeight: 500, fontSize: 28, letterSpacing: em(0.3), color: i ? RED : DIM}}>{lab}</Rise>
            <div style={{height: 46, marginTop: 12, width: 760 * (v / mx) * k(t, at[i] + 0.2, at[i] + 1.6, 0, 1, INOUT), background: i ? RED : DIM}} />
            <Rise at={at[i] + 1.2} style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 32, color: BONE, marginTop: 8}}>{txt}</Rise>
          </div>))}
        <Rise at={at[rows.length] ?? at[0] + 3} style={{fontFamily: SANS, fontSize: 22, letterSpacing: em(0.2), color: DIM}}>{sub}</Rise>
      </div>
    </Env>
  );
};

export const FILM = {title: Title, end_text: EndText, lower: Lower, stamp: Stamp, map: MapView, loop: Loop, split_labels: SplitLabels, daylight: Daylight, bowl: Bowl,
  records: Records, thermo: Thermo, tod: Tod, engine: Engine, permafrost: Permafrost, threshold: Threshold, body: Body, range: Range, bars: Bars};
