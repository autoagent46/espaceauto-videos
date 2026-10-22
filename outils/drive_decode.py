"""Décode un fichier téléchargé avec l'outil Google Drive (download_file_content).
Quand le résultat est trop gros, l'outil l'enregistre dans un fichier JSON {content: base64, ...}.
Usage : python3 -I drive_decode.py <fichier_resultat.txt> <sortie>"""
import json, base64, sys
d = json.load(open(sys.argv[1]))
open(sys.argv[2], 'wb').write(base64.b64decode(d['content']))
print(sys.argv[2], d.get('title'), d.get('mimeType'))
