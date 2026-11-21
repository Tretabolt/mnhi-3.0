# CLAUDE.MD — Especificação Mestre: Motor Causal MNHI 3.0

## 1. Domínio e Propósito
O MNHI 3.0 é uma máquina de causalidade verificável e governada projetada para eliminar a "Diluição Causal" (Vanishing Attention) e a suscetibilidade a ruído estatístico falso.

## 2. Regras Arquiteturais Obrigatórias (Camada 0 → Camada Superior)
1. **Identidade vs. Estado (`layer0_hasher.py`):**
   - `id_canonico` (SHA-256) de um vértice é calculado APENAS sobre atributos imutáveis (ex: `name`, `data_criacao`, `entity_type`).
   - Atributos mutáveis (`estado_emocional`, `localizacao`, `saude`) são explicitamente excluídos do hash.
   - `id_aresta_canonica` concatena: `origin_id + target_id + dados_canonicos_relacao`.
2. **Deduplicação e Sharding Canônico (`graph_store.py`):**
   - A ingestão verifica existência do hash antes de gravar; duplicados não poluem o grafo.
   - Os primeiros `X` bits do `id_canonico` definem o shard físico destino.
3. **Auditoria de Integridade em Background:**
   - Re-hasheia vértices e arestas armazenados para detectar adulteração ou corrupção silenciosa.
4. **Extrapolation (`extrapolation.py`):**
   - Gera cenários contrafactuais a partir da Geodésica da Verdade sem alterar ou diluir o fato original.
   - Mede a curvatura/distância causal (`D_hiperbolica`) via divergência informacional (KL simetrizada / JSD).
5. **Heptagram (`heptagram.py`):**
   - Rules Engine nativo integrado à inferência; gera **PCE** (Pontuação de Conformidade Ética entre `0.0` e `1.0`).
6. **Pentacosagram (`pentacosagram.py`):**
   - Cadeia de auditoria imutável *append-only* registrando ações, cenários extrapolados e PCE.

## 3. Critério de Validação Principal (Memória do Oráculo)
- Fato verdadeiro distante + 500.000 tokens de ruído temporal + aresta falsa recente (peso `0.2`) -> O MNHI 3.0 deve retornar `id_aresta_VERDADE` (peso `0.9`) sem degradação por distância temporal.

## Nota de verificação (20/11/2026, Alice)

Conferido contra o código — a especificação acima é do Dan, não foi
reescrita; o que segue é só o que o código de fato faz, onde difere:

1. **`D_hiperbolica` via "KL simetrizada / JSD" (§2, item 4): não é o
   que o código faz.** `extrapolation.py` calcula `d_hiperbolica` com
   `causal_kl_divergence` — uma KL simples, de um só sentido, entre
   duas distribuições binárias (log base 2). Não há KL simetrizada e
   não há nenhuma função JSD no código. O valor é usado de verdade
   (`heptagram.py` calcula o PCE a partir dele), mas a divergência
   nomeada no documento não é a implementada.
2. **"Auditoria de Integridade em Background" (§2, item 3): parcial.**
   `run_integrity_audit()` existe em `graph_store.py` e é testada
   (chamada em `test_layer0_hasher.py` e `test_oracle_memory_500k.py`),
   mas nada a executa em background: não há thread, agendador ou
   chamada periódica — é um método síncrono, chamado à mão.
3. **"Rules Engine nativo" (§2, item 5): questão de nome.** Não existe
   um módulo separado de rules engine; o papel é cumprido pela própria
   classe `Heptagram` (`heptagram.py`), que calcula o PCE a partir de
   `d_hiperbolica`. Não falta funcionalidade — só não há um módulo com
   esse nome.
