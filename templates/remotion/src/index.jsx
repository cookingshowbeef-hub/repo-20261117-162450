import React, {useEffect, useState} from 'react';
import {AbsoluteFill, Composition, continueRender, delayRender, registerRoot, staticFile} from 'remotion';
import {FILM} from './Film';
import {OVERLAYS} from './Overlays';
import {FONT_FILES} from './style';

const useFont = () => {
  const [h] = useState(() => delayRender('font'));
  useEffect(() => {
    Promise.all(FONT_FILES.map((x) => new FontFace(x.family, `url(${staticFile(x.file)})`, {weight: x.weight || 'normal', style: x.style || 'normal'})
      .load().then((f) => document.fonts.add(f))))
      .catch((e) => console.error('font', e)).finally(() => continueRender(h));   // the style's fonts (public/fonts)
  }, [h]);
};
const Gfx = (p) => {
  useFont();
  const C = FILM[p.kind] || OVERLAYS[p.kind];
  return C ? <C {...p} /> : <AbsoluteFill style={{background: 'magenta'}} />;
};
const Root = () => (
  <Composition id="Gfx" component={Gfx} fps={30} width={1920} height={1080} durationInFrames={90} defaultProps={{kind: 'title', dur: 4, at: [0]}}
    calculateMetadata={({props}) => ({durationInFrames: Math.max(1, Math.round(props.dur * 30))})} />
);
registerRoot(Root);
