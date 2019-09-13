# Starting a two server MC cluster synchronized with MC3P

In order get everything up and running, a couple of things need to be done:

1. Install the prerequisites
2. Install the customized version of MC
3. Install the MC3P MC Plugin
3. Install the network agent (MC3P-NA)
4. Edit the configuration files
5. Start the cluster

When all components are installed, the customized [MiniNDN repository](https://gitlab.itec.aau.at/minecraft/mini-ndn) can be
used to perform the evaluations.

## Install the prerequisites

### GRPC and Protocoll buffers

```bash
// https://github.com/grpc/grpc/blob/master/BUILDING.md

sudo apt install build-essential autoconf libtool pkg-config libgflags-dev libgtest-dev clang libc++-dev cmake -y

git clone -b v1.19.0 https://github.com/grpc/grpc
cd grpc
git submodule update --init

make
sudo make install

// install protobuf
cd third_party/protobuf/
make
sudo make install
cd ../../..

```

### ZeroMQ

```bash
git clone https://github.com/zeromq/libzmq.git
cd libzmq
git checkout v4.3.1
mkdir build
cd build
cmake ..
make
sudo make install
cp ../..

git clone https://github.com/zeromq/cppzmq.git
cd cppzmq
git checkout bfdc7885b87e0931a561c769b9b1375595cb7abb
mkdir build                                                               
cd build                                                                
cmake ..                                                                
sudo make -j4 install
cd ../..
```

### NDN Components

For installing all required NDN components, the install script from the
MiniNDN repository is very convenient. It is installing some additional
dependencies as well, but they don't disturb.

```bash
mkdir -p NDN
cd NDN
wget https://raw.githubusercontent.com/named-data/mini-ndn/master/install.sh
sudo ./install.sh

cd ndn-cxx/
git fetch --tags
git checkout ndn-cxx-0.6.5
./waf && sudo ./waf install

cd ../NFD/
git fetch --tags
git checkout NFD-0.6.5
./waf && sudo ./waf install

cd ../PSync/
git fetch --tags && git checkout 0.1.0
./waf clean && ./waf && sudo ./waf install
cd ../..
```

### Proxy Application to connect clients

In order to connect clients to the distributed server cluster, we use an proxy
Minecraft proxy, created by [Herman Engelbrecht et al.](https://ieeexplore.ieee.org/abstract/document/6866580/). In order to
download and install it, follow the following instructions.

```bash
git clone https://phylib@bitbucket.org/hebrecht/herobrineproxy.git
git checkout phmoll/v1.12.2/ndn
mvn install
cd ..
```

## Installation of modified Spigot

```bash
// Download and build spigot in versoin 1.12.2
// Requires JDK 8, 11 does __not__ work!
mkdir -p mc && cd mc
mkdir spigot && cd spigot
wget  https://hub.spigotmc.org/jenkins/job/BuildTools/lastSuccessfulBuild/artifact/target/BuildTools.jar
java -jar BuildTools.jar --rev 1.12.2

// Path Spigot
cd Spigot/Spigot-Server/
git remote add aau https://gitlab.itec.aau.at/minecraft/MC3P-Spigot-Server.git
git checkout -b aau-master aau/master
mvn clean install
cd ../../../..
// Modified version of spigot can be found in ~/mc/spigot/Spigot/Spigot-Server/target
```

## Compilation of the MC3P plugin

```bash
sudo apt install openjdk-8-jdk maven
mkdir -p mc && cd mc
git clone https://gitlab.itec.aau.at/minecraft/MC3P.git
cd MC3P
cp ../spigot/Spigot/Spigot-Server/target/spigot-1.12.2-R0.1-SNAPSHOT.jar lib/
mvn clean install
// Compiled plugin in target folder
cd ../..
```

## Compilation of MC3P-NA

```bash
mkdir -p mc && cd mc
git clone https://gitlab.itec.aau.at/minecraft/MC3P-NA.git
cd MC3P-NA/
cmake . && make
cd ../..
```

## Configure MC3P plugin

```bash
cd mc/
mkdir -p server
cp spigot/Spigot/Spigot-Server/target/spigot-1.12.2-R0.1-SNAPSHOT.jar ./server/
cd server/
// Start server and accept eula (java -jar spigot-1.12.2-R0.1-SNAPSHOT.jar)
mkdir -p plugins
cp ../MC3P/target/MC3P.jar ./plugins/
// Start and stop server to generate conifg file for plugins
// Configuration for MC3P plugin can be found `plugins/MC3P/config.yml`
// The config.yml file specifies how the plugin works together with
// the network agent.
```

## Configure MC3P-NA

The network agent basically needs two configuration file. The topology file
describes how the topology of the cluster looks like (which server simulates
which region). The second file, the network agent configuration defines the
settings of a single network agent instance.

## NFD settings

Server 0:
```
sudo nfd-stop
sudo nfd-start
sudo nfdc face create remote udp://192.168.33.11
sudo nfdc route add prefix /server1 nexthop udp://192.168.33.11
sudo nfdc route add prefix /mc/0/5:5/ nexthop udp://192.168.33.11
sudo nfdc route add prefix /mc/0/5:4/ nexthop udp://192.168.33.11
sudo nfdc route add prefix /mc/0/0:5/ nexthop udp://192.168.33.11
sudo nfdc route add prefix /mc/0/1:3/ nexthop udp://192.168.33.11
sudo nfdc route add prefix /mc/0/5:3/ nexthop udp://192.168.33.11
sudo nfdc route add prefix /mc/0/0:3/ nexthop udp://192.168.33.11
sudo nfdc route add prefix /mc/0/1:5/ nexthop udp://192.168.33.11
sudo nfdc route add prefix /mc/0/1:4/ nexthop udp://192.168.33.11
sudo nfdc route add prefix /mc/0/0:4/ nexthop udp://192.168.33.11
sudo nfdc route add prefix /mc/0/2:5/ nexthop udp://192.168.33.11
sudo nfdc route add prefix /mc/0/3:3/ nexthop udp://192.168.33.11
sudo nfdc route add prefix /mc/0/2:3/ nexthop udp://192.168.33.11
sudo nfdc route add prefix /mc/0/3:4/ nexthop udp://192.168.33.11
sudo nfdc route add prefix /mc/0/2:4/ nexthop udp://192.168.33.11
sudo nfdc route add prefix /mc/0/4:5/ nexthop udp://192.168.33.11
sudo nfdc route add prefix /mc/0/3:5/ nexthop udp://192.168.33.11
sudo nfdc route add prefix /mc/0/4:3/ nexthop udp://192.168.33.11
sudo nfdc route add prefix /mc/0/4:4/ nexthop udp://192.168.33.11
```

Server1:
```
sudo nfd-stop
sudo nfd-start
sudo nfdc face create remote udp://192.168.33.10
sudo nfdc route add prefix /server0 nexthop udp://192.168.33.10
sudo nfdc route add prefix /mc/0/6:2/ nexthop udp://192.168.33.10
sudo nfdc route add prefix /mc/0/6:1/ nexthop udp://192.168.33.10
sudo nfdc route add prefix /mc/0/5:2/ nexthop udp://192.168.33.10
sudo nfdc route add prefix /mc/0/5:1/ nexthop udp://192.168.33.10
sudo nfdc route add prefix /mc/0/1:2/ nexthop udp://192.168.33.10
sudo nfdc route add prefix /mc/0/5:0/ nexthop udp://192.168.33.10
sudo nfdc route add prefix /mc/0/1:1/ nexthop udp://192.168.33.10
sudo nfdc route add prefix /mc/0/2:0/ nexthop udp://192.168.33.10
sudo nfdc route add prefix /mc/0/0:0/ nexthop udp://192.168.33.10
sudo nfdc route add prefix /mc/0/3:1/ nexthop udp://192.168.33.10
sudo nfdc route add prefix /mc/0/1:0/ nexthop udp://192.168.33.10
sudo nfdc route add prefix /mc/0/4:0/ nexthop udp://192.168.33.10
sudo nfdc route add prefix /mc/0/0:1/ nexthop udp://192.168.33.10
sudo nfdc route add prefix /mc/0/2:2/ nexthop udp://192.168.33.10
sudo nfdc route add prefix /mc/0/3:0/ nexthop udp://192.168.33.10
sudo nfdc route add prefix /mc/0/0:2/ nexthop udp://192.168.33.10
sudo nfdc route add prefix /mc/0/2:1/ nexthop udp://192.168.33.10
sudo nfdc route add prefix /mc/0/3:2/ nexthop udp://192.168.33.10
sudo nfdc route add prefix /mc/0/4:1/ nexthop udp://192.168.33.10
sudo nfdc route add prefix /mc/0/6:0/ nexthop udp://192.168.33.10
sudo nfdc route add prefix /mc/0/4:2/ nexthop udp://192.168.33.10
```

