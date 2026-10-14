import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';

export interface DataPoint {
  year: string;
  value: number;
}

export interface DataChartCardProps {
  headline?: string;
  source_label?: string;
  data_points?: DataPoint[];
  unit_label?: string;
}

export const DataChartCard: React.FC<DataChartCardProps> = ({
  headline = 'Análise Quantitativa',
  source_label = 'Fonte: Registros Documentais e Estatísticos',
  data_points = [
    { year: '2004', value: 1.2 },
    { year: '2006', value: 4.8 },
    { year: '2008', value: 12.4 },
  ],
  unit_label = '',
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // Movimento de câmera contínuo sutil
  const cameraZoom = interpolate(frame, [0, durationInFrames], [1.0, 1.04]);

  // Barra de progresso da animação dos dados (inicia no frame 15 e cresce até o frame 60)
  const chartProgress = interpolate(frame, [15, 60], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const rawMax = Math.max(...data_points.map((d) => d.value), 1);
  const maxValue = rawMax * 1.25;


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
      {/* Grade técnica de fundo milimetrada */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />

      {/* Cartão de Dados Escuro */}
      <div
        style={{
          transform: `scale(${cameraZoom})`,
          width: 1300,
          backgroundColor: '#161920',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: 12,
          padding: '50px 70px',
          boxShadow: '0 25px 50px rgba(0,0,0,0.6)',
          zIndex: 1,
        }}
      >
        {/* Título de Impacto */}
        <h2
          style={{
            color: '#F8FAFC',
            fontSize: 42,
            fontFamily: "'Inter', sans-serif",
            fontWeight: 800,
            margin: '0 0 10px 0',
            letterSpacing: '-0.02em',
          }}
        >
          {headline}
        </h2>

        {/* Rodapé da Fonte */}
        <p
          style={{
            color: '#94A3B8',
            fontSize: 18,
            fontFamily: "'JetBrains Mono', monospace",
            margin: '0 0 50px 0',
          }}
        >
          {source_label}
        </p>

        {/* Área Gráfica de Barras Verticais */}
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-end',
            justifyContent: 'space-around',
            height: 380,
            borderBottom: '2px solid rgba(255,255,255,0.2)',
            paddingBottom: 10,
          }}
        >
          {data_points.map((point, index) => {
            const heightPercent = (point.value / maxValue) * 100 * chartProgress;
            const isCrisisPeak = index === data_points.length - 1;

            return (
              <div
                key={point.year}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  width: 140,
                }}
              >
                {/* Valor numérico no topo da barra com count-up */}
                <span
                  style={{
                    color: isCrisisPeak ? '#EF4444' : '#FCD34D',
                    fontSize: 28,
                    fontWeight: 700,
                    fontFamily: "'JetBrains Mono', monospace",
                    marginBottom: 12,
                    opacity: chartProgress,
                  }}
                >
                  {(point.value * chartProgress).toFixed(1)}{unit_label}
                </span>


                {/* Barra Animada com gradiente */}
                <div
                  style={{
                    width: '100%',
                    height: `${heightPercent}%`,
                    backgroundColor: isCrisisPeak ? '#EF4444' : '#FCD34D',
                    borderRadius: '6px 6px 0 0',
                    boxShadow: isCrisisPeak
                      ? '0 0 25px rgba(239,68,68,0.4)'
                      : '0 0 20px rgba(252,211,77,0.3)',
                    transition: 'height 0.1s ease',
                  }}
                />

                {/* Rótulo do Ano (Eixo X) */}
                <span
                  style={{
                    color: '#94A3B8',
                    fontSize: 22,
                    fontWeight: 600,
                    fontFamily: "'Inter', sans-serif",
                    marginTop: 20,
                  }}
                >
                  {point.year}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};
