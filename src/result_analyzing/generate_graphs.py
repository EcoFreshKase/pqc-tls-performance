from pathlib import Path

from matplotlib.ticker import AutoMinorLocator
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

RESULTS_BASE_PATH = Path("./results/raw_data/")
AMT_OF_MEASUREMENTS = 5
RESULT_PROVIDERS_FILE_MAP = {
    "oqs": "Open Quantum Safe",
    "pqs": "pqShield",
    "ossl35": "OpenSSL 3.5"
}

# Fixed provider order to ensure consistent colors across all diagrams
PROVIDER_ORDER = ["Open Quantum Safe", "pqShield", "OpenSSL 3.5"]

KEM_NAME_MAP = {
    "ML-KEM-1024": "mlkem1024",
    "ML-KEM-768": "mlkem768",
    "ML-KEM-512": "mlkem512",
}

def read_data(file_suffix: str) -> pd.DataFrame:
    data = pd.DataFrame()
    for provider in RESULT_PROVIDERS_FILE_MAP.keys():
        for i in range(1, AMT_OF_MEASUREMENTS + 1):
            csv_path = RESULTS_BASE_PATH / f"{provider}_{i}" / file_suffix
            res = pd.read_csv(csv_path)
            res['provider'] = RESULT_PROVIDERS_FILE_MAP[provider]
            data = pd.concat([data, res], ignore_index=True)
    return data

def read_tls_data() -> pd.DataFrame:
    return read_data("results_tls.csv")

def read_kem_alg_perf_data() -> pd.DataFrame:
    return read_data("results_kem_alg.csv")

def read_sig_alg_perf_data() -> pd.DataFrame:
    return read_data("results_sig_alg.csv")

def get_tls_graph(nist_level: int, data: pd.DataFrame, ax):
    data = data[data['nist_level'].astype(int) == int(nist_level)].copy()
    data['label'] = data['KEM'].astype(str) + ' | ' + data['SIG'].astype(str)

    summary = data.groupby(['label', 'provider'], as_index=False)['connections/s'].agg(['mean', 'std']).reset_index()

    # Pivot summary to wide form so we can control bar positions precisely
    pivot = summary.pivot(index='label', columns='provider', values='mean').fillna(0)
    pivot_std  = summary.pivot(index='label', columns='provider', values='std').fillna(0)
    labels = pivot.index.tolist()
    # Use consistent provider ordering, filtering out any missing providers
    providers = [p for p in PROVIDER_ORDER if p in pivot.columns]

    n = len(labels)
    m = len(providers)

    x = np.arange(n)

    # total width occupied by a group of bars (0..1)
    group_total_width = 0.90
    single_width = group_total_width / max(m, 1)
    inner_fill = 0.95  # fraction of single_width that is actual bar (rest is padding)
    bar_width = single_width * inner_fill

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
    ax.set_xlabel('Schlüsselkapselungsverfahren | Signatur Algorithmus')
    ax.set_ylabel('Verbindungen pro Sekunde')
    ax.set_title(f'NIST level {nist_level}')

    # Grid customization (only horizontal lines)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, which='major', linestyle='--', linewidth=0.8, color='0.75')
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.grid(True, which='minor', linestyle=':', linewidth=0.5, color='0.85', alpha=0.7)
    ax.xaxis.grid(False)
    ax.margins(y=0.15)


    # Increase legend text size and title size for readability
    ax.legend(title="Anbieter", fontsize=9, title_fontsize=11, markerscale=1, handlelength=1.5, handletextpad=0.6)

