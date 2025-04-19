import os.path as osp
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib.ticker import AutoMinorLocator
import pandas
import seaborn


RAW_DATA_DIR = "../kernel_build-data"
NUMCPU_LIST = [1, 2, 4, 8, 16, 32]
MODE_DICT = {
    "baseline": "Native",
    "kernel_rr": "KRR",
    "whole_system_rr": "VM-RR",
}

PALETTE = {
    "baseline": (0.2980392156862745, 0.4470588235294118, 0.6901960784313725),
    "kernel_rr": (0.3333333333333333, 0.6588235294117647, 0.40784313725490196),
    "whole_system_rr": "salmon",
}

HEIGHT = 2.6
WIDTH = 4

def draw_graph():
    time_df_filepath = osp.join(RAW_DATA_DIR, "kernel_build-kernel_build-time.csv")
    rawdata_df = pandas.read_csv(time_df_filepath)

    timetaken_data_df = pandas.DataFrame({"cores": [], "mode": [], "value": []})
    for mode in MODE_DICT:
        for num_cpu in NUMCPU_LIST:
            trialdata_df = rawdata_df[(rawdata_df["mode"] == mode) & (rawdata_df["cores"] == num_cpu)]
            # get the mean value
            value = trialdata_df["value"].mean() / 60
            row = [num_cpu, mode, value]
            timetaken_data_df.loc[len(timetaken_data_df)] = row

    slowdown_data_df = pandas.DataFrame({"cores": [], "mode": [], "value": []})
    for mode in MODE_DICT:
        if mode == "baseline":
            continue
        for num_cpu in NUMCPU_LIST:
            trialdata_df = rawdata_df[(rawdata_df["mode"] == mode) & (rawdata_df["cores"] == num_cpu)]
            this_mode_time = timetaken_data_df[(timetaken_data_df["mode"] == mode) & (timetaken_data_df["cores"] == num_cpu)]["value"]
            baseline_time = timetaken_data_df[(timetaken_data_df["mode"] == "baseline") & (timetaken_data_df["cores"] == num_cpu)]["value"]
            assert len(this_mode_time) == 1
            assert len(baseline_time) == 1
            this_mode_time = this_mode_time.iloc[0]
            baseline_time = baseline_time.iloc[0]
            #overhead = (this_mode_time - baseline_time) / baseline_time
            overhead = this_mode_time / baseline_time
            row = [num_cpu, mode, overhead]
            slowdown_data_df.loc[len(slowdown_data_df)] = row

    timetaken_data_df['cores'] = timetaken_data_df['cores'].astype(str)
    slowdown_data_df['cores'] = slowdown_data_df['cores'].astype(str)

    _, ax_pair = plt.subplots(2, 1, figsize=(WIDTH, HEIGHT), \
                        gridspec_kw = {'height_ratios':[1.8, 1]}, \
                        sharex=True)
    ax1 = ax_pair[0]
    ax2 = ax_pair[1]

    seaborn.lineplot(x="cores", y="value", \
                    hue="mode", style="mode", \
                    markers=['o', 'X', 'd'], \
                    dashes=False, \
                    linewidth=2, \
                    palette=PALETTE, \
                    data=timetaken_data_df, ax=ax1)
    ax1.set_ylim(bottom=0)
    ax1.set_xticks([str(num_cpu) for num_cpu in NUMCPU_LIST])
    ax1.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax1.yaxis.set_major_locator(MaxNLocator(4))
    ax1.grid(True, color='gray', alpha=0.25)
    ax1.set_ylabel("Time\n(minutes)")

    # draw the barplot to show the overhead
    seaborn.barplot(x="cores", y="value", hue="mode", \
                    palette=PALETTE, \
                    width=0.5, \
                    data=slowdown_data_df, ax=ax2)
    ax2.set_ylabel('Slowdown\n(times)')

    max_height = max([p.get_height() for p in ax2.patches])
    ax2.set_ylim(0, max_height * 1.65)

    for p in ax2.containers[0].patches:
        height = p.get_height()
        label = f'{height:.2f}'
        ax2.text(p.get_x() + p.get_width(), max_height * 1.1, label, ha="center", size=10, color=PALETTE["kernel_rr"])

    for p in ax2.containers[1].patches:
        height = p.get_height()
        label = f'{height:.2f}'
        ax2.text(p.get_x(), max_height * 1.38, label, ha="center", size=10, color=PALETTE["whole_system_rr"])

    ax2.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax2.yaxis.set_major_locator(MaxNLocator(4))
    ax2.get_legend().remove()
    ax2.grid(True, color='gray', alpha=0.25)

    ax1.set_xlabel("")
    ax2.set_xlabel("Num. of Cores")

    handles, labels = ax1.get_legend_handles_labels()
    new_labels = []
    for label in labels:
        new_labels.append(MODE_DICT[label])
    ax1.legend(handles, new_labels, loc='best')

    file = "kernel-compile.pdf"
    print("Graph {} is generated".format(file))

    plt.tight_layout(pad = 0.0)
    plt.subplots_adjust(hspace=0.1)
    plt.savefig(file)


draw_graph()
