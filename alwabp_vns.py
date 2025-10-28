import sys
import math
import random
import time
from typing import List, Tuple, Dict, Any

# Constante para representar tempo infinito (incapacidade)
INF = float('inf')

class ALWABPInstance:
    """
    Armazena os dados de uma instância do problema ALWABP.
    """
    def __init__(self, num_tasks: int, num_workers: int, task_times: List[List[float]], precedences: List[Tuple[int, int]]):
        self.num_tasks = num_tasks  # n
        self.num_workers = num_workers  # k (também o número de estações m)
        # task_times[w][i] é o tempo da tarefa i+1 pelo trabalhador w+1 (0-indexado)
        self.task_times = task_times
        # precedences é uma lista de pares (i, j) onde i deve preceder j (1-indexado)
        self.precedences = precedences
        # Dicionário de adjacência para acesso rápido às precedências (1-indexado)
        self.predecessors: Dict[int, List[int]] = {i: [] for i in range(1, num_tasks + 1)}
        self.successors: Dict[int, List[int]] = {i: [] for i in range(1, num_tasks + 1)}
        for i, j in precedences:
            self.successors[i].append(j)
            self.predecessors[j].append(i)

    @classmethod
    def from_stdin(cls) -> 'ALWABPInstance':
        """
        Lê os dados da instância a partir da entrada padrão (stdin)
        conforme o formato especificado.
        """
        try:
            # 1. Número de tarefas (n)
            line = sys.stdin.readline().strip()
            if not line:
                raise EOFError("Fim de arquivo inesperado ao ler o número de tarefas.")
            num_tasks = int(line)
        except Exception as e:
            print(f"Erro ao ler o número de tarefas: {e}", file=sys.stderr)
            sys.exit(1)

        # 2. Matriz de tempos de tarefa (t_wi)
        task_times_raw: List[List[float]] = []
        num_workers = 0
        for _ in range(num_tasks):
            try:
                line = sys.stdin.readline().strip()
                if not line:
                    raise EOFError("Fim de arquivo inesperado ao ler tempos de tarefa.")
                
                # Os tempos são lidos como strings e convertidos para float
                times = [float(t) for t in line.split()]
                task_times_raw.append(times)
                
                # O número de trabalhadores (k) é o número de colunas na primeira linha
                if num_workers == 0:
                    num_workers = len(times)
                elif len(times) != num_workers:
                    raise ValueError("Número inconsistente de trabalhadores/tempos por tarefa.")
            except Exception as e:
                print(f"Erro ao ler tempos de tarefa: {e}", file=sys.stderr)
                sys.exit(1)

        if num_workers == 0 and num_tasks > 0:
             raise ValueError("Não foi possível determinar o número de trabalhadores.")
        
        # Transpor a matriz para ter task_times[w][i]
        # task_times[w][i] = tempo da tarefa i (0-indexado) pelo trabalhador w (0-indexado)
        if num_tasks > 0 and num_workers > 0:
            task_times_transposed = [[task_times_raw[i][w] for i in range(num_tasks)] for w in range(num_workers)]
        else:
            task_times_transposed = []

        # 3. Restrições de precedência (i j)
        precedences: List[Tuple[int, int]] = []
        while True:
            try:
                line = sys.stdin.readline().strip()
                if not line:
                    # Se não houver mais linhas, pode ser o fim do arquivo
                    break
                
                parts = line.split()
                if not parts:
                    continue

                i, j = map(int, parts)
                
                if i == -1 and j == -1:
                    break
                
                # As tarefas são 1-indexadas no arquivo
                precedences.append((i, j))
            except Exception as e:
                # Se a linha não for -1 -1 e não for um par de inteiros, é um erro
                if line and not line.startswith('#'):
                     print(f"Erro ao ler precedências na linha: {line}. Erro: {e}", file=sys.stderr)
                     sys.exit(1)
                elif not line:
                     break
                
        return cls(num_tasks, num_workers, task_times_transposed, precedences)

