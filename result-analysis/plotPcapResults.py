import os
import argparse
import matplotlib.pyplot as plt
from pylab import rcParams
import copy
import math

rcParams['pdf.fonttype'] = 42
rcParams['ps.fonttype'] = 42
rcParams.update({'font.size': 32})

stat_prototype = {"intf_name": "", "in/out": "", "#interests": 0, "bytesInterests": 0, "#data": 0, "bytesData": 0,
                  "#Nack": 0, "bytesNack": 0,
                  "#IPSyncPackets": 0,
                  "bytesIPSyncPackets": 0, "#MCPackets": 0,
                  "bytesMCPackets": 0}

CAPTION_REPLACEMENTS = {
    "1x1": "Single Server Setting",
    "2x1": "Two Server Setting",
    "3x1": "Three Server Setting",
    "2x2": "Four Server Setting",
    "3x3": "Nine Server Setting"
}


def readStatistics_files(directory):
    statistics = {}
    # assume this header: intf_name	in/out	#interests	bytesInterests	#data	bytesData	#Nack	bytesNack	#IPSyncPackets	bytesIPSyncPackets	#MCPackets	bytesMCPackets
    for file in os.listdir(directory):
        if file.endswith(".csv"):
            interface_stats = []

            stat_sum = copy.deepcopy(stat_prototype)
            stat_sum["intf_name"] = "all"
            stat_sum["in/out"] = "n.a."  # "out" as we only count outgoing traffic

            with open(os.path.join(directory, file)) as stat_file:
                for line in stat_file.readlines()[1:]:  # skip header line
                    stat = copy.deepcopy(stat_prototype)
                    values = line.split("\t")
                    stat["intf_name"] = values[0]
                    stat["in/out"] = values[1]
                    stat["#interests"] = int(values[2])
                    stat["bytesInterests"] = int(values[3])
                    stat["#data"] = int(values[4])
                    stat["bytesData"] = int(values[5])
                    stat["#Nack"] = int(values[6])
                    stat["bytesNack"] = int(values[7])
                    stat["#IPSyncPackets"] = int(values[8])
                    stat["bytesIPSyncPackets"] = int(values[9])
                    stat["#MCPackets"] = int(values[10])
                    stat["bytesMCPackets"] = int(values[11])

                    # only count outgoing traffic
                    if stat["in/out"] == "in":
                        interface_stats.append(stat)

                        stat_sum["#interests"] += stat["#interests"]
                        stat_sum["bytesInterests"] += stat["bytesInterests"]
                        stat_sum["#Nack"] += stat["#Nack"]
                        stat_sum["bytesNack"] += stat["bytesNack"]

                    elif stat["in/out"] == "out":
                        interface_stats.append(stat)

                        stat_sum["#data"] += stat["#data"]
                        stat_sum["bytesData"] += stat["bytesData"]
                        stat_sum["#IPSyncPackets"] += stat["#IPSyncPackets"]
                        stat_sum["bytesIPSyncPackets"] += stat["bytesIPSyncPackets"]
                        stat_sum["#MCPackets"] += stat["#MCPackets"]
                        stat_sum["bytesMCPackets"] += stat["bytesMCPackets"]

            run_name = file[:-4] if file.endswith(".csv") else file
            statistics[run_name] = stat_sum
    return statistics


def get_stats_by_scenario(statistics):
    result_dict = {}
    # examples for name: 'RESULTS_50_zones_2x2_IP_run_1','RESULTS_1_zones_2x2_NDN_run_1'
    for name in statistics.keys():
        name_parts = name.split("_")
        players = name_parts[1]
        scenario = name_parts[3]
        type = name_parts[4]
        run = name_parts[5] + "_" + name_parts[6]

        # add dict for run if not already existing
        if run not in result_dict:
            result_dict[run] = {}

        run_dict = result_dict[run]
        if scenario not in run_dict:
            run_dict[scenario] = {}

        scenario_dict = run_dict[scenario]
        if players not in scenario_dict:
            scenario_dict[players] = {}

        if type in scenario_dict[players]:
            raise Exception(name + ": stat file for type " + type + " is already present in dict! " + str(result_dict))
        else:
            scenario_dict[players][type] = statistics[name]

    return result_dict


