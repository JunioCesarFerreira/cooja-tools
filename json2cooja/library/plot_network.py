import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle
from dto import SimulationConfig

def _build_network_plot(
    points: list[tuple[float, float]],
    region: tuple[float, float, float, float],
    radius: float,
    interference_radius: float,
    paths: list[list[str]] = None
    ) -> None:
    """
    Plota uma rede de nós com discos de comunicação/interferência e caminhos (paths).
    Agora cada curva (path) recebe um label com o número do node correspondente.
    """
    if interference_radius < radius:
        raise ValueError("interference_radius deve ser maior ou igual a radius")

    fig, ax = plt.subplots(figsize=(10, 8))

    # Configuração do plot
    ax.set_xlim(region[0] + region[0]/10, region[2] + region[2]/10)
    ax.set_ylim(region[1] + region[1]/10, region[3] + region[3]/10)
    ax.set_aspect("equal")
    ax.grid(True, linestyle="--", alpha=0.7)
    ax.set_title(
        f"Net {len(points)} fixed nodes "
        f"(comm radius = {radius}, interf radius = {interference_radius})"
    )

    # Região retangular
    ax.add_patch(
        plt.Rectangle(
            (region[0], region[1]),
            region[2] - region[0],
            region[3] - region[1],
            fill=False,
            linestyle="--",
            edgecolor="red",
            linewidth=1,
        )
    )

    # Arestas de comunicação
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            d = np.hypot(points[i][0] - points[j][0],
                         points[i][1] - points[j][1])
            if d <= radius:
                ax.plot(
                    [points[i][0], points[j][0]],
                    [points[i][1], points[j][1]],
                    color="#EE0A0A",
                    linewidth=1,
                    alpha=0.7,
                )

    # Discos
    for (x, y) in points:
        ax.add_patch(
            Circle(
                (x, y),
                interference_radius,
                facecolor="lightgray",
                edgecolor="gray",
                alpha=0.25,
                linewidth=1.0,
            )
        )
        ax.add_patch(
            Circle(
                (x, y),
                radius,
                facecolor="#4ECDC4",
                edgecolor="green",
                alpha=0.35,
                linewidth=1.0,
            )
        )

    # Nós fixos
    for i, (x, y) in enumerate(points):
        ax.plot(x, y, "o", markersize=8, color="gray")
        ax.text(x, y, str(i + 1), color="black",
                ha="center", va="center", fontsize=8)

    # Caminhos móveis (paths)
    if paths:
        cmap = plt.get_cmap("tab10")
        for path_idx, path in enumerate(paths):
            if not isinstance(path, list) or any(len(part) != 2 for part in path):
                print(f"Atenção: Caminho ignorado por estrutura inválida: {path}")
                continue

            num_parts = len(path)
            ts = np.linspace(0, 1, 100 * num_parts)

            xs_total = []
            ys_total = []

            for part_idx, (x_expr, y_expr) in enumerate(path):
                t_start = part_idx / num_parts
                t_end = (part_idx + 1) / num_parts

                ts_segment = ts[(ts >= t_start) & (ts <= t_end)]
                t_local = (ts_segment - t_start) / (t_end - t_start)

                try:
                    x_eval = eval(x_expr, {"np": np, "t": t_local})
                    y_eval = eval(y_expr, {"np": np, "t": t_local})

                    if np.isscalar(x_eval):
                        x_vals = np.full_like(t_local, x_eval, dtype=float)
                    else:
                        x_vals = np.array(x_eval, dtype=float)

                    if np.isscalar(y_eval):
                        y_vals = np.full_like(t_local, y_eval, dtype=float)
                    else:
                        y_vals = np.array(y_eval, dtype=float)

                except Exception as e:
                    print(f"Erro ao avaliar parte {part_idx} do caminho {path_idx}: {e}")
                    continue

                xs_total.extend(x_vals)
                ys_total.extend(y_vals)

            color = cmap(path_idx % 10)
            nodeNumber = path_idx + len(points) + 1
            label = f"Node {nodeNumber}"
            ax.plot(xs_total, ys_total, linestyle='--', color=color, alpha=0.8, label=label)

            # Adiciona texto próximo ao final da trajetória
            if len(xs_total) > 0 and len(ys_total) > 0:
                ax.text(xs_total[-1], ys_total[-1], f"{nodeNumber}",
                        fontsize=9, color=color, weight="bold",
                        ha="left", va="center")

        ax.legend(loc="upper right", fontsize="small", title="Mobile Nodes")

def plot_network(
    file_path: str,
    sim_model: SimulationConfig
    ) -> None:

    fixed_motes = sim_model["simulationElements"]["fixedMotes"]
    mobile_motes = sim_model["simulationElements"]["mobileMotes"]

    points = [tuple(mote["position"]) for mote in fixed_motes]
    region = tuple(sim_model["region"])
    radius = sim_model["radiusOfReach"]
    interference_radius = sim_model["radiusOfInter"]
    paths = [list[str](mote["functionPath"]) for mote in mobile_motes]

    _build_network_plot(points, region, radius, interference_radius, paths)
    plt.savefig(file_path)
