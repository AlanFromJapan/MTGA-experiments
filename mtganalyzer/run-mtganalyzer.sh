#!/bin/bash

cd ~/Git/MTGA-experiments/mtganalyzer

#will start in parallel, but normally by the time the website is opened the service has been launched
xdg-open http://localhost:45678/

python3 main.py ../MTGA_Logs/ 
