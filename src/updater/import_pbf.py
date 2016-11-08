#!/usr/bin/env python

# Created by: Dave Barrett
# Date: 18/10/2016
# Purpose: Handle the import of pbf file into postgis using imposm3.

import argparse
import urllib
import json
import os
import subprocess
import logging
from datetime import date

def import_pbf(config):
    logging.info("Importing to Postgis using Imposm3.")
    imposm_config_path = config["imposm_config_path"]
    pbf = config["pbf_file"]
    # requires imposm3 to be in the path for your system
    subprocess.call(["imposm3", "import", "--config=%s" % imposm_config_path, "-overwritecache", "-read=%s" % pbf, "-dbschema-import=public", "-write", "-optimize", "-diff"])
    return None

def convert_pbf(config):
    logging.info("Converting %s to o5m format" % config["pbf_file"])
    pbf = config["pbf_file"]
    o5m = config["o5m_file"]
    logging.info(o5m)
    subprocess.call(["osmconvert", pbf, "--out-o5m", "-o=%s" % o5m])
    return None

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
    parser = argparse.ArgumentParser(description="Simple tool for automating the loading of data into Postgis using Imposm3.")
    parser.add_argument("-c", "--config", default="./default.conf.json", help="Path to the config. An example is located in default.conf.json")
    parser.add_argument("-i", "--importpbf", action="store_true", help="Import the pbf file specified in the config file into Postgis")
    parser.add_argument("-C", "--convert", action="store_true", help="Convert the pbf file to o5m format for later use. Requires osmconvert to be installed.")
    args = parser.parse_args()

    with open(args.config, "r") as configfile:
        config = json.load(configfile)

    if args.importpbf:
        import_pbf(config)

    if args.convert:
        convert_pbf(config)
        
