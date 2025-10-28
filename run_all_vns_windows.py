import os
import subprocess
import glob
import time
from typing import List, Dict
"""

    execução para windows cmd

"""
# Configurações
NUM_REPLICATIONS = 5
SEEDS = [42, 101, 202, 303, 404] # 5 sementes diferentes
INSTANCES_DIR = "alwabp"
VNS_SCRIPT = "alwabp_vns.py"
OUTPUT_DIR = "vns_results"
SUMMARY_FILE = os.path.join(OUTPUT_DIR, "summary_results.csv")

def run_experiment():
    """
    Executa o VNS para todas as instâncias com múltiplas replicações.
    Esta versão é adaptada para o Windows Command Prompt (CMD) usando
    redirecionamento de entrada (<) em vez do comando 'cat'.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Encontrar todas as instâncias
    instance_files = sorted(glob.glob(os.path.join(INSTANCES_DIR, "*")))
    
    # Cabeçalho do arquivo CSV de resumo
    with open(SUMMARY_FILE, "w") as f:
        f.write("Instance;Replication;Seed;SI;SF;Time_s\n")

    print(f"Iniciando experimentos: {len(instance_files)} instâncias x {NUM_REPLICATIONS} replicações...")

    for instance_path in instance_files:
        instance_name = os.path.basename(instance_path)
        print(f"\nProcessando instância: {instance_name}")
        
        for rep in range(NUM_REPLICATIONS):
            seed = SEEDS[rep]
            output_filename = os.path.join(OUTPUT_DIR, f"{instance_name}_rep{rep+1}_seed{seed}.txt")
            
            print(f"  -> Replicação {rep+1} (Semente: {seed})...", end="", flush=True)
            
            # Comando de execução adaptado para Windows/CMD:
            # python VNS_SCRIPT output_file seed < instance_path
            # Nota: O uso de 'python' em vez de 'python3' é mais comum no Windows
            command = f"python {VNS_SCRIPT} {output_filename} {seed} < {instance_path}"
            
            try:
                # Executa o comando e captura a saída padrão (stdout)
                # O VNS_SCRIPT imprime a linha de resumo (SI;SF;Time_s) no stdout
                result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
                
                # A saída padrão deve ser: SI;SF;Time_s
                summary_line = result.stdout.strip()
                
                # Escreve no arquivo de resumo
                with open(SUMMARY_FILE, "a") as f:
                    f.write(f"{instance_name};{rep+1};{seed};{summary_line}\n")
                
                print(" OK")
                
            except subprocess.CalledProcessError as e:
                print(f" ERRO: Falha na execução. Stderr: {e.stderr.strip()}")
                with open(SUMMARY_FILE, "a") as f:
                    f.write(f"{instance_name};{rep+1};{seed};ERROR;ERROR;ERROR\n")
            except Exception as e:
                print(f" ERRO: {e}")
                with open(SUMMARY_FILE, "a") as f:
                    f.write(f"{instance_name};{rep+1};{seed};ERROR;ERROR;ERROR\n")

    print("\nExperimentos concluídos. Resultados no arquivo:", SUMMARY_FILE)
    print("O usuário deve calcular as médias e desvios a partir deste CSV.")

if __name__ == "__main__":
    run_experiment()
