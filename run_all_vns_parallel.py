import os
import subprocess
import glob
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict
"""

    execução paralela

"""
# Configurações
NUM_REPLICATIONS = 5
SEEDS = [42, 101, 202, 303, 404] # 5 sementes diferentes
INSTANCES_DIR = "alwabp"
VNS_SCRIPT = "alwabp_vns.py"
OUTPUT_DIR = "vns_results"
SUMMARY_FILE = os.path.join(OUTPUT_DIR, "summary_results.csv")

# Função para executar uma única replicação
def run_single_replication(instance_path, instance_name, rep, seed):
    """
    Executa uma única replicação do VNS e retorna a linha de resumo.
    """
    # Garante que o diretório de saída exista, pois o ProcessPoolExecutor
    # executa em processos separados onde o estado do diretório pode não ser garantido.
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
    output_filename = os.path.join(OUTPUT_DIR, f"{instance_name}_rep{rep+1}_seed{seed}.txt")
    
    # Comando de execução adaptado para Windows/CMD:
    # python VNS_SCRIPT output_file seed < instance_path
    # Usaremos 'python' para compatibilidade, mas o usuário pode precisar mudar para 'python3'
    command = f"python {VNS_SCRIPT} {output_filename} {seed} < {instance_path}"
    
    try:
        # Executa o comando e captura a saída padrão (stdout)
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        
        # A saída padrão deve ser: SI;SF;Time_s
        summary_line = result.stdout.strip()
        
        # Retorna a linha completa para o CSV
        return f"{instance_name};{rep+1};{seed};{summary_line}"
        
    except subprocess.CalledProcessError as e:
        error_msg = f"ERRO: Falha na execução. Stderr: {e.stderr.strip()}"
        print(f"\n{instance_name} - Replicação {rep+1} (Semente: {seed}): {error_msg}")
        return f"{instance_name};{rep+1};{seed};ERROR;ERROR;ERROR"
    except Exception as e:
        error_msg = f"ERRO: {e}"
        print(f"\n{instance_name} - Replicação {rep+1} (Semente: {seed}): {error_msg}")
        return f"{instance_name};{rep+1};{seed};ERROR;ERROR;ERROR"


def run_experiment_parallel():
    """
    Executa o VNS para todas as instâncias com múltiplas replicações em paralelo.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    instance_files = sorted(glob.glob(os.path.join(INSTANCES_DIR, "*")))
    
    print(f"Iniciando experimentos em paralelo: {len(instance_files)} instâncias x {NUM_REPLICATIONS} replicações.")
    print(f"Resultados serão salvos em: {SUMMARY_FILE}")

    tasks = []
    
    # Cria a lista de tarefas a serem executadas
    for instance_path in instance_files:
        instance_name = os.path.basename(instance_path)
        for rep in range(NUM_REPLICATIONS):
            seed = SEEDS[rep]
            tasks.append((instance_path, instance_name, rep, seed))

    # Executa as tarefas em paralelo
    # O max_workers é o número de processos a serem usados. Por padrão, usa o número de núcleos da CPU.
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(run_single_replication, *task) for task in tasks]
        
        # Cabeçalho do arquivo CSV de resumo
        with open(SUMMARY_FILE, "w") as f:
            f.write("Instance;Replication;Seed;SI;SF;Time_s\n")
            
        print("\nProgresso:")
        
        # Coleta os resultados à medida que ficam prontos
        for i, future in enumerate(as_completed(futures)):
            result_line = future.result()
            
            # Escreve no arquivo de resumo
            with open(SUMMARY_FILE, "a") as f:
                f.write(result_line + "\n")
                
            # Exibe o progresso
            total_tasks = len(tasks)
            progress = (i + 1) / total_tasks * 100
            print(f"  -> Concluído {i + 1}/{total_tasks} ({progress:.2f}%)", end='\r', flush=True)

    print("\n\nExperimentos concluídos. Resultados no arquivo:", SUMMARY_FILE)
    print("O usuário deve calcular as médias e desvios a partir deste CSV.")

if __name__ == "__main__":
    run_experiment_parallel()
