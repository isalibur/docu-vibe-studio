import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, Img } from 'remotion';

export interface DocumentaryParallaxProps {
  backgroundSrc?: string;
  foregroundCutoutSrc?: string;
  cameraMotion?: 'push_in' | 'drift_left' | 'dramatic_zoom';
}

export const DocumentaryParallax: React.FC<DocumentaryParallaxProps> = ({
  backgroundSrc,
  foregroundCutoutSrc,
  cameraMotion = 'push_in',
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // Interpolação de ponto flutuante contínua (Sub-pixel puro / ZERO JITTER)
  const progress = interpolate(frame, [0, durationInFrames], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Movimento de câmera do fundo (desfoque e zoom mais acentuado)
  const bgScale = interpolate(progress, [0, 1], [1.0, 1.12]);
  const bgTranslateX = cameraMotion === 'drift_left' ? interpolate(progress, [0, 1], [0, -35]) : 0;

  // Movimento do sujeito em primeiro plano (velocidade menor criando profundidade 3D)
  const fgScale = interpolate(progress, [0, 1], [1.0, 1.05]);
  const fgTranslateY = interpolate(progress, [0, 1], [0, -18]);

  return (
    <AbsoluteFill style={{ backgroundColor: '#0D0F12', overflow: 'hidden' }}>
      {/* Camada 1: Fundo com leve desfoque e escurecimento */}
      {backgroundSrc ? (
        <AbsoluteFill
          style={{
            transform: `scale(${bgScale}) translateX(${bgTranslateX}px)`,
            filter: 'blur(4px) brightness(0.85)',
          }}
        >
          <Img src={backgroundSrc} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        </AbsoluteFill>
      ) : (
        <AbsoluteFill style={{ backgroundColor: '#161920' }} />
      )}

      {/* Camada 2: Sujeito recortado com sombra dramática projetada */}
      {foregroundCutoutSrc && (
        <AbsoluteFill
          style={{
            transform: `scale(${fgScale}) translateY(${fgTranslateY}px)`,
            filter: 'drop-shadow(0 25px 35px rgba(0,0,0,0.85))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Img src={foregroundCutoutSrc} style={{ width: '85%', height: '85%', objectFit: 'contain' }} />
        </AbsoluteFill>
      )}

      {/* Camada 3: Vinheta escura suave nas bordas */}
      <AbsoluteFill
        style={{
          background: 'radial-gradient(circle, transparent 55%, rgba(13,15,18,0.75) 100%)',
          pointerEvents: 'none',
        }}
      />
    </AbsoluteFill>
  );
};
