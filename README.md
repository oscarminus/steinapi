# steinapi
Ziel des Projekt ist die synchronisierung zwischen Stein.APP und Divera 24/7.

## Systemumgebug
Der Code wurde auf Debian Linux 12 (Bookworm) und macOS getestet. Zusätzlich zur Standard-Python-Installation wird das httpx-Paket mit HTTP/2 support genutzt. 

### Installation unter Debian
```shell
apt install python3-httpx python3-h2
```

### Installation auf macOS
Ausgangslage: Python3 per Homebrew installiert
```shell
python3 -m venv .venv
source .venv/bin/activate
pip3 install "httpx[http2]"
```

## Einrichtung
1. Voarb: Zunächst werden je ein Nutzer in Stein.APP und Divera 24/7 benötigt.
    1. Divera 24/7: Im Menüpunkt Verwaltung -> Schnittstellen -> System-Benutzer muss ein neuer System-Benutzer angelegt werden. Der dabei generierte Accesskey wird gleich benötigt.
    1. Stein.APP: Es wird ein "techuser" benötigt. Also einen neuen Nutzer mit dem Häckchen "Für Nutzung über API".
1. Damit die Fahrzeuge in Stein denen in Divera 24/7 zugeordnet werden können, wird das Feld Kennzeichen genutzt. Daher müssen sowohl in Stein als auch in Divera 24/7 die Kennzeichen gepflegt und identisch sein. 
1. Kopiere config.json.sample nach config.json
1. Editieren von config.json
    1. Divera: Unter "accesskey" den vorher generierten Accesskey eintragen.
    1. Stein: Hier den API KEy des angelegten Benutzers eintragen. Unter "buname" wird die ID der Organisationseinheit eingetragen. Dies ist der Name des OVs ohne Dienststellenkürzel. Also "671" für OV Siegburg.
1. Anschließend das script divera.py aufrufen. 

## Docker
```shell
docker build -t steinapi .
docker run -ti --rm -v <config_folder>:/app/config steinapi --config /app/config/config.json --direction divera
```

# Hinweis
Das Projekt habe ich in meiner Freizeit für unseren OV geschrieben. Aufgrund der Nachfrage habe ich es dann auf GitHub veröffentlicht. Sämtlicher Code versteht sich ohne irgendwelche Haftung. Falls Fehler gefunden werden, gerne im Bugtracker melden. Ich freue mich auch über merge requests :)