class ALWABPSolution:
    """
    Representa uma solução para o problema ALWABP.
    Uma solução é definida pela alocação de tarefas a estações e trabalhadores a estações.
    """
    def __init__(self, instance: ALWABPInstance, task_station_assignment: List[int], worker_station_assignment: List[int]):
        self.instance = instance
        # task_station_assignment[i] = s (tarefa i (0-indexada) na estação s (0-indexada))
        self.task_station_assignment = task_station_assignment
        # worker_station_assignment[s] = w (trabalhador w (0-indexado) na estação s (0-indexada))
        self.worker_station_assignment = worker_station_assignment
        self.cycle_time = INF
        self.is_feasible = False
        self.station_times: List[float] = []

    def evaluate(self):
        """
        Avalia a solução, verificando a factibilidade e calculando o tempo de ciclo (C_max).
        """
        inst = self.instance
        n = inst.num_tasks
        m = inst.num_workers # número de estações

        # 1. Verificar Factibilidade de Precedência
        # A tarefa i deve estar em uma estação anterior ou igual à estação da tarefa j, se i precede j.
        for i_task_1, j_task_2 in inst.precedences:
            # Converter para 0-indexado para acesso ao vetor
            i = i_task_1 - 1
            j = j_task_2 - 1
            
            # task_station_assignment é 0-indexado, representando a estação (0 a m-1)
            station_i = self.task_station_assignment[i]
            station_j = self.task_station_assignment[j]

            # Se alguma tarefa não foi alocada (station_i == -1), a solução é infactível
            if station_i == -1 or station_j == -1:
                self.is_feasible = False
                self.cycle_time = INF
                self.station_times = [INF] * m
                return

            if station_i > station_j:
                self.is_feasible = False
                self.cycle_time = INF
                self.station_times = [INF] * m
                return

        # 2. Calcular o tempo de trabalho em cada estação e verificar incapacidade
        station_times = [0.0] * m
        
        # Agrupar tarefas por estação
        tasks_in_station: Dict[int, List[int]] = {s: [] for s in range(m)}
        for i in range(n):
            station = self.task_station_assignment[i]
            tasks_in_station[station].append(i) # i é a tarefa 0-indexada

        # Calcular o tempo de cada estação
        for s in range(m):
            # w é o trabalhador 0-indexado alocado à estação s
            w = self.worker_station_assignment[s]
            
            current_station_time = 0.0
            for i in tasks_in_station[s]:
                # i é o índice da tarefa (0-indexado)
                # w é o índice do trabalhador (0-indexado)
                task_time = inst.task_times[w][i]

                # 2.1. Verificar Incapacidade (tempo infinito)
                if task_time >= INF: # Usamos >= INF para capturar float('inf') e valores muito grandes
                    self.is_feasible = False
                    self.cycle_time = INF
                    self.station_times = [INF] * m
                    return

                current_station_time += task_time
            
            station_times[s] = current_station_time

        # 3. Calcular C_max
        self.is_feasible = True
        self.station_times = station_times
        self.cycle_time = max(station_times) if station_times else 0.0
    
    def __lt__(self, other: 'ALWABPSolution') -> bool:
        """
        Compara duas soluções. Usado para encontrar a melhor solução.
        """
        # Prioridade para factibilidade
        if self.is_feasible and not other.is_feasible:
            return True
        if not self.is_feasible and other.is_feasible:
            return False
        
        # Se ambas infactíveis ou ambas factíveis, compara o tempo de ciclo
        return self.cycle_time < other.cycle_time

    def to_output_format(self) -> str:
        """
        Formata a solução para a saída padrão (stdout) no formato exigido.
        """
        if not self.is_feasible:
            return f"{INF}\nSolução Infactível"
        
        # Formato de saída:
        # C_max
        # Estação 1: Trabalhador w1 -> Tarefas: t1 t2 ...
        # Estação 2: Trabalhador w2 -> Tarefas: t3 t4 ...
        
        output = f"{self.cycle_time:.6f}\n" # Tempo de ciclo com 6 casas decimais
        
        m = self.instance.num_workers
        n = self.instance.num_tasks
        
        # Agrupar tarefas (1-indexadas) por estação (1-indexada)
        station_tasks: Dict[int, List[int]] = {s + 1: [] for s in range(m)}
        for i in range(n):
            station = self.task_station_assignment[i] + 1 # 1-indexada
            station_tasks[station].append(i + 1) # i+1 é a tarefa 1-indexada
        
        # Gerar a saída
        for s in range(1, m + 1):
            w = self.worker_station_assignment[s - 1] + 1 # Trabalhador 1-indexado
            tasks_str = " ".join(map(str, sorted(station_tasks[s])))
            output += f"Estação {s}: Trabalhador {w} -> Tarefas: {tasks_str}\n"
            
        return output.strip()

# --- Funções Auxiliares para o VNS ---