def draw_packets(scenario, ax, title):
    # collect information to be displayed
    player_numbers = sorted(map(int, scenario.keys()))
    player_number_strs = list(map(str, player_numbers))
    num_players = len(player_numbers)

    num_packets_ip = [0] * num_players
    num_packets_ndn_interest = [0] * num_players
    num_packets_ndn_data = [0] * num_players
    num_packets_ndn_sync_interest = [0] * num_players
    num_packets_ndn_sync_data = [0] * num_players
    downscale_factor = 10 ** 3
    max_y = 0

    for i in range(0, num_players):
        stat_data = scenario[player_number_strs[i]]

        for type in stat_data.keys():
            if type == "IP":
                num_packets_ip[i] = int(stat_data[type]["#IPSyncPackets"] / downscale_factor)
                if num_packets_ip[i] > max_y:
                    max_y = num_packets_ip[i]
            elif type == "NDNSync":
                num_packets_ndn_sync_interest[i] = int(stat_data[type]["#interests"] / downscale_factor)
                num_packets_ndn_sync_data[i] = int(stat_data[type]["#data"] / downscale_factor)

                ndn_sum = num_packets_ndn_sync_interest[i] + num_packets_ndn_sync_data[i]
                if ndn_sum > max_y:
                    max_y = ndn_sum
            elif type == "NDN":
                num_packets_ndn_interest[i] = int(stat_data[type]["#interests"] / downscale_factor)
                num_packets_ndn_data[i] = int(stat_data[type]["#data"] / downscale_factor)

                ndn_sum = num_packets_ndn_interest[i] + num_packets_ndn_data[i]
                if ndn_sum > max_y:
                    max_y = ndn_sum
            else:
                raise Exception("unknown type: " + type)

    # draw bars
    bar_width = 0.27
    x_ticks = range(0, num_players)
    # https://matplotlib.org/api/_as_gen/matplotlib.pyplot.bar.html  -> standard alignment for x is "center"
    bar_pos_ip = list(map(lambda x: x - bar_width, x_ticks))
    bar_pos_ndn = list(map(lambda x: x, x_ticks))
    bar_pos_ndn_sync = list(map(lambda x: x + bar_width, x_ticks))

    # draw ip bars
    ax.bar(bar_pos_ip, num_packets_ip, bar_width * 0.96, label="IP Sync Traffic", color="w", edgecolor='black',
           hatch="")

    # draw ndn bars (bars for interest and data stacked on top of each other)
    ax.bar(bar_pos_ndn, num_packets_ndn_data, bar_width * 0.96, label="NDN Data [naive]", color="#dcdcdc",
           edgecolor='black')
    ax.bar(bar_pos_ndn, num_packets_ndn_interest, bar_width * 0.96, bottom=num_packets_ndn_data,
           label="NDN Interests [naive]", color="#dcdcdc", edgecolor='black',
           hatch="//")

    ax.bar(bar_pos_ndn_sync, num_packets_ndn_sync_data, bar_width * 0.96, label="NDN Data [RMA]", color="#808080",
           edgecolor='black')
    ax.bar(bar_pos_ndn_sync, num_packets_ndn_sync_interest, bar_width * 0.96, bottom=num_packets_ndn_sync_data,
           label="NDN Interests [RMA]", color="#808080", edgecolor='black',
           hatch="//")

    ax.set_xlim(x_ticks[0] - bar_width * 2, x_ticks[-1] + bar_width * 2)
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(player_number_strs)
    ax.set_xlabel("Players")
    ax.set_ylabel("Packets [k]")
    # ax.set_title(title, y=-0.55)

    return max_y


