"""Fabrique la requête Buffer (colonne M du Journal de publication).
Usage :
  Reel  : python3 -I buffer_requete.py --texte texte.txt --url <lien public mp4> --date-utc 2026-10-24T16:00:00.000Z
  Story : python3 -I buffer_requete.py --format story --url <lien public mp4> --date-utc 2026-10-24T16:00:00.000Z
Une story Instagram publiée automatiquement n'affiche ni texte ni lien (Buffer l'exige) : la requête story
part donc sans texte, toutes les infos doivent être dans la vidéo (3 à 60 s, 9:16).
Affiche le JSON à coller tel quel dans la colonne M."""
import json, argparse
CANAL = "6ada3acb778b240e2f8e831e"  # compte Instagram de test autoagent46
p = argparse.ArgumentParser()
p.add_argument('--format', choices=['reel', 'story'], default='reel')
p.add_argument('--texte', default=None); p.add_argument('--url', required=True)
p.add_argument('--date-utc', required=True); p.add_argument('--canal', default=CANAL)
p.add_argument('--vignette-ms', type=int, default=3000)
a = p.parse_args()
if a.format == 'reel':
    if not a.texte:
        p.error('--texte est obligatoire pour un Reel')
    texte = open(a.texte, encoding='utf-8').read().strip()
    video = '{ url: %s, metadata: { thumbnailOffset: %d } }' % (json.dumps(a.url), a.vignette_ms)
    meta = '{ type: reel, shouldShareToFeed: true }'
else:
    texte = ''
    video = '{ url: %s }' % json.dumps(a.url)
    meta = '{ type: story, shouldShareToFeed: false }'
q = ("mutation { createPost(input: { text: %s, channelId: %s, schedulingType: automatic, mode: customScheduled, "
     "dueAt: %s, assets: [{ video: %s }], metadata: { instagram: %s } }) "
     "{ ... on PostActionSuccess { post { id } } ... on MutationError { message } } }") % (
     json.dumps(texte, ensure_ascii=False), json.dumps(a.canal), json.dumps(a.date_utc), video, meta)
print(json.dumps({"query": q}, ensure_ascii=False))