def check_precedence_feasibility(instance: ALWABPInstance, task_station_assignment: List[int]) -> bool:
    """ Verifica se a atribuição de tarefas a estações respeita as precedências. """
    for i_task_1, j_task_2 in instance.precedences:
        i = i_task_1 - 1
        j = j_task_2 - 1
        station_i = task_station_assignment[i]
        station_j = task_station_assignment[j]
        if station_i == -1 or station_j == -1: return False
        if station_i > station_j: return False
    return True

def generate_initial_solution(instance: ALWABPInstance) -> ALWABPSolution:
    """
    Gera uma solução inicial factível usando uma heurística gulosa.
    1. Alocação de trabalhadores aleatória.
    2. Alocação de tarefas: Alocar tarefas na ordem topológica para a primeira
       estação que satisfaz a restrição de capacidade (tempo de ciclo inicial grande).
    """
    n = instance.num_tasks
    m = instance.num_workers
    
    # 1. Alocação de Trabalhadores a Estações (Permutação aleatória)
    workers = list(range(m)) # 0-indexados
    random.shuffle(workers)
    worker_station_assignment = workers # worker_station_assignment[s] = w

    # 2. Alocação de Tarefas a Estações (Heurística Gulosa)
    task_station_assignment = [-1] * n # -1 indica não alocada
    
    # Ordenação topológica das tarefas (para garantir precedência)
    # Usando Kahn's algorithm
    in_degree = {i: len(instance.predecessors[i+1]) for i in range(n)}
    queue = [i for i in range(n) if in_degree[i] == 0]
    topological_order = []
    
    while queue:
        i = queue.pop(0)
        topological_order.append(i)
        
        for j_task_1 in instance.successors[i+1]:
            j = j_task_1 - 1
            in_degree[j] -= 1
            if in_degree[j] == 0:
                queue.append(j)

    if len(topological_order) != n:
        # O grafo de precedência tem um ciclo, o que não deveria ocorrer no ALWABP
        print("Erro: Ciclo detectado no grafo de precedência.", file=sys.stderr)
        # Retornar uma solução infactível
        return ALWABPSolution(instance, [-1] * n, worker_station_assignment)

    # Alocação de tarefas na ordem topológica
    current_station_times = [0.0] * m
    
    for i in topological_order: # Tarefa 0-indexada
        task_1_index = i + 1
        
        # Tentar alocar a tarefa i para a estação com menor tempo de trabalho atual
        best_station = -1
        min_time = INF
        
        # Tentar alocar na ordem das estações (0 a m-1)
        for s in range(m): # Estação 0-indexada
            w = worker_station_assignment[s] # Trabalhador 0-indexado
            task_time = instance.task_times[w][i]

            # Restrição de Incapacidade
            if task_time >= INF:
                continue
            
            # Restrição de Precedência (já garantida pela ordem topológica,
            # mas vamos garantir que todos os predecessores estão em estações <= s)
            precedence_ok = True
            for pred_1_index in instance.predecessors[task_1_index]:
                pred_0_index = pred_1_index - 1
                # A estação do predecessor deve ser <= estação atual
                if task_station_assignment[pred_0_index] > s:
                    precedence_ok = False
                    break
            
            if not precedence_ok:
                continue

            # Heurística: Alocar para a primeira estação factível (ou a que minimiza o tempo)
            # Vamos usar a primeira estação factível para simplificar a busca inicial
            task_station_assignment[i] = s
            break
        
        if task_station_assignment[i] == -1:
            # Se não for possível alocar a tarefa i, a instância é infactível
            print(f"Erro: Não foi possível alocar a tarefa {i+1} de forma factível.", file=sys.stderr)
            return ALWABPSolution(instance, [-1] * n, worker_station_assignment)

    sol = ALWABPSolution(instance, task_station_assignment, worker_station_assignment)
    sol.evaluate()
    
    # Se a solução for infactível, tentar uma nova alocação de trabalhadores aleatória
    # ou uma heurística de alocação de tarefas diferente.
    # Por agora, confiamos que a heurística gulosa produzirá uma solução factível.
    # O VNS irá refinar o balanceamento.
    
    return sol

# --- Implementação do VNS ---

