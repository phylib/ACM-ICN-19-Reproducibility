#!/bin/bash
cd $ANALYSIS_HOME/results/
wget -O final-results.tar.gz  http://ftp.itec.aau.at/icn/minecraft-ndn/ICN-19/final-results.tar.gz
tar -zxf final-results.tar.gz
