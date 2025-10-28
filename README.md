# Trabalho Prático Final - GCC118/PCC540: ALWABP com VNS

## 1. Introdução

O presente trabalho visa a resolução do **Problema de Balanceamento de Linhas de Produção e Designação de Trabalhadores (ALWABP)**, um problema de otimização combinatória que busca minimizar o tempo de ciclo de uma linha de montagem ao mesmo tempo em que considera a alocação de trabalhadores com diferentes tempos de execução e restrições de incapacidade. Para tal, foi utilizada a metaheurística **Variable Neighborhood Search (VNS)**.

O ALWABP, introduzido por Miralles et al. (2007), é um problema complexo que generaliza o problema clássico de balanceamento de linha de montagem ao incorporar a heterogeneidade dos trabalhadores. A solução requer a definição de:
1.  Uma atribuição de tarefas a estações.
2.  Uma atribuição de trabalhadores a estações.

O objetivo é minimizar o tempo de ciclo ($C_{\max}$), que é o tempo máximo de processamento entre todas as estações.

## 2. Formulação do Problema como Programa Linear Inteiro Misto (MILP)

A formulação a seguir representa o ALWABP como um modelo de Programação Linear Inteira Mista (MILP), conforme solicitado.

# Formulação do Problema ALWABP como Programa Linear Inteiro Misto (MILP)

O problema ALWABP (Assembly Line Worker Assignment and Balancing Problem) consiste em designar tarefas a estações de trabalho e alocar trabalhadores a essas estações, minimizando o tempo de ciclo da linha de montagem, sujeito a restrições de precedência, capacidade do trabalhador e tempo de ciclo.

## Conjuntos e Parâmetros

| Símbolo | Descrição |
| :--- | :--- |
| $N = \{1, \dots, n\}$ | Conjunto de tarefas. |
| $W = \{1, \dots, k\}$ | Conjunto de trabalhadores. |
| $S = \{1, \dots, m\}$ | Conjunto de estações de trabalho. Assume-se $m=k$ (uma estação por trabalhador). |
| $P$ | Conjunto de pares de precedência $(i, j) \in N \times N$, onde $i$ deve preceder $j$. |
| $t_{wi} \in \mathbb{R}^+$ | Tempo de execução da tarefa $i \in N$ pelo trabalhador $w \in W$. |
| $I_w \subseteq N$ | Conjunto de tarefas que o trabalhador $w$ é incapaz de executar ($t_{wi} = \infty$, $\forall i \in I_w$). |
| $M$ | Uma constante grande (Big M). |

## Variáveis de Decisão

| Símbolo | Tipo | Descrição |
| :--- | :--- | :--- |
| $C_{\max} \in \mathbb{R}^+$ | Variável que representa o tempo de ciclo da linha de produção (a ser minimizado). |
| $y_{si} \in \{0, 1\}$ | $y_{si} = 1$ se a tarefa $i \in N$ é designada à estação $s \in S$. $y_{si} = 0$ caso contrário. |
| $z_{ws} \in \{0, 1\}$ | $z_{ws} = 1$ se o trabalhador $w \in W$ é alocado à estação $s \in S$. $z_{ws} = 0$ caso contrário. |
| $u_{wis} \in \{0, 1\}$ | Variável auxiliar para linearizar o produto $y_{si} \cdot z_{ws}$. $u_{wis}=1$ se a tarefa $i$ é atribuída à estação $s$ e o trabalhador $w$ está na estação $s$. |

## Função Objetivo

Minimizar o tempo de ciclo da linha de produção:
$$
\min C_{\max}
$$

## Restrições

### 1. Designação de Tarefas e Trabalhadores

Cada tarefa deve ser designada a exatamente uma estação:
$$
\sum_{s \in S} y_{si} = 1 \quad \forall i \in N \quad \text{(R1)}
$$

Cada trabalhador deve ser alocado a exatamente uma estação:
$$
\sum_{s \in S} z_{ws} = 1 \quad \forall w \in W \quad \text{(R2)}
$$

Cada estação deve ter exatamente um trabalhador alocado:
$$
\sum_{w \in W} z_{ws} = 1 \quad \forall s \in S \quad \text{(R3)}
$$

### 2. Linearização e Restrição de Incapacidade

Linearização do produto $y_{si} \cdot z_{ws}$ através da variável $u_{wis}$:
$$
u_{wis} \le y_{si} \quad \forall i \in N, w \in W, s \in S \quad \text{(R4.1)}
$$
$$
u_{wis} \le z_{ws} \quad \forall i \in N, w \in W, s \in S \quad \text{(R4.2)}
$$
$$
u_{wis} \ge y_{si} + z_{ws} - 1 \quad \forall i \in N, w \in W, s \in S \quad \text{(R4.3)}
$$

Restrição de Incapacidade: Se o trabalhador $w$ é incapaz de executar a tarefa $i$ (ou seja, $t_{wi} = \infty$), então $u_{wis}$ deve ser zero para todos os $s$:
$$
u_{wis} = 0 \quad \forall i \in I_w, w \in W, s \in S \quad \text{(R5)}
$$
*Nota: Esta restrição pode ser simplificada se a matriz $t_{wi}$ for tratada no modelo, mas a formulação explícita é mais clara.*

### 3. Restrições de Tempo de Ciclo

O tempo total de trabalho em cada estação $s$ deve ser menor ou igual ao tempo de ciclo $C_{\max}$:
$$
\sum_{i \in N} \sum_{w \in W} t_{wi} u_{wis} \le C_{\max} \quad \forall s \in S \quad \text{(R6)}
$$