def vns(instance: ALWABPInstance, max_iter: int, k_max: int) -> Tuple[ALWABPSolution, ALWABPSolution]:
    """
    Implementação da metaheurística Variable Neighborhood Search (VNS).
    """
    
    # 1. Geração da Solução Inicial
    s_initial = generate_initial_solution(instance)
    s_best = s_initial
    s_current = s_initial
    
    if not s_best.is_feasible:
        # Se a solução inicial não é factível, o VNS pode não convergir
        # Mas vamos tentar, pois a busca local pode reparar a solução.
        pass
        
    iteration = 0
    while iteration < max_iter:
        k = 1
        while k <= k_max:
            # 2. Shaking (Perturbação)
            s_prime = shaking(s_current, k)
            
            # 3. Busca Local (Local Search)
            # Usaremos o VNS-Descent (VND) no lugar do Local Search
            s_prime_prime = vnd(s_prime)
            
            # 4. Movimento (Move)
            if s_prime_prime < s_current:
                s_current = s_prime_prime
                if s_current < s_best:
                    s_best = s_current
                    k = 1 # Reinicia a busca
                else:
                    k += 1 # Vai para a próxima vizinhança
            else:
                k += 1 # Vai para a próxima vizinhança
                
        iteration += 1
        
    return s_initial, s_best

def shaking(solution: ALWABPSolution, k: int) -> ALWABPSolution:
    """
    Perturba a solução atual (Shaking) usando a k-ésima vizinhança.
    Vizinhanças propostas (k):
    k=1: Troca de 2 tarefas entre 2 estações diferentes (Task Swap).
    k=2: Reatribuição de 1 tarefa para uma estação diferente (Task Reassignment).
    k=3: Troca de 2 trabalhadores entre 2 estações diferentes (Worker Swap).
    """
    inst = solution.instance
    n = inst.num_tasks
    m = inst.num_workers
    
    new_task_station_assignment = list(solution.task_station_assignment)
    new_worker_station_assignment = list(solution.worker_station_assignment)
    
    if k == 1:
        # Task Swap: Troca de 2 tarefas entre 2 estações
        if n < 2: return solution
        
        # Seleciona duas tarefas diferentes
        i1, i2 = random.sample(range(n), 2)
        
        # Troca as estações
        s1 = new_task_station_assignment[i1]
        s2 = new_task_station_assignment[i2]
        
        new_task_station_assignment[i1] = s2
        new_task_station_assignment[i2] = s1
        
    elif k == 2:
        # Task Reassignment: Reatribuição de 1 tarefa para uma estação diferente
        if n < 1: return solution
            
        # Seleciona uma tarefa e uma nova estação
        i = random.choice(range(n))
        s_old = new_task_station_assignment[i]
        
        # Seleciona uma nova estação diferente da atual
        possible_new_stations = [s for s in range(m) if s != s_old]
        if not possible_new_stations: return solution
            
        s_new = random.choice(possible_new_stations)
        
        new_task_station_assignment[i] = s_new
        
    elif k == 3:
        # Worker Swap: Troca de 2 trabalhadores entre 2 estações
        if m < 2: return solution
            
        # Seleciona duas estações diferentes
        s1, s2 = random.sample(range(m), 2)
        
        # Troca os trabalhadores
        w1 = new_worker_station_assignment[s1]
        w2 = new_worker_station_assignment[s2]
        
        new_worker_station_assignment[s1] = w2
        new_worker_station_assignment[s2] = w1
        
    else:
        # Para k > 3, repete o movimento de reatribuição de tarefa
        return shaking(solution, 2)
        
    s_prime = ALWABPSolution(inst, new_task_station_assignment, new_worker_station_assignment)
    s_prime.evaluate()
    return s_prime

def vnd(solution: ALWABPSolution) -> ALWABPSolution:
    """
    Variable Neighborhood Descent (VND) - Busca Local com Múltiplas Vizinhanças.
    Vizinhanças (l):
    l=1: Task Reassignment (First Improvement)
    l=2: Worker Swap (First Improvement)
    """
    s_current = solution
    l_max = 2
    l = 1
    
    while l <= l_max:
        s_prime = s_current
        
        if l == 1:
            # Vizinhança 1: Task Reassignment (Mover 1 tarefa para outra estação)
            s_prime = local_search_task_reassignment(s_current)
        elif l == 2:
            # Vizinhança 2: Worker Swap (Trocar 2 trabalhadores de estação)
            s_prime = local_search_worker_swap(s_current)
            
        if s_prime < s_current:
            s_current = s_prime
            l = 1 # Reinicia a busca
        else:
            l += 1 # Vai para a próxima vizinhança
            
    return s_current

