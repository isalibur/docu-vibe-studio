import React from 'react';
import { Composition, registerRoot } from 'remotion';
import { DocumentaryParallax, DocumentaryParallaxProps } from './templates/DocumentaryParallax';
import { NewspaperHighlight, NewspaperHighlightProps } from './templates/NewspaperHighlight';
import { DataChartCard, DataChartCardProps } from './templates/DataChartCard';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* 1. Template Anti-Zoompan: Parallax 2.5D */}
      <Composition
        id="DocumentaryParallax"
        component={DocumentaryParallax}
        durationInFrames={180} // 6 segundos a 30fps
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          cameraMotion: 'push_in',
        } as DocumentaryParallaxProps}
      />

      {/* 2. Template Investigativo: Manchete 3D com Marca-Texto */}
      <Composition
        id="NewspaperHighlight"
        component={NewspaperHighlight}
        durationInFrames={180}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          headline: 'MARKET CRASH: BILLIONS VANISH IN MINUTES',
          source_label: 'The Financial Journal - Edição Histórica',
          highlight_words: 'BILLIONS VANISH',
          date_label: '15 de Setembro de 2008',
        } as NewspaperHighlightProps}
      />

      {/* 3. Template de Dados: Gráfico estilo Vox */}
      <Composition
        id="DataChartCard"
        component={DataChartCard}
        durationInFrames={180}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          headline: 'Exposição de Ativos Tóxicos (US$ Trilhões)',
          source_label: 'Fonte: Relatório da Comissão de Inquérito Econômico',
          data_points: [
            { year: '2004', value: 1.2 },
            { year: '2006', value: 4.8 },
            { year: '2008', value: 12.4 },
          ],
        } as DataChartCardProps}
      />
    </>
  );
};

registerRoot(RemotionRoot);