### 4. Restrições de Precedência

Se a tarefa $i$ precede a tarefa $j$ ($(i, j) \in P$), então a estação que executa $i$ deve ser anterior ou igual à estação que executa $j$:
$$
\sum_{s \in S} s \cdot y_{si} \le \sum_{s \in S} s \cdot y_{sj} \quad \forall (i, j) \in P \quad \text{(R7)}
$$

### 5. Domínio das Variáveis

$$
y_{si} \in \{0, 1\}, z_{ws} \in \{0, 1\}, u_{wis} \in \{0, 1\}, C_{\max} \ge 0 \quad \text{(R8)}
$$

## 3. Algoritmo Proposto: Variable Neighborhood Search (VNS)

A metaheurística escolhida para resolver o ALWABP é o **Variable Neighborhood Search (VNS)**. O VNS é baseado na ideia de mudança sistemática de vizinhanças (neighborhoods) para a busca local e global.

### 3.1. Representação da Solução

Uma solução $S$ é definida por dois vetores principais:
1.  **Atribuição de Tarefas a Estações ($Y$):** Um vetor onde $Y[i]$ é a estação à qual a tarefa $i$ é atribuída.
2.  **Atribuição de Trabalhadores a Estações ($Z$):** Um vetor onde $Z[s]$ é o trabalhador alocado à estação $s$.

### 3.2. Função de Avaliação

A função objetivo é o tempo de ciclo ($C_{\max}$), calculado como o tempo máximo de processamento entre todas as estações. A avaliação também verifica a factibilidade da solução:
1.  **Factibilidade de Precedência:** Para todo par de precedência $(i, j)$, a estação de $i$ deve ser menor ou igual à estação de $j$.
2.  **Factibilidade de Incapacidade:** Nenhuma tarefa $i$ pode ser atribuída a uma estação $s$ cujo trabalhador alocado $Z[s]$ é incapaz de executá-la (tempo de execução $t_{Z[s], i} = \infty$).

Soluções infactíveis são penalizadas com um $C_{\max} = \infty$.

### 3.3. Geração da Solução Inicial

A solução inicial é gerada por uma heurística gulosa:
1.  **Alocação de Trabalhadores:** Uma permutação aleatória dos trabalhadores é atribuída às estações.
2.  **Alocação de Tarefas:** As tarefas são percorridas em ordem topológica (respeitando precedências) e atribuídas à primeira estação factível que satisfaça as restrições de incapacidade e precedência.

### 3.4. Estrutura de Vizinhanças ($N_k$)

O VNS utiliza uma sequência de $K_{max}=3$ vizinhanças:

| $k$ | Vizinhança ($N_k$) | Descrição |
| :--- | :--- | :--- |
| 1 | Task Swap | Troca as estações de duas tarefas aleatórias. |
| 2 | Task Reassignment | Move uma tarefa aleatória para uma estação diferente. |
| 3 | Worker Swap | Troca os trabalhadores alocados a duas estações aleatórias. |

### 3.5. Busca Local (Variable Neighborhood Descent - VND)

O VND é aplicado após a perturbação (Shaking) e utiliza uma sequência de vizinhanças de busca local ($L_{max}=2$):

| $l$ | Vizinhança de Busca Local | Estratégia |
| :--- | :--- | :--- |
| 1 | Task Reassignment | Busca o primeiro movimento de reatribuição de tarefa que melhora a solução (First Improvement). |
| 2 | Worker Swap | Busca o primeiro movimento de troca de trabalhadores que melhora a solução (First Improvement). |

O VND reinicia a busca na vizinhança $l=1$ sempre que uma melhoria é encontrada.

### 3.6. Critério de Parada

O critério de parada é o número máximo de iterações ($MAX\_ITER$) do ciclo principal do VNS.

## 4. Resultados Obtidos com Análise

**(ESTA SEÇÃO DEVE SER PREENCHIDA PELO USUÁRIO APÓS A EXECUÇÃO DO SCRIPT `run_all_vns.py`)**

Esta seção deve apresentar e analisar os resultados computacionais obtidos pela execução da metaheurística VNS, conforme as regras do trabalho.

### 4.1. Configuração Experimental

*   **Hardware:** (Preencher)
*   **Software:** Python 3.x
*   **Parâmetros do VNS:** $MAX\_ITER=50$, $K_{max}=3$.
*   **Replicações:** 5 replicações por instância com sementes diferentes.

### 4.2. Tabela de Resultados

A tabela de resultados deve seguir o formato exigido, apresentando a média das 5 replicações:

| Instância | SI (Média) | SF (Média) | Desvio % (SI-SF)/SI | Desvio % (SF-Ótimo) | Tempo VNS (s) | Tempo Solver (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1\_hes | (Preencher) | (Preencher) | (Preencher) | (Preencher) | (Preencher) | (Preencher) |
| ... | ... | ... | ... | ... | ... | ... |

### 4.3. Análise dos Resultados

**(Preencher com a análise)**

## 5. Conclusão

**(Preencher com a conclusão)**

## 6. Bibliografia

**(Preencher com as referências, incluindo a referência original do ALWABP)**
*   Miralles, C., Garcia-Sabater, J. P., Andres, C., & Cardos, M. (2007). Advantages of assembly lines in sheltered work centres for disabled. A case study. International Journal of Production Economics, 110(1-2), 187-197.
*   (Outras referências)

