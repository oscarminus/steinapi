#!/usr/bin/python3

import httpx
from pprint import pprint
import steinapi
from datetime import datetime
import argparse
import json
import logging
import sys

URL = "https://app.divera247.com/api/v2/"

FMSSTEIN = {
    1 : 'semiready',
    2 : 'ready',
    3 : 'inuse',
    4 : 'inuse',
    6 : 'notready',
    'ready' : 2,
    'semiready' : 1,
    'notready' : 6,
    'inuse' : 3,
    'maint' : 6
}

def convertToUnixTs(string : str) -> int:
    # 2022-10-21T10:22:01+02:00
    string = string.split('+')[0]
    dt = datetime.strptime(string, '%Y-%m-%dT%H:%M:%S')
    return int(dt.strftime('%s'))


def setDataDivera(id, data):
    payload = {
        'status' : FMSSTEIN[data['status']],
        'status_id' : FMSSTEIN[data['status']]
    }
    if 'comment' in data:
        comment_without_linebreaks = data['comment'].replace('\n', ' ')  # Replace line breaks with spaces
        payload.update({'status_note' : comment_without_linebreaks})
    
    logging.debug("Payload: %s" % str(payload))

    htclient = httpx.Client(http2=True)
    r = htclient.post(URL + "using-vehicles/set-status/" + str(id) + "?accesskey=" + config['divera']['accesskey'], json=payload)
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":

    # Read options and configuration
    parser = argparse.ArgumentParser(prog='Divera sync', description="Synchronisiert Divera mit Stein.app")
    parser.add_argument("--config", "-c", default="config.json", help="Pfad zur Konfigdatei.")
    parser.add_argument("--debug", "-d", action='store_true')
    args = parser.parse_args()

    # set up logging
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    logging.debug("Python version: %s" % sys.version)
    logging.debug("Lade config file %s" % args.config)
    config = dict()
    with open(args.config) as f:
        config = json.load(f)

    # get data from Divera
    logging.debug("Lese Daten von Divera")
    htclient = httpx.Client(http2=True)
    r = htclient.get(URL + "pull/vehicle-status?accesskey=" + config['divera']['accesskey'])
    data = r.json()['data']
    assets_divera = dict()
    for d in data:
        if d['number'] != '':
            assets_divera.update({d['number'] : d})
    logging.debug("Assets in Divera: %s" % str(assets_divera))

    # get data from stein
    logging.debug("Lese Daten von Stein")
    s = steinapi.SteinAPI(config['stein']['buname'])
    s.connect(config['stein']['user'], config['stein']['password'])
    data = s.getAssets()
    assets_stein = dict()
    for d in data:
        if d['groupId'] in [1, 5]:
            assets_stein.update({d['name'] : d})
    logging.debug("Assets in Stein: %s" % str(assets_stein))

    for k,data_stein in assets_stein.items():
        if k not in assets_divera:
            continue

        data_divera = assets_divera[k]
        # normalize comment to empty string
        if data_stein['comment'] == None:
            data_stein['comment'] = ''
        if data_divera['fmsstatus'] != FMSSTEIN[data_stein['status']] or data_divera['fmsstatus_note'] != data_stein['comment']:
            
            if convertToUnixTs(data_stein['lastModified']) > data_divera['fmsstatus_ts']:
                # Stein ist das aktuellere Datum
                logging.info("Neue Daten in Stein: Fahrzeug %s, Status Divera %s, Status Stein %s, Text Divera '%s', Text Stein '%s'" % (data_divera['name'], data_divera['fmsstatus'], data_stein['status'], data_divera['fmsstatus_note'], data_stein['comment']))
                setDataDivera(data_divera['id'], data_stein)
            else:
                logging.info("Neue Daten in Divera: Fahrzeug %s, Status Divera %s, Status Stein %s, Text Divera '%s', Text Stein '%s'" % (data_divera['name'], data_divera['fmsstatus'], data_stein['status'], data_divera['fmsstatus_note'], data_stein['comment']))
                payload = {
                    'status' : FMSSTEIN[data_divera['fmsstatus']],
                    'comment' : data_divera['fmsstatus_note']
                }
                s.updateAsset(data_stein['id'], payload)
