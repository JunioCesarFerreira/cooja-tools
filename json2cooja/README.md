# json2cooja - Cooja Scenario Runner

This tool converts a JSON description of a wireless sensor network simulation into the necessary Cooja files for execution (`.xml` and `positions.dat`).  
It automates the generation of simulation scripts based on structured input data.

---

## 📁 Project Structure

```
json2cooja/
├── runner.py
├── data/
│   └── simulation_template.xml
├── input/
│   └── input.json
├── library/
│   ├── dto.py
│   ├── parse_json_pos.py
│   └── replace_xml.py
└── output/
    ├── simulation.xml
    └── positions.dat
```

- **`runner.py`** - the main Python script to execute.
- **`library`** - the library Python scripts to conversions and structures.
- **`data/simulation_template.xml`** - the base file for cooja xml configuration build.
- **`input/input.json`** - the JSON file describing the simulation (network, mobile paths, parameters, etc.).
- **`output/`** - directory where the generated Cooja files will be saved.

---

## ⚙️ Requirements

- **Python 3.10+**
- Standard libraries only (no additional dependencies unless specified).

---

## 🚀 Usage

1. Place your simulation description file in the `input` directory:
```
input/input.json
````

2. Run the converter:
```bash
python runner.py
````

3. If successful, the following files will be generated in the `output` directory:

   ```
   output/simulation.xml
   output/positions.dat
   ```

These files can be opened directly in **Cooja** for simulation.

---

## 🧩 Notes

* Ensure the input JSON follows the required schema (nodes, positions, source files, etc.).
* Existing files in `output/` with the same names will be **overwritten**.
* To use the `simulation.xml` file in Cooja, you need to rename it to `simulation.csc`.
* This project is part of a series of related repositories under the SimLab ecosystem.
    - [simlab](https://github.com/JunioCesarFerreira/simlab)
    - [Cooja-Docker-Setup](https://github.com/JunioCesarFerreira/Cooja-Docker-VM-Setup)