"""Fabrique la requête Buffer (colonne M du Journal de publication).
Usage : python3 -I buffer_requete.py --texte texte.txt --url <lien public mp4> --date-utc 2026-10-24T16:00:00.000Z
Affiche le JSON à coller tel quel dans la colonne M."""
import json, argparse
CANAL = "6ada3acb778b240e2f8e831e"  # compte Instagram de test autoagent46
p = argparse.ArgumentParser()
p.add_argument('--texte', required=True); p.add_argument('--url', required=True)
p.add_argument('--date-utc', required=True); p.add_argument('--canal', default=CANAL)
p.add_argument('--vignette-ms', type=int, default=3000)
a = p.parse_args()
texte = open(a.texte, encoding='utf-8').read().strip()
q = ("mutation { createPost(input: { text: %s, channelId: %s, schedulingType: automatic, mode: customScheduled, "
     "dueAt: %s, assets: [{ video: { url: %s, metadata: { thumbnailOffset: %d } } }], "
     "metadata: { instagram: { type: reel, shouldShareToFeed: true } } }) "
     "{ ... on PostActionSuccess { post { id } } ... on MutationError { message } } }") % (
     json.dumps(texte, ensure_ascii=False), json.dumps(a.canal), json.dumps(a.date_utc), json.dumps(a.url), a.vignette_ms)
print(json.dumps({"query": q}, ensure_ascii=False))
