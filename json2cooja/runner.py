import os
import json
from pathlib import Path

# -------------------------------------------------------------------------------------
# Imports locais
# -------------------------------------------------------------------------------------
from library.dto import SimulationConfig
from library.parse_json_pos import generate_positions_from_json
from library.replace_xml import update_simulation_xml

# -------------------------------------------------------------------------------------
# Função principal de conversão dos arquivos de configuração do Cooja
# -------------------------------------------------------------------------------------
def convert_simulation_files(
    config: SimulationConfig, 
    template_file: str = "simulation_template.xml",
    outsim: str = "./output/simulation.xml",
    outpos: str = "./output/positions.dat"
):
    """Processa a simulação completa a partir dos arquivos de configuração."""
    
    # Gera arquivo de posições e obtém posições iniciais
    fixed_positions, mobile_start_positions = generate_positions_from_json(
        config["simulationElements"], 
        output_filename=outpos
    )
    
    # Se não há motes móveis, remove o arquivo positions.dat (não necessário)
    if not mobile_start_positions:
        try:
            os.remove(outpos)
        except FileNotFoundError:
            pass  # evita erro se o arquivo ainda não foi criado
    
    # Identifica motes servidores (assume que o primeiro fixo é o servidor)
    root_motes = [1]
    
    # Gera arquivo XML de simulação
    update_simulation_xml(
        fixed_positions=fixed_positions,
        mobile_positions=mobile_start_positions,
        root_motes=root_motes,
        simulation_time=config["duration"],
        tx_range=config["radiusOfReach"],
        interference_range=config["radiusOfInter"],
        input_file=template_file,
        output_file=outsim
    )

# -------------------------------------------------------------------------------------
# Função main
# -------------------------------------------------------------------------------------
def main():
    # Diretórios e arquivos
    DATA_DIR = Path("data")
    TEMPLATE_XML = DATA_DIR / "simulation_template.xml"

    INPUT_DIR = Path("input")

    OUTPUT_DIR = Path("output")
    OUTPUT_DIR.mkdir(exist_ok=True)

    OUTSIM_XML = OUTPUT_DIR / "simulation.xml"
    OUTPOS_DAT = OUTPUT_DIR / "positions.dat"

    INPUT_JSON =  INPUT_DIR / "input.json"
        
    # Leitura do JSON
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        sim_model = json.load(f)

    # Execução da conversão
    convert_simulation_files(sim_model, TEMPLATE_XML, OUTSIM_XML, OUTPOS_DAT)

    # Mensagens finais
    print(f"✅ Simulação gerada com sucesso a partir de '{INPUT_JSON}'.")
    print(f"📄 Saídas: {OUTSIM_XML} e {OUTPOS_DAT}")

# -------------------------------------------------------------------------------------
# Ponto de entrada
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
