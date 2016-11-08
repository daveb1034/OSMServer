#!/usr/bin/env python

## This is a modified version of the differ_cron.py script available at
## https://github.com/lyrk/imposm3-differ
## It has been adatped to handle running a full import as well as other tasks
## that utilise osmctools

import argparse
import urllib
import json
import os
import subprocess
import logging
from datetime import date


def _get_current_diff_id():
    timedelta = date.today() - date(2012, 9, 12)
    current_id = timedelta.days
    return current_id


def download_diff(diff_id, config):
    base_url = "http://planet.osm.org/replication/day/{AAA}/{BBB}/{CCC}.{suffix}"
    (AAA, BBB, CCC) = map(''.join, zip(*[iter('{0:09d}'.format(diff_id))]*3))
    url_state = base_url.format(AAA=AAA, BBB=BBB, CCC=CCC, suffix="state.txt")
    url_osc = base_url.format(AAA=AAA, BBB=BBB, CCC=CCC, suffix="osc.gz")
    
    state_download_path = os.path.join(config["download_path"], "%s.state.txt" % diff_id)
    diff_download_path = os.path.join(config["download_path"], "%s.osc.gz" % diff_id)

    logging.info("Downloading diff file (id %s)" % diff_id)
    statefile = urllib.urlopen(url_state)
    with open(state_download_path, "wb") as f:
            f.write(statefile.read())
    statefile.close()

    difffile = urllib.urlopen(url_osc)
    with open(diff_download_path, "wb") as f:
            f.write(difffile.read())
    difffile.close()

    return diff_download_path, state_download_path


def import_diff(diff_path, state_download_path, config):
    """Imports diff file using imposm3
    """
    logging.info("Importing with imposm")
    imposm_config_path = config["imposm_config_path"]
    subprocess.call(["imposm3", "diff", "--config=%s" % imposm_config_path, diff_path])


def update_o5m(diff_path, state_download_path, config):
    """Updates the o5m file with a daily update
    """
    o5m = config["o5m_file"]
    old_o5m = os.path.join(os.path.dirname(o5m),"planet-old.o5m")
    os.rename(o5m,old_o5m)
    logging.info("Applying diff to planet-old.o5m")
    subprocess.call(["osmconvert", old_o5m, diff_path, "--out-o5m", "-o=%s" % o5m])
    logging.info("File updated, removing old file")
    os.remove(old_o5m)
    return None
    
def filter_highways(config):
    """Filters routing related information from planet-new.o5m
    This is not yet working due to the construction of the query.
    """
    o5m = config["o5m_file"]
    highways = os.path.join(os.path.dirname(o5m),"planet-highways.o5m")
    params = config["osmfilter_parameters"]
    logging.info("Applying filter to file: %s" % o5m)
    subprocess.call(["osmfilter", o5m, "--parameter-file=%s" % params,"-o=%s" % highways])
    logging.info("Filtered routing information")


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

    parser = argparse.ArgumentParser(description="Simple tool for downloading and processing OSM diffs for imposm 3.")
    parser.add_argument("-c", "--config", default="./default.conf.json", help="Path to the config. An example is located in default.conf.json")
    parser.add_argument("-d", "--diffnumber", type=int, help="If you don't want to download the newest diff, specify the diff number here.")
    parser.add_argument("-u", "--updateo5m", action="store_true", help="Update o5m file with the diff file")
    parser.add_argument("-f", "--filterhighways", action="store_true", help="FIlter the updated o5m file to extract routing related features.")
    args = parser.parse_args()

    with open(args.config, "r") as configfile:
            config = json.load(configfile)

    if args.diffnumber == None:
            diff_path, state_download_path = download_diff(_get_current_diff_id(), config)
    else:
            diff_path, state_download_path = download_diff(args.diffnumber, config)

    #import the diff file to Postgis by default
    import_diff(diff_path, state_download_path, config)

    # if the -u option is specified update the local .o5m file as well
    if args.updateo5m:
        update_o5m(diff_path, state_download_path, config)

    # if the -f option is specified filter routing information from planet-new.o5m
    if args.filterhighways:
       filter_highways(config)

    
    logging.info("Cleaning up")
    if os.path.exists(diff_path):
        os.remove(diff_path)
    if os.path.exists(state_download_path):
        os.remove(state_download_path)
    
