import os
import argparse
import csv
import matplotlib.pyplot as plt
from pylab import rcParams

rcParams['pdf.fonttype'] = 42
rcParams['ps.fonttype'] = 42
rcParams.update({'font.size': 44})

BLOCKS_PER_CHUNK = 16
BLOCKS_PER_PLAYER_LOG_LENGTH_UNIT = 150

CAPTION_REPLACEMENTS = {
    "1x1": "Single Server Setting",
    "2x1": "Two Server Setting",
    "3x1": "Three Server Setting",
    "2x2": "Four Server Setting",
    "3x3": "Nine Server Setting"
}


def readPlayerFiles(directory):
    player_movement_info = {}
    for file in os.listdir(directory):
        if file.startswith("player_") and file.endswith("_movement.csv"):
            id = file.split("_")[1]
            movement = {"x": [], "z": []}

            with open(os.path.join(directory, file), 'rt') as csvfile:
                reader = csv.reader(csvfile, delimiter="\t")
                for row in reader:
                    movement["x"].append(float(row[1].strip()) * BLOCKS_PER_PLAYER_LOG_LENGTH_UNIT / BLOCKS_PER_CHUNK)
                    movement["z"].append(float(row[2].strip()) * BLOCKS_PER_PLAYER_LOG_LENGTH_UNIT / BLOCKS_PER_CHUNK)
            player_movement_info[id] = movement
    return player_movement_info


def readSelectedPlayerFiles(directory, player_ids):
    player_movement_info = readPlayerFiles(directory)
    result_dict = {}

    # filter player info
    for id in player_movement_info.keys():
        player_id = int(id)
        if player_id in player_ids:
            result_dict[id] = player_movement_info[id]

    return result_dict


def draw(ax, player_movement_info):
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)

    for id in player_movement_info:
        movement = player_movement_info[id]
        ax.plot(movement['x'], movement['z'], 'b', label=id, color='#0e0eff', linewidth=1)

    ax.set_xticks(range(0, height + 1, 16))
    ax.set_yticks(range(0, width + 1, 16))
    ax.set_xlabel("X Coordinates")
    ax.set_ylabel("Z Coordinates")


def add_zone_borders(ax, zoning_variant):
    parts = zoning_variant.split("x")
    rows = int(parts[0])
    cols = int(parts[1])

    for z in range(0, height, int(height / rows))[1:]:
        ax.axhline(z, color="r", lw=4, ls="--")

    for x in range(0, width, int(width / cols))[1:]:
        ax.axvline(x, color="r", lw=4, ls="--")

    #ax.set_title(zoning_variant)
    ax.set_title(CAPTION_REPLACEMENTS[zoning_variant], y=-0.28)


def add_macro_chunk_borders(ax):
    for z in range(0, height, 16)[1:]:
        ax.axhline(z, color="#bbbbbb", linewidth=1.75)

    for x in range(0, width, 16)[1:]:
        ax.axvline(x, color="#bbbbbb", linewidth=1.75)


def drawAll(player_movement_info):
    num_subplots = len(zoning_variants)
    fig, axes = plt.subplots(nrows=1, ncols=num_subplots)

    height = 10.5
    fig.set_size_inches(height * 4, height + 1.3)

    for i in range(0, num_subplots):
        draw(axes[i], player_movement_info)
        if draw_macrochunks:
            add_macro_chunk_borders(axes[i])
        add_zone_borders(axes[i], zoning_variants[i])
    plt.tight_layout()
    plt.savefig(os.path.join(output, "playerMovement.pdf"))
    os.system("pdfcrop --margins '5 5 5 5' playerMovement.pdf playerMovement-crop.pdf")
    # plt.show()


# entry point of script
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", help="Input directory containing e.g. player_00_movement.csv", default="./",
                    required=True)
parser.add_argument("-z", "--zoning", help="List of partitioning schemes, e.g. 1x1,2x1,2x2,3x3",
                    default="1x1,2x1,3x1,2x2")
parser.add_argument("-w", "--width", help="Width in chunks", type=int, default=96)
parser.add_argument("-l", "--height", help="Height in chunks", type=int, default=96)
parser.add_argument("-m", "--macro", help="Draw macro chunk borders", type=bool, default=True)
parser.add_argument("-o", "--output", help="Output directory [./]", default="./")
args = parser.parse_args()

width = args.width
height = args.height
zoning_variants = args.zoning.split(",")
input = args.input
output = args.output
draw_macrochunks = args.macro

#player_movement_info = readPlayerFiles(input)
player_movement_info = readSelectedPlayerFiles(input, range(0,20))

print("read " + str(len(player_movement_info)) + " player movement traces")
for id in player_movement_info.keys():
    print(id + "\t" + str(player_movement_info[id]))

drawAll(player_movement_info)
