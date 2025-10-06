from pathlib import Path

from matplotlib.ticker import AutoMinorLocator
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

RESULTS_BASE_PATH = Path("./results/")
AMT_OF_MEASUREMENTS = 5
RESULT_PROVIDERS = ("oqs", "ossl35", "pqs")

def read_tls_data() -> pd.DataFrame:
    data = pd.DataFrame()
    for provider in RESULT_PROVIDERS:
        for i in range(1, AMT_OF_MEASUREMENTS + 1):
            csv_path = RESULTS_BASE_PATH / f"{provider}_{i}" / f"results_tls.csv"
            res = pd.read_csv(csv_path)
            res['provider'] = provider
            data = pd.concat([data, res], ignore_index=True)
    return data

def get_nist_graph(nist_level: int, data: pd.DataFrame):
    data = data[data['nist_level'].astype(int) == int(nist_level)].copy()
    data['label'] = data['KEM'].astype(str) + ' | ' + data['SIG'].astype(str)

    summary = data.groupby(['label', 'provider'], as_index=False)['connections/s'].agg(['mean', 'std']).reset_index()

    # Pivot summary to wide form so we can control bar positions precisely
    pivot = summary.pivot(index='label', columns='provider', values='mean').fillna(0)
    pivot_std  = summary.pivot(index='label', columns='provider', values='std').fillna(0)
    labels = pivot.index.tolist()
    providers = pivot.columns.tolist()

    n = len(labels)
    m = len(providers)

    x = np.arange(n)

    # total width occupied by a group of bars (0..1)
    group_total_width = 0.90
    single_width = group_total_width / max(m, 1)
    inner_fill = 0.95  # fraction of single_width that is actual bar (rest is padding)
    bar_width = single_width * inner_fill

    fig, ax = plt.subplots(figsize=(14, 8))
    palette = sns.color_palette("colorblind", n_colors=len(providers))
    # plot each provider's bars with offsets so bars within the same label are side-by-side
    for i, provider in enumerate(providers):
        offsets = x - (group_total_width / 2) + i * single_width + single_width / 2
        values = pivot[provider].values
        errs  = pivot_std[provider].values
        bars =  ax.bar(
            offsets, 
            values, 
            width=bar_width, 
            label=provider, 
            align='center', 
            zorder=3,
            color=palette[i],
            yerr=errs, 
            error_kw={'elinewidth':4, 'alpha':0.9},
        )
        ax.bar_label(bars, fmt='%.1f', padding=3)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=0, ha='center')
    ax.set_xlabel('KEM | SIG')
    ax.set_ylabel('Connections per second')
    ax.set_title(f'NIST level {nist_level} — connections/s by KEM|SIG')

    # Grid customization (only horizontal lines)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, which='major', linestyle='--', linewidth=0.8, color='0.75')
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.grid(True, which='minor', linestyle=':', linewidth=0.5, color='0.85', alpha=0.7)
    ax.xaxis.grid(False)


    # Increase legend text size and title size for readability
    ax.legend(title="Provider", fontsize=12, title_fontsize=13, markerscale=1.2, handlelength=2, handletextpad=0.8)


if __name__ == "__main__":
    # Sample data
    
    tls_data = read_tls_data()

    get_nist_graph(1, tls_data)
    get_nist_graph(3, tls_data)
    get_nist_graph(5, tls_data)


    plt.tight_layout()
    plt.show()
