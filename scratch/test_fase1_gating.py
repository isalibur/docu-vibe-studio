import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.stage1_director.script_director import ScriptDirector

print("=== INICIANDO GATING TEST DA FASE 1: DIRETOR VIA 9ROUTER ===")
start = time.time()

director = ScriptDirector()
manifest = director.generate_script(
    topic_or_text="O vesúvio de pompeia",
    project_id="gating_fase1_test",
    title="O Vesúvio de Pompeia: Catástrofe no Império",
    target_duration_sec=30
)
elapsed = time.time() - start

print(f"\n[1] Tempo de execução: {elapsed:.2f} segundos")
print(f"[2] Título gerado: '{manifest.title}'")
print(f"[3] Quantidade de cenas: {len(manifest.scenes)} (Esperado: 3)")

assert len(manifest.scenes) == 3, f"Erro: esperava 3 cenas, obteve {len(manifest.scenes)}"

total_words = 0
queries = []
for s in manifest.scenes:
    words = len(s.narration_text.split())
    total_words += words
    queries.append(s.visual_config.search_query)
    print(f"\n--- CENA {s.scene_id} ---")
    print(f"Texto ({words} palavras): {s.narration_text}")
    print(f"Tipo Visual: {s.visual_type.value}")
    print(f"Busca Visual: '{s.visual_config.search_query}'")
    print(f"Movimento: {s.visual_config.camera_motion}")

print(f"\n[4] Total de palavras: {total_words} (Faixa ideal: 60-80 palavras)")
print(f"[5] Verificação de queries únicas: {len(set(queries))} únicas de {len(queries)}")

assert len(set(queries)) == len(queries), "Erro: queries de busca repetidas detectadas!"
assert total_words >= 55, f"Erro: contagem de palavras muito baixa ({total_words})"

print("\n" + "="*60)
print(">>> GATING TEST FASE 1 APROVADO COM LOUVOR! <<<")
print("="*60)
