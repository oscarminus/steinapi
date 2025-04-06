#!/usr/bin/python3

import httpx
from pprint import pprint
from steinapi import SteinAPI
from datetime import datetime
import argparse
import json
import logging
import sys

URL = "https://app.divera247.com/api/v2/"

FMSSTEIN = {
    1: 'semiready',
    2: 'ready',
    3: 'inuse',
    4: 'inuse',
    6: 'notready',
    'ready': 2,
    'semiready': 6,
    'notready': 6,
    'inuse': 3,
    'maint': 6
}


def convertToUnixTs(string: str) -> int:
    return int(datetime.fromisoformat(string).strftime('%s'))
    

def setDataDivera(id, data):
    payload = {
        'status': FMSSTEIN[data['status']],
        'status_id': FMSSTEIN[data['status']]
    }
    if 'comment' in data:
        comment_without_linebreaks = data['comment'].replace('\n', ' ')
        payload.update({'status_note': comment_without_linebreaks})

    logging.debug("Payload: %s" % str(payload))

    htclient = httpx.Client(http2=True)
    r = htclient.post(URL + "using-vehicles/set-status/" + str(id) + "?accesskey=" + config['divera']['accesskey'], json=payload)
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog='Divera sync', description="Synchronisiert Divera mit Stein.app")
    parser.add_argument("--config", "-c", default="config.json", help="Pfad zur Konfigdatei.")
    parser.add_argument("--debug", "-d", action='store_true', help="Debug Modus")
    parser.add_argument("--direction", choices=['divera', 'stein', 'both'], default='both', help="In welche Richtung soll synchronisiert werden? both ist default")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    logging.info("Python version: %s" % sys.version)
    logging.info("Lade config file %s" % args.config)
    with open(args.config) as f:
        config = json.load(f)

    logging.info("Lese Daten von Divera")
    htclient = httpx.Client(http2=True)
    r = htclient.get(URL + "pull/vehicle-status?accesskey=" + config['divera']['accesskey'])
    data = r.json()['data']
    assets_divera = {d['number']: d for d in data if d['number'] != ''}
    logging.debug("Assets in Divera: %s" % str(assets_divera))
    logging.info("Divera Daten geladen")

    logging.info("Lese Daten von Stein")
    s = SteinAPI(config['stein']['buname'], config['stein']['apikey'])
    data = s.get_assets()
    assets_stein = {d['name']: d for d in data if d['groupId'] in [1, 5]}
    logging.debug("Assets in Stein: %s" % str(assets_stein))
    logging.info("Stein Daten geladen")

    for k,data_stein in assets_stein.items():
        if k not in assets_divera:
            continue

        data_divera = assets_divera[k]
        # normalize comment to empty string
        if data_stein['comment'] == None:
            data_stein['comment'] = ''
        if data_divera['fmsstatus'] != FMSSTEIN[data_stein['status']] or data_divera['fmsstatus_note'] != data_stein['comment']:

            if args.direction == 'both':
                # in beide Richtungen, je nachdem wer da aktuellere Datum hat
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
                    s.update_asset(data_stein['id'], payload)

            elif args.direction == 'divera':
                # Überschreibe Daten in Divera
                logging.info("Sync nur Divera aktiv")
                logging.info("Überschreibe Daten in Divera: Fahrzeug %s, Status Divera %s, Status Stein %s, Text Divera '%s', Text Stein '%s'" % (data_divera['name'], data_divera['fmsstatus'], data_stein['status'], data_divera['fmsstatus_note'], data_stein['comment']))
                setDataDivera(data_divera['id'], data_stein)
            elif args.direction == 'stein':
                # Überschreibe Daten in Stein
                logging.info("Sync nur Stein aktiv")
                logging.info("Überschreibe Daten in Stein: Fahrzeug %s, Status Divera %s, Status Stein %s, Text Divera '%s', Text Stein '%s'" % (data_divera['name'], data_divera['fmsstatus'], data_stein['status'], data_divera['fmsstatus_note'], data_stein['comment']))
                payload = {
                    'status' : FMSSTEIN[data_divera['fmsstatus']],
                    'comment' : data_divera['fmsstatus_note']
                }
                s.update_asset(data_stein['id'], payload)
        else:
            logging.info("Eintrag unverändert")
