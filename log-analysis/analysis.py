from pathlib import Path
    
from library.process_log_metrics_packet import process_log

DIR_INPUT = Path("input")
DIR_OUTPUT = Path("output")

log_path = DIR_INPUT / "cooja.log"
csv_full  = DIR_OUTPUT / "cooja_metrics.csv"
csv_means = DIR_OUTPUT / "cooja_means.csv"
dir_plots = DIR_OUTPUT / "plots"

process_log(log_path, csv_full, csv_means, dir_plots)