def draw_bytes(scenario, ax, title):
    # collect information to be displayed
    player_numbers = sorted(map(int, scenario.keys()))
    player_number_strs = list(map(str, player_numbers))
    num_players = len(player_numbers)

    num_packets_ip = [0] * num_players
    num_packets_ndn_interest = [0] * num_players
    num_packets_ndn_data = [0] * num_players
    num_packets_ndn_sync_interest = [0] * num_players
    num_packets_ndn_sync_data = [0] * num_players
    downscale_factor = 10 ** 6
    max_y = 0

    for i in range(0, num_players):
        stat_data = scenario[player_number_strs[i]]

        for type in stat_data.keys():
            if type == "IP":
                num_packets_ip[i] = int(stat_data[type]["bytesIPSyncPackets"] / downscale_factor)
                if num_packets_ip[i] > max_y:
                    max_y = num_packets_ip[i]
            elif type == "NDNSync":
                num_packets_ndn_sync_interest[i] = int(stat_data[type]["bytesInterests"] / downscale_factor)
                num_packets_ndn_sync_data[i] = int(stat_data[type]["bytesData"] / downscale_factor)

                ndn_sum = num_packets_ndn_sync_interest[i] + num_packets_ndn_sync_data[i]
                if ndn_sum > max_y:
                    max_y = ndn_sum
            elif type == "NDN":
                num_packets_ndn_interest[i] = int(stat_data[type]["bytesInterests"] / downscale_factor)
                num_packets_ndn_data[i] = int(stat_data[type]["bytesData"] / downscale_factor)

                ndn_sum = num_packets_ndn_interest[i] + num_packets_ndn_data[i]
                if ndn_sum > max_y:
                    max_y = ndn_sum
            else:
                raise Exception("unknown type: " + type)

    # draw bars
    bar_width = 0.27
    x_ticks = range(0, num_players)
    # https://matplotlib.org/api/_as_gen/matplotlib.pyplot.bar.html  -> standard alignment for x is "center"
    bar_pos_ip = list(map(lambda x: x - bar_width, x_ticks))
    bar_pos_ndn = list(map(lambda x: x, x_ticks))
    bar_pos_ndn_sync = list(map(lambda x: x + bar_width, x_ticks))

    # draw ip bars
    ax.bar(bar_pos_ip, num_packets_ip, bar_width * 0.96, label="IP Sync Traffic", color="w", edgecolor='black',
           hatch="")

    # draw ndn bars (bars for interest and data stacked on top of each other)
    ax.bar(bar_pos_ndn, num_packets_ndn_data, bar_width * 0.96, label="NDN Data [LLI]", color="#dcdcdc",
           edgecolor='black')
    ax.bar(bar_pos_ndn, num_packets_ndn_interest, bar_width * 0.96, bottom=num_packets_ndn_data,
           label="NDN Interests [LLI]", color="#dcdcdc", edgecolor='black',
           hatch="//")

    ax.bar(bar_pos_ndn_sync, num_packets_ndn_sync_data, bar_width * 0.96, label="NDN Data [Sync]", color="#808080",
           edgecolor='black')
    ax.bar(bar_pos_ndn_sync, num_packets_ndn_sync_interest, bar_width * 0.96, bottom=num_packets_ndn_sync_data,
           label="NDN Interests [Sync]", color="#808080", edgecolor='black',
           hatch="//")

    ax.set_xlim(x_ticks[0] - bar_width * 2, x_ticks[-1] + bar_width * 2)
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(player_number_strs)
    ax.set_xlabel("Players")
    ax.set_ylabel("MB")
    ax.set_title(title, y=-0.56)

    return max_y


def round(step):
    pot = math.floor(math.log10(step))
    return int(math.ceil(step / math.pow(10.0, pot)) * math.pow(10, pot))


def set_y_lim(ax, ylimit):
    #scaled_limit = round(ylimit)
    ax.set_ylim(bottom=0, top=ylimit)
    #step = int(ylimit * 0.2)
    #scaled_step = round(step)
    #ax.set_yticks(range(0, int(scaled_limit + 1), scaled_step))