def local_search_task_reassignment(solution: ALWABPSolution) -> ALWABPSolution:
    """
    Busca Local (First Improvement) usando a vizinhança de Task Reassignment.
    """
    s_current = solution
    inst = solution.instance
    n = inst.num_tasks
    m = inst.num_workers
    
    improved = True
    while improved:
        improved = False
        
        # Iterar sobre todos os movimentos de Task Reassignment
        for i in range(n): # Tarefa 0-indexada
            s_old = s_current.task_station_assignment[i]
            
            for s_new in range(m): # Nova estação 0-indexada
                if s_new == s_old:
                    continue
                
                # Criar nova solução
                new_task_station_assignment = list(s_current.task_station_assignment)
                new_task_station_assignment[i] = s_new
                
                # Verificar factibilidade de precedência antes de avaliar
                if not check_precedence_feasibility(inst, new_task_station_assignment):
                    continue
                
                s_neighbor = ALWABPSolution(inst, new_task_station_assignment, s_current.worker_station_assignment)
                s_neighbor.evaluate()
                
                # Critério de Melhoria (First Improvement)
                if s_neighbor < s_current:
                    s_current = s_neighbor
                    improved = True
                    break # Sai do loop de s_new e recomeça a busca
            
            if improved:
                break # Sai do loop de i e recomeça a busca
                
    return s_current

def local_search_worker_swap(solution: ALWABPSolution) -> ALWABPSolution:
    """
    Busca Local (First Improvement) usando a vizinhança de Worker Swap.
    """
    s_current = solution
    inst = solution.instance
    m = inst.num_workers
    
    improved = True
    while improved:
        improved = False
        
        # Iterar sobre todos os pares de estações (s1, s2)
        for s1 in range(m):
            for s2 in range(s1 + 1, m):
                # Criar nova solução
                new_worker_station_assignment = list(s_current.worker_station_assignment)
                
                # Troca os trabalhadores
                new_worker_station_assignment[s1], new_worker_station_assignment[s2] = \
                    new_worker_station_assignment[s2], new_worker_station_assignment[s1]
                
                s_neighbor = ALWABPSolution(inst, s_current.task_station_assignment, new_worker_station_assignment)
                s_neighbor.evaluate()
                
                # Critério de Melhoria (First Improvement)
                if s_neighbor < s_current:
                    s_current = s_neighbor
                    improved = True
                    break # Sai do loop de s2 e recomeça a busca
            
            if improved:
                break # Sai do loop de s1 e recomeça a busca
                
    return s_current


# --- Função Principal ---

def main():
    # O primeiro argumento da linha de comando é o nome do arquivo para gravar a melhor solução
    if len(sys.argv) < 2:
        output_filename = "best_solution.txt"
    else:
        output_filename = sys.argv[1]
        
    # 1. Leitura da Instância
    # A entrada é redirecionada para o stdin pelo usuário
    instance = ALWABPInstance.from_stdin()
    
    # 2. Parâmetros do VNS
    # Parâmetros podem ser lidos da linha de comando em uma versão mais completa
    # Por enquanto, usamos valores fixos.
    MAX_ITER = 50 # Número máximo de iterações do VNS
    K_MAX = 3 # Número máximo de vizinhanças para o Shaking
    
    # 3. Execução do VNS
    # O segundo argumento (opcional) é a semente aleatória.
    if len(sys.argv) > 2:
        try:
            seed_value = int(sys.argv[2])
            random.seed(seed_value)
        except ValueError:
            print("Aviso: Semente aleatória inválida. Usando semente padrão.", file=sys.stderr)
            random.seed(42) # Semente padrão
    else:
        random.seed(42) # Semente padrão
        
    start_time = time.time()
    
    # 3. Execução do VNS
    initial_solution, best_solution = vns(instance, MAX_ITER, K_MAX)
    
    end_time = time.time()
    computational_time = end_time - start_time
    
    # 4. Saída
    # 4. Saída
    # Imprimir a melhor solução encontrada na saída padrão (stdout)
    # O formato de saída para o script de automação será:
    # SI;SF;TempoComputacional
    
    si_value = initial_solution.cycle_time if initial_solution.is_feasible else INF
    sf_value = best_solution.cycle_time if best_solution.is_feasible else INF
    
    print(f"{si_value};{sf_value};{computational_time:.4f}")
    
    # Gravar a melhor solução (completa) no arquivo especificado
    try:
        with open(output_filename, "w") as f:
            f.write(best_solution.to_output_format())
    except Exception as e:
        print(f"Erro ao gravar a solução no arquivo {output_filename}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()

