#!/bin/bash
# Install wireshark and NDN dissector
sudo apt install tshark wireshark
git clone https://github.com/named-data/ndn-tools.git
cd ndn-tools/tools/dissect-wireshark
sudo mkdir /usr/local/share/ndn-dissect-wireshark/
sudo cp -v ndn.lua /usr/local/share/ndn-dissect-wireshark/
echo "dofile(\"/usr/local/share/ndn-dissect-wireshark/ndn.lua\")" | sudo tee -a /usr/share/wireshark/init.lua > /dev/null

# Install python dependencies
sudo pip3 install virtualenv
virtualenv icn-analysis
source icn-analysis/bin/activate
pip install pyshark matplotlib scipy numpy

# Execute analysis
#python3 ~/Coding/Minecraft/mc-server-sync/statistics/trafficAnalysis/parsePCAP.py -i final-results/ -o final-results/