def get_kem_alg_graph(data: pd.DataFrame):
    # normalize KEM names
    data = data.replace({"kem-algorithm": KEM_NAME_MAP})

    # aggregate mean and std per (kem-algorithm, provider)
    summary = data.groupby(['kem-algorithm', 'provider'], as_index=False)[['encaps/s', 'decaps/s']].agg(['mean', 'std']).reset_index()
    summary.columns = ['_'.join(col).strip() if col[1] else col[0] for col in summary.columns.values]
    summary.rename(columns={
        'kem-algorithm_': 'kem-algorithm',
        'provider_': 'provider',
        'encaps/s_mean': 'encaps/s_mean',
        'encaps/s_std': 'encaps/s_std',
        'decaps/s_mean': 'decaps/s_mean',
        'decaps/s_std': 'decaps/s_std',
    }, inplace=True)

    # pivot so rows = kem-algorithm, columns = provider
    pivot_encap = summary.pivot(index='kem-algorithm', columns='provider', values='encaps/s_mean').fillna(0)
    pivot_encap_std = summary.pivot(index='kem-algorithm', columns='provider', values='encaps/s_std').fillna(0)
    pivot_decap = summary.pivot(index='kem-algorithm', columns='provider', values='decaps/s_mean').fillna(0)
    pivot_decap_std = summary.pivot(index='kem-algorithm', columns='provider', values='decaps/s_std').fillna(0)

    kem_labels = pivot_encap.index.tolist()
    # Use consistent provider ordering, filtering out any missing providers
    providers = [p for p in PROVIDER_ORDER if p in pivot_encap.columns]

    n_kem = len(kem_labels)
    n_prov = len(providers)
    x = np.arange(n_kem)

    # sizing: outer groups by KEM, inner groups by provider, two bars (encap+decap) per provider
    group_total_width = 0.9
    prov_group_width = group_total_width / max(n_prov, 1)
    bar_width = prov_group_width * 0.45   # each metric bar
    gap = prov_group_width * 0.025        # gap between encap and decap for same provider

    fig, ax = plt.subplots(figsize=(16, 8))
    palette = sns.color_palette("colorblind", n_colors=n_prov)

    # draw bars: for each provider, plot encap and decap for all KEM algorithms
    for i, provider in enumerate(providers):
        prov_center = x - (group_total_width / 2) + i * prov_group_width + prov_group_width / 2

        encap_vals = pivot_encap[provider].values
        encap_errs = pivot_encap_std[provider].values
        decap_vals = pivot_decap[provider].values
        decap_errs = pivot_decap_std[provider].values

        encap_positions = prov_center - (bar_width / 2 + gap / 2)
        decap_positions = prov_center + (bar_width / 2 + gap / 2)

        # Plot encap bars (solid)
        bars_enc = ax.bar(encap_positions, encap_vals, width=bar_width,
                          color=palette[i], align='center', zorder=3,
                          yerr=encap_errs, error_kw={'elinewidth':4, 'alpha':0.9})
        # Plot decap bars (hatched, same color)
        bars_dec = ax.bar(decap_positions, decap_vals, width=bar_width,
                          color=palette[i], hatch='///', edgecolor="#ffffff", align='center', zorder=3,
                          yerr=decap_errs, error_kw={'elinewidth':4, 'alpha':0.9})

        # label bars
        ax.bar_label(bars_enc, fmt='%.0f', padding=3)
        ax.bar_label(bars_dec, fmt='%.0f', padding=3)

    # xticks at group centers
    ax.set_xticks(x)
    ax.set_xticklabels(kem_labels, rotation=0, ha='center')
    ax.set_xlabel('Schlüsselkapselungsverfahren')
    ax.set_ylabel('Operationen pro Sekunde')
    ax.set_title('Schlüsselkapselungsverfahren-Leistung: Kapselung & Dekapselung nach Anbieter')

    # Provider legend: colored patches + encap/decap explanation
    from matplotlib.patches import Patch
    provider_handles = [Patch(facecolor=palette[i], label=providers[i]) for i in range(len(providers))]
    enc_handle = Patch(facecolor='white', edgecolor='black', label='Kapselung/s')
    dec_handle = Patch(facecolor='white', edgecolor='black', hatch='///', label='Dekapselung/s')
    ax.legend(handles=provider_handles + [enc_handle, dec_handle], title='Anbieter / Metrik',
              fontsize=11, title_fontsize=12, ncol=2)

    # Grid customization (only horizontal lines)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, which='major', linestyle='--', linewidth=0.8, color='0.75')
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.grid(True, which='minor', linestyle=':', linewidth=0.5, color='0.85', alpha=0.7)
    ax.xaxis.grid(False)

