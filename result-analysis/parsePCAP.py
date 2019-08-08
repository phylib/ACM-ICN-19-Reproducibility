import pyshark
import os
import argparse
import time
import copy
import json
import multiprocessing
from multiprocessing import Pool

IP_SERVER_SYNC_PORT = "5555"
MC_SERVER_PORT = "25565"
PYSHARK_DEBUG = True

proc_pool_args = []


# needs python3-packet pyshark (& installed tshark/wireshark)

# NDN packet dissector:
# git clone https://github.com/named-data/ndn-tools.git
# cd ndn-tools/tools/dissect-wireshark
# sudo cp -v ndn.lua /usr/local/share/ndn-dissect-wireshark/
# sudo vim /usr/share/wireshark/init.lua (append the following two lines to the end of the file)
# --dofile("/full/path/to/ndn.lua")
# dofile("/usr/local/share/ndn-dissect-wireshark/ndn.lua")

# https://stackoverflow.com/questions/800197/how-to-get-all-of-the-immediate-subdirectories-in-python
def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]


def append_stat_dict_to_file(stat_dict, output_file_path):
    with open(output_file_path, "a") as output_file:
        output_file.write(
            "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t\n".format(stat_dict["intf_name"],
                                                                                stat_dict["in/out"],
                                                                                stat_dict["#interests"],
                                                                                stat_dict["bytesInterests"],
                                                                                stat_dict["#data"],
                                                                                stat_dict["bytesData"],
                                                                                stat_dict["#Nack"],
                                                                                stat_dict["bytesNack"],
                                                                                stat_dict["#IPSyncPackets"],
                                                                                stat_dict["bytesIPSyncPackets"],
                                                                                stat_dict["#MCPackets"],
                                                                                stat_dict["bytesMCPackets"],
                                                                                stat_dict["bytesSyncPayload"],
                                                                                stat_dict["bytesMCPayload"]))


def get_parent_dir(directory):
    return os.path.dirname(directory)


def get_own_ip_by_host_name(path):
    own_name = os.path.basename(path).split("-")[0]
    mc3pna_dir = get_parent_dir(get_parent_dir(path))
    mc3pna_dir = os.path.join(mc3pna_dir, "mc3p-na")

    for file in os.listdir(mc3pna_dir):
        if file.endswith(".json"):
            with open(os.path.join(mc3pna_dir, file)) as json_file:
                json_data = json.load(json_file)
                for world in json_data["zone_information"]:
                    for zone in world['zone']:
                        if zone["master_name"] == own_name:
                            return zone["master_ip_port"].split(":")[0]

    raise Exception("IP not found for " + path)


def parse_pcap(path_and_output_file_path):
    # unpack tuple and call function
    parse_pcap_file(path_and_output_file_path[0], path_and_output_file_path[1])


