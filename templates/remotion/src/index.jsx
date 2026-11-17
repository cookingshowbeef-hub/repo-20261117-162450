import React, {useEffect, useState} from 'react';
import {AbsoluteFill, Composition, continueRender, delayRender, registerRoot, staticFile} from 'remotion';
import {FILM} from './Film';
import {OVERLAYS} from './Overlays';

const useFont = () => {
  const [h] = useState(() => delayRender('font'));
  useEffect(() => {
    const f = new FontFace('Jost', `url(${staticFile('fonts/Jost-wght.ttf')})`, {weight: '100 900'});
    f.load().then((x) => { document.fonts.add(x); continueRender(h); });
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
