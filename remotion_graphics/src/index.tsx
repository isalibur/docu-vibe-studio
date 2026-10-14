import React from 'react';
import { Composition, registerRoot } from 'remotion';

// Placeholder Composition inicial
const DemoScene: React.FC = () => {
  return (
    <div
      style={{
        flex: 1,
        backgroundColor: '#0D0F12',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#F8FAFC',
        fontFamily: 'sans-serif',
        fontSize: 48,
        fontWeight: 'bold',
      }}
    >
      Docu-Vibe-Studio: Remotion Engine Ready
    </div>
  );
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="DemoScene"
        component={DemoScene}
        durationInFrames={150} // 5 segundos a 30fps
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};

registerRoot(RemotionRoot);
