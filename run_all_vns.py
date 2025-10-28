import os
import subprocess
import glob
import time
from typing import List, Dict
"""

    primeira versão (para linux)

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
    Este script deve ser executado no diretório onde estão os arquivos.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Encontrar todas as instâncias
    # O user tem o arquivo alwabp.tar.gz, que foi descompactado em 'alwabp/'
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
            # O nome do arquivo de solução completa é gerado aqui, mas o VNS_SCRIPT
            # irá gerar a saída resumida para o stdout.
            output_filename = os.path.join(OUTPUT_DIR, f"{instance_name}_rep{rep+1}_seed{seed}.txt")
            
            # O comando de execução deve ser compatível com o shell (Linux/WSL/Git Bash)
            # O usuário pode precisar adaptar para o Command Prompt do Windows.
            # Usaremos a sintaxe compatível com Unix/WSL/Git Bash.
            # Comando: cat instance | python3 vns_script output_file seed
            command = f"cat {instance_path} | python3 {VNS_SCRIPT} {output_filename} {seed}"
            
            print(f"  -> Replicação {rep+1} (Semente: {seed})...", end="", flush=True)
            
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
