#!/usr/bin/env python3
import os
import sys
import shutil
from pathlib import Path

def main():
    # ----------------------------
    # 1. Lê o argumento
    # ----------------------------
    if len(sys.argv) != 2:
        print("Uso: python copy_simulation.py <nome_da_simulacao>")
        sys.exit(1)

    sim_name = sys.argv[1]

    # ----------------------------
    # 2. Caminhos base
    # ----------------------------
    script_dir = Path(__file__).resolve().parent
    database_dir = script_dir / "database"
    dest_dir = database_dir / sim_name

    # ----------------------------
    # 3. Cria diretórios destino
    # ----------------------------
    (dest_dir / "input").mkdir(parents=True, exist_ok=True)
    (dest_dir / "output").mkdir(parents=True, exist_ok=True)

    # ----------------------------
    # 4. Define origens relativas
    # ----------------------------
    src_json2cooja_input  = (script_dir / "../json2cooja/input").resolve()
    src_json2cooja_output = (script_dir / "../json2cooja/output").resolve()
    src_log_input         = (script_dir / "../log-analysis/input").resolve()
    src_log_output        = (script_dir / "../log-analysis/output").resolve()

    # ----------------------------
    # 5. Função auxiliar de cópia
    # ----------------------------
    def copytree(src: Path, dst: Path):
        """Copia src → dst preservando estrutura, substituindo se existir."""
        if not src.exists():
            print(f"[AVISO] Diretório não encontrado: {src}")
            return
        for item in src.iterdir():
            dest_item = dst / item.name
            if item.is_dir():
                shutil.copytree(item, dest_item, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest_item)

    # ----------------------------
    # 6. Cópias
    # ----------------------------
    print(f"[INFO] Copiando arquivos para {dest_dir} ...")

    # ../json2cooja/input → ./database/<sim>/input
    copytree(src_json2cooja_input, dest_dir / "input")

    # ../json2cooja/output → ./database/<sim>/input
    copytree(src_json2cooja_output, dest_dir / "input")

    # ../log-analysis/input → ./database/<sim>/output
    copytree(src_log_input, dest_dir / "output")

    # ../log-analysis/output → ./database/<sim>/output
    copytree(src_log_output, dest_dir / "output")

    print(f"[OK] Cópia concluída com sucesso: {dest_dir}")

if __name__ == "__main__":
    main()
