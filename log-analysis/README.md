# log-analysis - Cooja Log Analysis

This tool extracts structured data from **COOJA simulation logs** (`.log`) of a wireless sensor network and generates **metrics reports** (`.csv`) and **plots** for data analysis.  
It provides automated processing of simulation logs to compute latency, RSSI, energy, packet loss, and other performance indicators.

---

## 📁 Directory Structure

```

log-analysis/
├── analysis.py
├── input/
│   └── cooja.log
├── output/
│   ├── cooja_metrics.csv
│   ├── cooja_means.csv
│   └── plots/
│       ├── boxes/
│       │   └── *.png
│       └── lines/
│           └── *.png
└── library/
└── process_log_metrics_packet.py

````

- **`analysis.py`** – Main execution script. Loads the log file and calls the processing library.
- **`library/`** – Contains helper modules for log parsing, metric computation, and plotting.
- **`input/cooja.log`** – Raw Cooja log file produced by the simulation.
- **`output/`** – Directory for generated results, including CSV files and plots.

---

## ⚙️ Requirements

- **Python 3.10+**
- Libraries:
  - `pandas`
  - `matplotlib`
  - *(optional)* `seaborn` (for enhanced boxplot visualization)

If `seaborn` is not installed, the script automatically falls back to standard Matplotlib boxplots.

Install dependencies with:
```bash
pip install pandas matplotlib seaborn
````

---

## 🚀 Usage

1. Place your simulation log file in the `input` directory:

   ```
   input/cooja.log
   ```

2. Run the analysis:

   ```bash
   python analysis.py
   ```

3. After successful execution, the following files will be generated in the `output` directory:

   ```
   output/cooja_metrics.csv     # All extracted metrics
   output/cooja_means.csv       # Mean values per node
   output/plots/lines/*.png     # Time-series plots
   output/plots/boxes/*.png     # Boxplots comparing nodes and runs
   ```

---

## 📊 Generated Metrics

Depending on the fields available in the simulation log, the script may extract and analyze:

* `rtt_latency`, `r2n_latency`, `n2r_latency`
* `rssi`
* `radio_rx_energy_mj`, `radio_tx_energy_mj`, `cpu_energy_mj`
* `lost_packets_r2n`, `lost_packets_n2r`
* `hops`

For each node, a mean value table is produced and displayed in the console.

---

## 🧩 Notes

* Existing files in the `output/` directory will be **overwritten**.
* Plots are organized by metric:
  * **`lines/`** – metric variation over time.
  * **`boxes/`** – distribution comparison among nodes.
* The project is part of the **SimLab** ecosystem:

  * [simlab](https://github.com/JunioCesarFerreira/simlab)
  * [Cooja-Docker-Setup](https://github.com/JunioCesarFerreira/Cooja-Docker-VM-Setup)
