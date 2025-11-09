import csv
from pathlib import Path
import matplotlib.pyplot as plt

def combinar_csvs(base_dir="./database", prefix="disteffect", n=9, out_name="combined_cooja_means.csv"):
    rows = []
    fieldnames_out = None

    for i in range(1, n + 1):
        distance_m = i * 10
        csv_path = Path(base_dir) / f"{prefix}{i}" / "output" / "cooja_means.csv"

        if not csv_path.exists():
            print(f"[AVISO] Arquivo não encontrado: {csv_path}")
            continue

        with csv_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            try:
                row = next(reader)
            except StopIteration:
                print(f"[AVISO] Arquivo vazio: {csv_path}")
                continue

            if fieldnames_out is None:
                original_fields = reader.fieldnames or []
                fieldnames_out = ["distance_m"] + [c for c in original_fields if c != "node"]

            out_row = {"distance_m": distance_m}
            for k, v in row.items():
                if k == "node":
                    continue
                out_row[k] = v
            rows.append(out_row)

    if not rows:
        raise RuntimeError("Nenhum dado encontrado para combinar.")

    out_path = Path(base_dir) / out_name
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames_out)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Arquivo combinado gerado em: {out_path.resolve()}")
    return rows


def plot_rssi(rows):
    distances = [float(r["distance_m"]) for r in rows]
    rssi_values = [float(r["rssi"]) for r in rows]

    plt.figure(figsize=(7, 5))
    plt.plot(distances, rssi_values, marker="o", linestyle="-", linewidth=2)
    plt.xlabel("Distância (m)")
    plt.ylabel("RSSI (dBm)")
    plt.title("RSSI vs Distância")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    dados = combinar_csvs()
    plot_rssi(dados)
