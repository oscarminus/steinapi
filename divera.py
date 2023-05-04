#!/usr/bin/python3

import requests
from pprint import pprint
import steinapi
from datetime import datetime
import argparse
import json

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
    if data['comment']:
        payload.update({'fmsstatus_note' : data['comment']})

    r = requests.post(URL + "using-vehicles/set-status/" + str(id) + "?accesskey=" + config['divera']['accesskey'], json=payload)
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":

    # Read options and configuration
    parser = argparse.ArgumentParser(prog='Divera sync', description="Synchronisiert Divera mit Stein.app")
    parser.add_argument("--config", "-c", default="config.json", help="Pfad zur Konfigdatei.")
    args = parser.parse_args()

    config = dict()
    with open(args.config) as f:
        config = json.load(f)

    # get data from Divera
    r = requests.get(URL + "pull/vehicle-status?accesskey=" + config['divera']['accesskey'])
    data = r.json()['data']
    assets_divera = dict()
    for d in data:
        if d['number'] != '':
            assets_divera.update({d['number'] : d})
    
    # get data from stein
    s = steinapi.SteinAPI(config['stein']['buname'])
    s.connect(config['stein']['user'], config['stein']['password'])
    data = s.getAssets()
    assets_stein = dict()
    for d in data:
        if d['groupId'] in [1, 5]:
            assets_stein.update({d['name'] : d})

    for k,data_stein in assets_stein.items():
        if k not in assets_divera:
            continue

        data_divera = assets_divera[k]
        if data_divera['fmsstatus'] != FMSSTEIN[data_stein['status']]:
            print("Unterschied: Fahrzeug %s, Status Divera %s, Status Stein %s" % (data_divera['name'], data_divera['fmsstatus'], data_stein['status']))
            if convertToUnixTs(data_stein['lastModified']) > data_divera['fmsstatus_ts']:
                # Stein ist das aktuellere Datum
                setDataDivera(data_divera['id'], data_stein)
            else:
                payload = {
                    'status' : FMSSTEIN[data_divera['fmsstatus']],
                    'comment' : data_divera['fmsstatus_note']
                }
                s.updateAsset(data_stein['id'], payload)