def parse_pcap_file(path, output_file_path):
    start = time.time()
    print(path + ": started processing")
    # shoddy solution to finding endpoint ip (as endpoints/hosts have MC server running at port 25565)
    own_ip = get_own_ip_by_host_name(path)
    print(path + ": found own ip: " + own_ip)
    intf_name = os.path.basename(path).replace(".pcap", "")

    stat_in = {"intf_name": intf_name, "in/out": "in", "#interests": 0, "bytesInterests": 0, "#data": 0, "bytesData": 0,
               "#Nack": 0, "bytesNack": 0,
               "#IPSyncPackets": 0,
               "bytesIPSyncPackets": 0, "#MCPackets": 0,
               "bytesMCPackets": 0, "bytesSyncPayload": 0, "bytesMCPayload": 0}

    stat_out = copy.deepcopy(stat_in)
    stat_out["in/out"] = "out"

    cap = pyshark.FileCapture(path, only_summaries=False)
    cap.set_debug(PYSHARK_DEBUG)

    for packet in cap:
        if not hasattr(packet, "udp") and not hasattr(packet, "tcp"):  # skip certain packets (ARP, ICMP)
            continue

        # determine if incoming/outgoing
        stat = stat_in  # incoming data by default
        if packet.ip.src == own_ip:  # outgoing if src is own_ip
            stat = stat_out
        elif (packet.ip.dst != own_ip):
            raise Exception(
                "unsolicited packet: " + str(packet))  # should not happen if only captured one interface (= one IP)

        # get packet infos
        if hasattr(packet, "ndn"):
            ndn_packet_type = packet.ndn._ws_lua_text.split(',')[0]
            if ndn_packet_type == "Interest":
                stat["#interests"] += 1
                stat["bytesInterests"] += int(packet.length)
            elif ndn_packet_type == "Data":
                stat["#data"] += 1
                stat["bytesData"] += int(packet.length)

                # just take binary length of content as upper estimation of transported data (usually just two bytes above the actual size [TYPE, LENGTH])
                # parsing the TLV is too error prone / to much work
                # correctness hinges on correctness of Wireshark NDN dissector (ndn.lua, https://github.com/named-data/ndn-tools/tree/master/tools/dissect-wireshark )
                # https://named-data.net/doc/NDN-packet-spec/current/tlv.html#variable-size-encoding-for-type-t-and-length-l
                # https://named-data.net/doc/NDN-packet-spec/current/data.html
                read_len = len(packet.ndn.content.binary_value)
                stat["bytesSyncPayload"] += read_len
            elif ndn_packet_type == "Nack":
                stat["#Nack"] += 1
                stat["bytesNack"] += int(packet.length)
            else:
                print(path + ": unhandled NDN packet type: " + ndn_packet_type)
        elif hasattr(packet, "tcp"):
            ports = [packet.tcp.srcport, packet.tcp.dstport]

            # Segmentation-independent TCP payload. payload_bytes == 67 corresponds to the "Len:" in wireshark line:
            # Transmission Control Protocol, Src Port: 25565, Dst Port: 55782, Seq: 4488, Ack: 27, Len: 67
            # payload_bytes == 0 e.g. in case of "ACK"-only
            payload_bytes = int(packet.tcp.payload.size) if hasattr(packet.tcp, "payload") else 0

            if IP_SERVER_SYNC_PORT in ports:
                stat["#IPSyncPackets"] += 1
                stat["bytesIPSyncPackets"] += int(packet.length)
                stat["bytesSyncPayload"] += payload_bytes
            elif MC_SERVER_PORT in ports:
                stat["#MCPackets"] += 1
                stat["bytesMCPackets"] += int(packet.length)
                stat["bytesMCPayload"] += payload_bytes
            else:
                print(path + ": unrecognized TCP ports: " + str(ports))
        else:
            print(path + ": dissector detected no 'ndn' or 'tcp', packet layers: " + str(packet.layers))

    cap.close()

    end = time.time()
    print(path + ": finished in {} seconds".format(end - start))
    # write results to log file
    append_stat_dict_to_file(stat_in, output_file_path)
    append_stat_dict_to_file(stat_out, output_file_path)


def parse_directory(directory, fullPath):
    # write header to output file (overwrite existing)
    output_file_path = os.path.join(output_dir, directory + ".csv")
    with open(output_file_path, "w") as output_file:
        output_file.write(
            "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t\n".format("intf_name", "in/out", "#interests",
                                                                                "bytesInterests", "#data",
                                                                                "bytesData", "#Nack", "bytesNack",
                                                                                "#IPSyncPackets",
                                                                                "bytesIPSyncPackets", "#MCPackets",
                                                                                "bytesMCPackets", "bytesSyncPayload",
                                                                                "bytesMCPayload"))
    print("Parsing NDN-run: " + fullPath)
    host_path = os.path.join(fullPath, "link-state/faces-3")

    for subfolder in get_immediate_subdirectories(host_path):
        if subfolder.startswith("h"):
            pcap_dir = os.path.join(host_path, subfolder, "results")

            for file in os.listdir(pcap_dir):
                if file.endswith(".pcap"):
                    proc_pool_args.append((os.path.join(pcap_dir, file), output_file_path))


# entry point of script
num_cpus = multiprocessing.cpu_count()
used_cpus = max(1, int(num_cpus / 2))  # leave room for one tshark-process for every concurrently processed pcap-file

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", help="Input directory containing the result dirs of the runs",
                    default="./",
                    required=True)
parser.add_argument("-o", "--output", help="Output directory [./]", default="./")
parser.add_argument("-p", "--processes", help="Size of process pool [" + str(used_cpus) + "]", type=int,
                    default=used_cpus)
args = parser.parse_args()

input = args.input
output_dir = os.path.abspath(args.output)
used_cpus = args.processes
print("detected " + str(num_cpus) + " cpu(s), using " + str(used_cpus) + " cpu(s)")

p = Pool(args.processes)

# find pcap files that have to be processed, create output/log files for runs in output dir
for subfolder in get_immediate_subdirectories(input):
    if "_NDN_run_" in subfolder or "_IP_run_" in subfolder or "_NDNSync_run_" in subfolder:
        parse_directory(subfolder, os.path.join(input, subfolder))
    else:
        print("skipping directory: " + os.path.join(input, subfolder))

# concurrently process as many pcap files as possible
p.map(parse_pcap, proc_pool_args)
