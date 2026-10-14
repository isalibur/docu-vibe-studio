import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';

export interface NewspaperHighlightProps {
  headline?: string;
  source_label?: string;
  highlight_words?: string;
  date_label?: string;
}

export const NewspaperHighlight: React.FC<NewspaperHighlightProps> = ({
  headline = 'MARKET CRASH: BILLIONS VANISH IN MINUTES',
  source_label = 'The Financial Journal - Edição Histórica',
  highlight_words = 'BILLIONS VANISH',
  date_label = '15 de Setembro de 2008',
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // Movimento de câmera contínuo: leve aproximação (push-in) com perspectiva 3D
  const cameraZoom = interpolate(frame, [0, durationInFrames], [1.0, 1.06]);
  const cameraRotate = interpolate(frame, [0, durationInFrames], [3, 1]);

  // Animação da caneta marca-texto amarela (começa no frame 20 e dura 30 frames)
  const markerProgress = interpolate(frame, [20, 50], [0, 100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#0D0F12',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
      }}
    >
      {/* Moldura do Jornal com Perspectiva 3D */}
      <div
        style={{
          transform: `scale(${cameraZoom}) perspective(1000px) rotateX(${cameraRotate}deg)`,
          width: 1400,
          backgroundColor: '#F4EFE6',
          color: '#1A1817',
          padding: '60px 80px',
          boxShadow: '0 30px 60px rgba(0,0,0,0.8), inset 0 0 40px rgba(0,0,0,0.06)',
          borderRadius: 4,
          fontFamily: "'Playfair Display', Georgia, serif",
          border: '1px solid #D6CEBE',
        }}
      >
        {/* Cabeçalho do Jornal */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: '3px double #1A1817',
            paddingBottom: 16,
            marginBottom: 32,
            fontFamily: "'Inter', sans-serif",
            textTransform: 'uppercase',
            fontSize: 16,
            letterSpacing: '0.15em',
            color: '#555',
          }}
        >
          <span>{source_label}</span>
          <span>{date_label}</span>
        </div>

        {/* Manchete Principal */}
        <div style={{ position: 'relative', display: 'inline-block', width: '100%' }}>
          <h1
            style={{
              fontSize: 68,
              lineHeight: 1.15,
              fontWeight: 900,
              margin: '0 0 24px 0',
              textTransform: 'uppercase',
              letterSpacing: '-0.02em',
              color: '#111',
            }}
          >
            {headline}
          </h1>

          {/* Faixa Marca-Texto Amarela Animada */}
          <div
            style={{
              position: 'absolute',
              top: '12%',
              left: 0,
              width: `${markerProgress}%`,
              height: 70,
              backgroundColor: '#FCD34D',
              opacity: 0.65,
              mixBlendMode: 'multiply',
              borderRadius: 3,
              pointerEvents: 'none',
              transform: 'skewX(-4deg)',
              boxShadow: '0 0 10px rgba(252,211,77,0.5)',
            }}
          />
        </div>

        {/* Colunas de Texto Simulado (Estilo Imprensa Antiga) */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 40,
            fontFamily: "'Inter', sans-serif",
            fontSize: 15,
            lineHeight: 1.6,
            color: '#444',
            borderTop: '1px solid #C4BCAB',
            paddingTop: 20,
          }}
        >
          <div>
            Em uma reunião emergencial de fim de semana na sede do Federal Reserve de Nova York, líderes dos maiores
            bancos globais fracassaram em estruturar um plano de resgate privado.
          </div>
          <div>
            A autorização de falência desencadeou um efeito dominó imediato nos derivativos de crédito, congelando o
            mercado de empréstimos interbancários em poucas horas.
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