def get_sig_alg_graph(data: pd.DataFrame):
    # aggregate mean and std per (sig-algorithm, provider)
    summary = data.groupby(['sig-algorithm', 'provider'], as_index=False)[['signs/s', 'verify/s']].agg(['mean', 'std']).reset_index()
    summary.columns = ['_'.join(col).strip() if col[1] else col[0] for col in summary.columns.values]
    summary.rename(columns={
        'sig-algorithm_': 'sig-algorithm',
        'provider_': 'provider',
        'signs/s_mean': 'signs/s_mean',
        'signs/s_std': 'signs/s_std',
        'verify/s_mean': 'verify/s_mean',
        'verify/s_std': 'verify/s_std',
    }, inplace=True)

    # pivot so rows = sig-algorithm, columns = provider
    pivot_sign = summary.pivot(index='sig-algorithm', columns='provider', values='signs/s_mean').fillna(0)
    pivot_sign_std = summary.pivot(index='sig-algorithm', columns='provider', values='signs/s_std').fillna(0)
    pivot_verify = summary.pivot(index='sig-algorithm', columns='provider', values='verify/s_mean').fillna(0)
    pivot_verify_std = summary.pivot(index='sig-algorithm', columns='provider', values='verify/s_std').fillna(0)

    sig_labels = pivot_sign.index.tolist()
    # Use consistent provider ordering, filtering out any missing providers
    providers = [p for p in PROVIDER_ORDER if p in pivot_sign.columns]

    n_sig = len(sig_labels)
    n_prov = len(providers)
    x = np.arange(n_sig)

    # sizing: outer groups by SIG, inner groups by provider, two bars (encap+decap) per provider
    group_total_width = 0.9
    prov_group_width = group_total_width / max(n_prov, 1)
    bar_width = prov_group_width * 0.45   # each metric bar
    gap = prov_group_width * 0.025        # gap between encap and decap for same provider

    fig, ax = plt.subplots(figsize=(16, 8))
    palette = sns.color_palette("colorblind", n_colors=n_prov)

    # draw bars: for each provider, plot encap and decap for all SIG algorithms
    for i, provider in enumerate(providers):
        prov_center = x - (group_total_width / 2) + i * prov_group_width + prov_group_width / 2

        encap_vals = pivot_sign[provider].values
        encap_errs = pivot_sign_std[provider].values
        decap_vals = pivot_verify[provider].values
        decap_errs = pivot_verify_std[provider].values

        encap_positions = prov_center - (bar_width / 2 + gap / 2)
        decap_positions = prov_center + (bar_width / 2 + gap / 2)

        # Plot encap bars (solid)
        bars_enc = ax.bar(encap_positions, encap_vals, width=bar_width,
                          color=palette[i], align='center', zorder=3,
                          yerr=encap_errs, error_kw={'elinewidth':4, 'alpha':0.9})
        # Plot decap bars (hatched, same color)
        bars_dec = ax.bar(decap_positions, decap_vals, width=bar_width,
                          color=palette[i], hatch='///', edgecolor="#ffffff", align='center', zorder=3,
                          yerr=decap_errs, error_kw={'elinewidth':4, 'alpha':0.9})

        # label bars
        ax.bar_label(bars_enc, fmt='%.0f', padding=3)
        ax.bar_label(bars_dec, fmt='%.0f', padding=3)

    # xticks at group centers
    ax.set_xticks(x)
    ax.set_xticklabels(sig_labels, rotation=0, ha='center')
    ax.set_xlabel('Signatur Algorithmus')
    ax.set_ylabel('Operationen pro Sekunde')
    ax.set_title('Leistung des Signatur Algorithmus: Signaturen/s & Verifikationen/s nach Anbieter')

    # Provider legend: colored patches + encap/decap explanation
    from matplotlib.patches import Patch
    provider_handles = [Patch(facecolor=palette[i], label=providers[i]) for i in range(len(providers))]
    enc_handle = Patch(facecolor='white', edgecolor='black', label='Signaturen/s')
    dec_handle = Patch(facecolor='white', edgecolor='black', hatch='///', label='Verifikationen/s')
    ax.legend(handles=provider_handles + [enc_handle, dec_handle], title='Anbieter / Metrik',
              fontsize=11, title_fontsize=12, ncol=2)

    # Grid customization (only horizontal lines)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, which='major', linestyle='--', linewidth=0.8, color='0.75')
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.grid(True, which='minor', linestyle=':', linewidth=0.5, color='0.85', alpha=0.7)
    ax.xaxis.grid(False)

if __name__ == "__main__":

    # TLS performance graphs for different NIST levels
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 15), constrained_layout=True)
    tls_data = read_tls_data()
    get_tls_graph(1, tls_data, ax1)
    get_tls_graph(3, tls_data, ax2)
    get_tls_graph(5, tls_data, ax3)

    kem_alg_perf_data = read_kem_alg_perf_data()
    get_kem_alg_graph(kem_alg_perf_data)

    sig_alg_perf_data = read_sig_alg_perf_data()
    get_sig_alg_graph(sig_alg_perf_data)
    print(sig_alg_perf_data)

    plt.tight_layout()
    plt.subplots_adjust(hspace=0.7)
    plt.show()
