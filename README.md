# steinapi
Ziel des Projekt ist die synchronisierung zwischen Stein.APP und Divera 24/7.

## Einrichtung
1. Voarb: Zunächst werden je ein Nutzer in Stein.APP und Divera 24/7 benötigt.
    1. Divera 24/7: Im Menüpunkt Verwaltung -> Schnittstellen -> System-Benutzer muss ein neuer System-Benutzer angelegt werden. Der dabei generierte Accesskey wird gleich benötigt.
    1. Stein.APP: Prinzipiell ist kein separater Nutzer notwendig. Zu besseren Abgrenzung der Änderungen durch die Api und durch manuelle Änderungen hat sich jedoch ein eingener Nutzer bewährt. 
1. Damit die Fahrzeuge in Stein denen in Divera 24/7 zugeordnet werden können, wird das Feld Kennzeichen genutzt. Daher müssen sowohl in Stein als auch in Divera 24/7 die Kennzeichen gepflegt und identisch sein. 
1. Kopiere config.json.sample nach config.json
1. Editieren von config.json
    1. Divera: Unter "accesskey" den vorher generierten Accesskey eintragen.
    1. Stein: Hier die Nutzerdaten des angelegten Benutzers eintragen. Unter "buname" wird der Name der Organisationseinheit eingetragen. Dies ist der Name des OVs ohne Dienststellenkürzel. Also "Paderborn" für OV Paderborn.
1. Anschließend das script divera.py aufrufen. 

# Hinweis
Das Projekt habe ich in meiner Freizeit für unseren OV geschrieben. Aufgrund der Nachfrage habe ich es dann auf GitHub veröffentlicht. Sämtlicher Code versteht sich ohne irgendwelche Haftung. Falls Fehler gefunden werden, gerne im Bugtracker melden. Ich freue mich auch über merge requests :)
