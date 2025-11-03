import os
import json
from pathlib import Path

# -------------------------------------------------------------------------------------
# Local imports
# -------------------------------------------------------------------------------------
from library.dto import SimulationConfig
from library.parse_json_pos import generate_positions_from_json
from library.replace_xml import update_simulation_xml

# -------------------------------------------------------------------------------------
# Main function for converting Cooja configuration files
# -------------------------------------------------------------------------------------
def convert_simulation_files(
    config: SimulationConfig, 
    template_file: str = "simulation_template.xml",
    outsim: str = "./output/simulation.xml",
    outpos: str = "./output/positions.dat"
):
    """Processes the full simulation from the configuration files."""
    
    # Generate the positions file and obtain initial positions
    fixed_positions, mobile_start_positions = generate_positions_from_json(
        config["simulationElements"], 
        output_filename=outpos
    )
    
    # If there are no mobile motes, remove the positions.dat file (not needed)
    if not mobile_start_positions:
        try:
            os.remove(outpos)
        except FileNotFoundError:
            pass  # avoid error if the file has not been created yet
    
    # Identify root motes (assumes the first fixed mote is the root)
    root_motes = [1]
    
    # Generate the XML simulation file
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
# Main function
# -------------------------------------------------------------------------------------
def main():
    # Directories and files
    DATA_DIR = Path("data")
    TEMPLATE_XML = DATA_DIR / "simulation_template.xml"

    INPUT_DIR = Path("input")

    OUTPUT_DIR = Path("output")
    OUTPUT_DIR.mkdir(exist_ok=True)

    OUTSIM_XML = OUTPUT_DIR / "simulation.xml"
    OUTPOS_DAT = OUTPUT_DIR / "positions.dat"

    INPUT_JSON =  INPUT_DIR / "input.json"
        
    # Read the JSON configuration
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        sim_model = json.load(f)

    # Run the conversion
    convert_simulation_files(sim_model, TEMPLATE_XML, OUTSIM_XML, OUTPOS_DAT)

    # Final messages
    print(f"✅ Simulation successfully generated from '{INPUT_JSON}'.")
    print(f"📄 Output files: {OUTSIM_XML} and {OUTPOS_DAT}")

# -------------------------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
