# Procédure quotidienne — Agent réseaux sociaux EspaceAutoMP

Ce fichier est lu à chaque exécution de la tâche planifiée. Les règles métier complètes (RTCE des 4 agents) sont dans
`INSTRUCTIONS-RTCE.md` : lis-les avant de commencer. Ce fichier-ci décrit les opérations techniques, dans l'ordre.

Tu travailles seul : Raphaël n'est pas là. Tu ne lui poses pas de question dans la conversation ;
quand tu as besoin de lui, tu lui écris par e-mail (Gmail, à raphaelclep@gmail.com) et tu mets la vidéo en « A valider ».

## Références

| Élément | Valeur |
| --- | --- |
| Dépôt GitHub (outils + vidéos publiques) | autoagent46/espaceauto-videos, branche main |
| Lien public d'une vidéo | https://autoagent46.github.io/espaceauto-videos/<dossier>/<fichier>.mp4 |
| Journal de publication (Google Sheet) | 1djCp49dPOF3zuEKoXXMrujMqEBdL5cnbneoqldxvAJQ, onglet « Feuille 1 » |
| Compte Instagram de test dans Buffer | 6ada3acb778b240e2f8e831e (déjà codé dans outils/buffer_requete.py) |
| Drive « 01 - A traiter » | 1u7hLN4CM8S8rXIPscoeixERfSG89gST7 |
| ↳ Presentation / Livraison / Conseil / Autre | 1Lkz5YI12sUq89yOoJhNCMGP19P-4nXGk / 18ldhMvkCcuwnaUJVF6t9uScSLEIVZAsm / 1Ig14rQSeqsnYFHsSpIh5ijtc95Ddo4Dy / 1sZYQYw6GiO7btnyO5L6jDvwDr9rQURPd |
| Drive « Musiques » | 1uYPUvp7SxMrccDlWsNHrfKxDuUpFNT9Q |
| Drive « 03 - A valider » | 1MwQfmTcYvpriWhdsM8V2elWCVlLazHU7 |
| Drive « 05 - Publie » | 1D6-KBnHxP5SELTZSL8k-qnmDpCGfS6sm |

Colonnes du journal : A Date · B Heure (France) · C Date ISO UTC · D Type · E Sujet · F Fichier · G Lien vidéo public ·
H Texte Instagram · I Musique · J Statut · K ID Buffer · L Remarques · M Requête Buffer.
Statuts : `A valider` · `Planifié` · `Envoyé à Buffer` · `Publié` · `Erreur`.
Make lit toutes les 4 h les lignes `Planifié`, envoie la colonne M à Buffer et passe la ligne à `Envoyé à Buffer`
(ou `Erreur`). Tu n'appelles jamais Buffer toi-même.

## Étape 0 — Préparer l'espace de travail

1. Si `/home/claude/espaceauto-videos` n'existe pas : `git clone --depth 1 https://github.com/autoagent46/espaceauto-videos`.
   Sinon `git -C ... pull`.
2. Travaille dans un dossier temporaire à toi (pas dans le dépôt) pour les rushes et les fichiers intermédiaires.

## Étape 1 — Ménage des publications passées

Lis le journal. Pour chaque ligne `Envoyé à Buffer` dont la date + heure est passée de plus de 24 h :
- passe le statut à `Publié` ;
- supprime la vidéo du dépôt (dossier `pret-a-publier/` ou `a-valider/`), commit, push.

Pour chaque ligne `Erreur` : écris un e-mail à Raphaël avec le contenu de la colonne L, puis ajoute « signalé le <date> »
dans la colonne L pour ne pas le signaler deux fois.

## Étape 2 — Trouver le travail du jour

1. Liste le contenu des 4 dossiers de « 01 - A traiter » (search_files avec `parentId = '<id>'`).
   Un élément = un fichier vidéo ou photo posé directement, ou un sous-dossier (un véhicule = un sous-dossier).
2. Traite au maximum **2 éléments** par exécution, du plus ancien au plus récent.
3. S'il n'y a rien : pas d'e-mail, fin de l'exécution.

## Étape 3 — Télécharger

