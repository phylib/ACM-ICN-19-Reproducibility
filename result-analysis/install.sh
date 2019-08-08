#!/bin/bash
# Install wireshark and NDN dissector
echo "Install wireshark and the ndn dissector"
sudo apt install tshark wireshark
if ! test -f /usr/local/share/ndn-dissect-wireshark/ndn.lua; then
  git clone https://github.com/named-data/ndn-tools.git
  sudo mkdir -p /usr/local/share/ndn-dissect-wireshark/
  sudo cp -v ndn-tools/tools/dissect-wireshark/ndn.lua /usr/local/share/ndn-dissect-wireshark/
  echo "dofile(\"/usr/local/share/ndn-dissect-wireshark/ndn.lua\")" | sudo tee -a /usr/share/wireshark/init.lua > /dev/null
fi

# Install python dependencies
echo "Install python virtualenvironment and all dependencies in the icn-analysis environment"
sudo apt install python3-pip python3-dev python3-setuptools
sudo pip3 install virtualenv
virtualenv icn-analysis
source icn-analysis/bin/activate
pip3 install wheel pandas jupyter pyshark matplotlib scipy numpy