def draw_all(stats):
    for run in stats.keys():
        scenarios = stats[run]
        fig, axes = plt.subplots(nrows=2, ncols=len(scenarios_to_be_drawn))

        height = 10.5
        fig.set_size_inches(height * len(scenarios_to_be_drawn), height)

        packet_ys = []
        byte_ys = []

        # add subfigures for scenarios
        column = 0
        for scenario_name in scenarios_to_be_drawn:
            if scenario_name in scenarios:
                title = CAPTION_REPLACEMENTS[scenario_name]
                packet_ys.append(draw_packets(scenarios[scenario_name], axes[0, column], title))
                byte_ys.append(draw_bytes(scenarios[scenario_name], axes[1, column], title))
                column += 1

        # set y limits of subplots to be equal
        packet_max = max(packet_ys) * 1.05
        byte_max = max(byte_ys) * 1.05
        for column in range(0, len(scenarios_to_be_drawn)):
            set_y_lim(axes[0, column], packet_max)
            set_y_lim(axes[1, column], byte_max)

        # set legend for whole figure
        handles, labels = axes[0, 0].get_legend_handles_labels()
        fig.legend(handles, labels, loc='lower center', ncol=5, prop={'size': 28}, frameon=False)
        # fig.subplots_adjust(top=0.2)  # add some space/padding on top

        plt.tight_layout()
        output_file_name = os.path.join(output_directory, "trafficStat-run-" + run + ".pdf")
        crop_file_name = os.path.join(output_directory, "trafficStat-run-" + run + "-crop.pdf")
        plt.savefig(output_file_name)
        os.system("pdfcrop --margins '5 5 5 5' " + output_file_name + " " + crop_file_name)
        # plt.show()


def log_to_file(stats, file_path):
    with open(file_path, "w") as output_file:
        output_file.write(
            "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format("run", "scenario", "players", "protocol",
                                                                              "#interests",
                                                                              "bytesInterests", "#data",
                                                                              "bytesData", "#Nack",
                                                                              "bytesNack",
                                                                              "#IPSyncPackets",
                                                                              "bytesIPSyncPackets",
                                                                              "#MCPackets",
                                                                              "bytesMCPackets"))

        for run in stats.keys():
            scenarios = stats[run]

            for scenario_name in scenarios_to_be_drawn:
                if scenario_name in scenarios:
                    scenario = scenarios[scenario_name]
                    player_numbers = sorted(map(int, scenario.keys()))
                    player_number_strs = list(map(str, player_numbers))
                    num_players = len(player_numbers)

                    for i in range(0, num_players):
                        protocol_data = scenario[player_number_strs[i]]
                        for protocol in protocol_data.keys():
                            stat_data = protocol_data[protocol]
                            output_file.write(
                                "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(run, scenario_name,
                                                                                                  player_number_strs[i],
                                                                                                  protocol,
                                                                                                  stat_data[
                                                                                                      "#interests"],
                                                                                                  stat_data[
                                                                                                      "bytesInterests"],
                                                                                                  stat_data["#data"],
                                                                                                  stat_data[
                                                                                                      "bytesData"],
                                                                                                  stat_data["#Nack"],
                                                                                                  stat_data[
                                                                                                      "bytesNack"],
                                                                                                  stat_data[
                                                                                                      "#IPSyncPackets"],
                                                                                                  stat_data[
                                                                                                      "bytesIPSyncPackets"],
                                                                                                  stat_data[
                                                                                                      "#MCPackets"],
                                                                                                  stat_data[
                                                                                                      "bytesMCPackets"]))


# entry point of script
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", help="Input directory containing e.g. 'RESULTS_1_zones_2x1_IP_run_1.csv'",
                    default="./",
                    required=True)
parser.add_argument("-s", "--scenarios", help="List of scenarios to draw, e.g. 2x1,3x1,2x2",
                    default="2x1,3x1,2x2")
parser.add_argument("-o", "--output", help="Output directory [./]", default="./")
args = parser.parse_args()

input_directory = args.input
output_directory = args.output
scenarios_to_be_drawn = args.scenarios.split(",")

# read stats of outgoing traffic from result files
statistics = readStatistics_files(input_directory)

print("gathered information about " + str(len(statistics.keys())) + " experiments")
for id in statistics.keys():
    print(id + "\t" + str(statistics[id]))

# store stats in dict to be plotted easier
rearranged_stats = get_stats_by_scenario(statistics)

# draw figure
draw_all(rearranged_stats)

#log_to_file(rearranged_stats, "plottedData.csv")