- `download_file_content` sur chaque fichier. Les gros fichiers sont enregistrés par l'outil dans un fichier
  `tool-results/...txt` (le chemin est donné dans l'erreur « exceeds maximum allowed tokens ») :
  décode-le avec `python3 -I outils/drive_decode.py <ce fichier> <sortie>`.
- Télécharge aussi une musique du dossier Musiques, différente de celle de la dernière ligne du journal (colonne I).

## Étape 4 — Agent 1 : Vidéo

Suis `INSTRUCTIONS-RTCE.md` (Agent 1). Côté technique :
- Infos véhicule : lis https://espaceautomp.fr/ avec WebFetch (pas curl : le site est bloqué depuis le terminal),
  puis la page de l'annonce correspondante.
- Transcription (vidéo où quelqu'un parle, obligatoire pour Conseil) : essaie
  `pip install --break-system-packages faster-whisper` puis un modèle « small » en français.
  Si l'installation ou le téléchargement du modèle échoue → la vidéo passe en `A valider` avec la raison
  « transcription impossible » (sauf si le nom du fichier donne le sujet).
- Montage : `python3 -I outils/montage.py --source <rush> --musique <mp3> --sortie <AAAA-MM-JJ_type_sujet.mp4> --intro "Ligne 1|Ligne 2|Ligne dorée"`
  Ajoute `--garder-son` si quelqu'un parle. Les lignes d'intro : 3 lignes courtes (16 caractères max chacune),
  sans aucune info non vérifiée.
- Vérification : ouvre `<sortie>_planche.jpg` avec Read et regarde chaque image.
  **Limite connue** : le floutage automatique ne reconnaît que les plaques **bleues**. Les plaques françaises
  (fond blanc) ne sont pas détectées. Si une plaque est lisible sur la planche → `A valider`, raison « plaque visible ».
- Photos seulement (pas de vidéo) : pas encore d'outil prêt → `A valider`, raison « montage photos à faire ».

## Étape 5 — Agent 2 : Texte

Suis `INSTRUCTIONS-RTCE.md` (Agent 2). Écris le texte dans un fichier `texte.txt` (UTF-8, sans emoji).

## Étape 6 — Agent 3 : Contrôle

Applique la grille de `INSTRUCTIONS-RTCE.md` (Agent 3), en relisant l'annonce sur le site au moment du contrôle.
Verdict : `Validé`, `Renvoyé` (tu corriges toi-même, 2 fois maximum) ou `A valider`.

## Étape 7 — Agent 4 : Planification et dépôt

Dans les deux cas (Validé ou A valider) :
1. Copie la vidéo dans le dépôt : `pret-a-publier/` si Validé, `a-valider/` si A valider. Commit + push
   (message clair, se termine par les lignes d'attribution habituelles).
2. Choisis la date (règles Agent 4 : premier jour libre dans le journal, jamais 2 publications le même jour,
   au plus 10 lignes `Planifié` + `Envoyé à Buffer` futures) et l'heure (lun-ven 18:00, sam 11:00, dim 18:30, heure de Paris).
   Convertis en UTC avec Python (`zoneinfo`, Europe/Paris : attention au changement d'heure).
3. Fabrique la requête : `python3 -I outils/buffer_requete.py --texte texte.txt --url <lien public> --date-utc <ISO UTC>`.
4. Ajoute une ligne au journal (A à M remplies, K vide). Statut : `Planifié` si Validé, `A valider` sinon.
5. Déplace le fichier ou sous-dossier source du Drive : vers « 05 - Publie » si Validé, vers « 03 - A valider » sinon.
   Renomme-le en commençant par la date (AAAA-MM-JJ_...) pour le retrouver.
6. Si `A valider` : envoie un e-mail à raphaelclep@gmail.com
   - Objet : `[EspaceAuto] Vidéo à valider : <sujet>`
   - Corps : la raison précise, le lien public de la vidéo, le texte prévu, la date prévue, et la marche à suivre :
     « Pour publier : passe la ligne <n> du Journal de publication en Planifié. Pour refuser : passe-la en Erreur. »
   - Si la date prévue est passée quand il valide, il doit aussi la modifier : précise-le dans l'e-mail.

## Fin d'exécution

Termine par un court résumé (ce qui a été traité, statut de chaque vidéo). Si une étape a échoué de façon inattendue,
écris un e-mail à Raphaël avec l'erreur et laisse les fichiers sources dans « 01 - A traiter ».
Ne publie jamais rien qui n'est pas passé par l'agent 3.
