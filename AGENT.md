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

**Surveillance de Make** (Make ne prévient pas toujours par e-mail quand il plante) : pour chaque ligne `Planifié`
dont la date + heure de publication est passée, ou arrive dans moins de 6 h, Make n'a pas fait son travail
(il passe toutes les 4 h). Envoie un e-mail à Raphaël :
- Objet : `[EspaceAuto] ALERTE Make : publication non envoyée à Buffer`
- Corps : les lignes concernées (date, sujet) et la marche à suivre : « Ouvre Make > Scenarios > Integration Google Sheets, HTTP >
  History. Si le scénario est désactivé, réactive-le ; s'il y a une ligne rouge, envoie une capture dans le projet. »
Ne modifie pas ces lignes toi-même.

Pour chaque ligne `Erreur` : écris un e-mail à Raphaël avec le contenu de la colonne L, puis ajoute « signalé le <date> »
dans la colonne L pour ne pas le signaler deux fois.

## Étape 2 — Trouver le travail du jour

**Combien en faire : remplir la file jusqu'à 3.**
Compte les lignes du journal en `Planifié` ou `Envoyé à Buffer` dont la date de publication n'est pas encore passée.
- 3 ou plus : la file est pleine. Ne traite rien de nouveau aujourd'hui (seulement le ménage et la surveillance).
- Moins de 3 : traite des éléments **à la chaîne**, un par un, jusqu'à ce que la file atteigne 3 (ou qu'il n'y ait plus rien).
  Une vidéo qui finit en `A valider` ne compte pas dans la file : passe à l'élément suivant.

**Deux sources, traitées en alternance** (une vidéo déposée, puis un lien, puis une vidéo…), pour varier les publications
et ne laisser aucune source attendre l'autre :

*Source A — vidéos et photos déposées* : contenu des 4 sous-dossiers de « 01 - A traiter » (search_files avec `parentId = '<id>'`),
du plus ancien au plus récent. Un élément = un fichier vidéo ou photo posé directement, ou un sous-dossier (un véhicule = un sous-dossier).

*Source B — liens d'annonce* : un seul endroit, le document Google Docs « Annonces a traiter » posé à la racine de « 01 - A traiter »
(ID 1gMxpgk9Q0UXFtrhSbw6CrHM-nqpJzF4D0ixa8Af2vcY). Ne cherche des liens nulle part ailleurs.
1. Lis-le avec read_file_content, puis extrais **tous** les liens d'annonce où qu'ils soient dans le texte
   (Google Docs les met parfois sur une seule ligne, entourés de `<…>`) :
   `python3 -c "import re,sys; print('\n'.join(dict.fromkeys(re.findall(r'https://espaceautomp\.fr/listings/[^\s<>\"]+', sys.stdin.read()))))"`
   en lui envoyant le texte du document. Garde l'ordre d'apparition, sans doublon, et normalise chaque lien avec un `/` final.
2. Un lien est **déjà traité** si la colonne L du journal contient `Annonce : <ce lien>`. Ignore-le.
   Ne modifie jamais ce document (Raphaël y ajoute des liens ; tu ne supprimes rien).
3. Pour un lien non traité, lis l'annonce (curl avec en-tête navigateur, voir étape 4) :
   - annonce introuvable (404) ou marquée vendue → ligne au journal en `A valider` avec `Annonce : <lien>` en colonne L
     et la raison, puis e-mail à Raphaël (pour ne pas retraiter le lien chaque jour) ;
   - sinon, c'est un élément « Presentation » à faire avec les photos de l'annonce (montage photos, étape 4).
4. Écris toujours `Annonce : <lien>` au début de la colonne L de la ligne du journal, quel que soit le statut.

**Une seule publication par annonce (pas de doublon)** : dès qu'un élément (vidéo déposée ou lien) est rattaché à une annonce
du site, écris `Annonce : <lien de l'annonce>` au début de la colonne L de sa ligne du journal. Avant de traiter un élément,
si son annonce figure déjà en colonne L d'une ligne `Planifié`, `Envoyé à Buffer` ou `Publié`, ne le refais pas :
- un lien → ignoré (déjà traité) ;
- une vidéo déposée → `A valider` avec la raison « annonce déjà publiée le <date> » (Raphaël décide s'il veut une 2e vidéo).

**Nom de fichier** : si le nom d'une vidéo déposée contient un lien d'annonce ou le nom de l'annonce tel qu'il apparaît dans le lien
(ex. `volkswagen-tiguan-2-0-tdi-150ch-dsg7-r-line`), utilise directement cette annonce, sans chercher à identifier le véhicule.

Aucune limite de taille pour les vidéos (jusqu'à plusieurs centaines de Mo) : voir l'étape 3.
S'il n'y a rien dans aucune des deux sources : pas d'e-mail, fin de l'exécution.

## Étape 3 — Télécharger

- **Rushes** (tout ce qui est dans « 01 - A traiter ») : téléchargement direct, sans passer par le connecteur Drive.
  Le dossier « 01 - A traiter » est partagé en lecture « Tous les utilisateurs disposant du lien » (depuis le 25/10/2026),
  et les domaines Google Drive sont autorisés dans l'espace de travail :
  `curl -sSL -o <sortie> "https://drive.usercontent.google.com/download?id=<ID du fichier>&export=download&confirm=t"`
  (`confirm=t` passe l'avertissement de Google sur les gros fichiers). Vérifie ensuite avec `file <sortie>` que c'est bien
  une vidéo ou une image : une page HTML veut dire que le partage a été retiré → e-mail à Raphaël, fichier laissé en place.
- Sous-dossier véhicule : liste ses fichiers avec search_files (`parentId = '<id du sous-dossier>'`), puis télécharge-les un par un.
- **Musique** : le dossier Musiques n'est pas partagé publiquement. Utilise `download_file_content` (fichiers de moins de 10 Mo).
  Si l'outil enregistre le résultat dans un fichier `tool-results/...txt`, décode-le avec `python3 -I outils/drive_decode.py <ce fichier> <sortie>`.
  Choisis une musique différente de celle de la dernière ligne du journal (colonne I).
- Ne partage jamais d'autre dossier « avec le lien » : seul « 01 - A traiter » l'est.

## Étape 4 — Agent 1 : Vidéo

Suis `INSTRUCTIONS-RTCE.md` (Agent 1). Côté technique :
- Infos véhicule : lis le site avec curl **en se présentant comme un navigateur** (sans ça, le site répond 403) :
  `curl -sS -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36" https://espaceautomp.fr/vehicules/page/<n>/`
  La liste des annonces est sur https://espaceautomp.fr/vehicules/ (puis /vehicules/page/2/ etc., jusqu'à la page qui répond 404).
  Chaque annonce a un lien https://espaceautomp.fr/listings/<modele>/ et une photo (wp-content/uploads/...) à comparer avec la vidéo.
  Le site a **plusieurs pages d'annonces** : lis-les **toutes** (pages 2, 3, 4… jusqu'à la dernière) avant de conclure
  qu'un véhicule n'est pas en vente.
- Annonce introuvable après lecture de toutes les pages : applique la règle « Annonce introuvable » de `INSTRUCTIONS-RTCE.md`
  (WebSearch puis WebFetch sur le site du constructeur ou une fiche technique L'argus / Caradisiac / Auto Plus).
  L'intro et la fiche peuvent afficher la motorisation (ex. « 2.5 TFSI »), jamais prix, km ni année.
- Vidéo déposée sans nom de véhicule (fichier posé directement dans Presentation, nom du type IMG_1234.MOV) :
  identifie le véhicule en comparant la vidéo (marque, modèle, couleur, jantes) aux annonces du site.
  Une seule annonce correspond sans aucun doute → continue avec ses infos. Plusieurs possibles ou aucune → `A valider`.
- Transcription (vidéo où quelqu'un parle, obligatoire pour Conseil) : essaie
  `pip install --break-system-packages faster-whisper` puis un modèle « small » en français.
  Si l'installation ou le téléchargement du modèle échoue → la vidéo passe en `A valider` avec la raison
  « transcription impossible » (sauf si le nom du fichier donne le sujet).
- Montage : `python3 -I outils/habillage.py` (habillage animé : logo qui se construit, accroche ligne par ligne,
  fiche véhicule animée avec prix et caractéristiques en pastilles, badge VENDUE, écran de fin animé). Voir l'aide en tête du fichier.
  - Présentation en vente : `--modele "MARQUE MODÈLE" --version "motorisation finition" --prix "6 990 €" --infos "km|carburant|année|boîte"`
    (toutes ces infos viennent de l'annonce du site, ou des infos génériques sourcées si l'annonce est introuvable — jamais de prix/km/année inventés).
  - Véhicule vendu : `--vendu` (badge VENDUE permanent, pas de prix, fin « Vous voulez vendre la vôtre ? »).
  - Rush sans voix (images ou vidéos de voiture seules) : `--accroche "Ligne 1|Ligne dorée|Ligne dorée" --musique <mp3> --volume-musique -16`
    (musique douce, environ -27 LUFS ; pas de son d'origine).
  - Vidéo où quelqu'un parle : `--garder-son` sans musique si la vidéo a déjà un fond sonore ; place `--fiche-debut` quand le véhicule est à l'écran.
  - Plus de 90 s : coupe avec `--debut-source/--fin-source`, ou pose l'intro/la fin sur la vidéo (`--intro-superposee --fin-superposee`).
  - L'ancien `outils/montage.py` (avec floutage des plaques) reste disponible si une vraie plaque avec numéro doit être floutée.
- Vérification : ouvre `<sortie>_planche.jpg` avec Read et regarde chaque image (textes lisibles, rien de coupé, bon véhicule).
  **Plaques** : les véhicules du garage portent des plaques de la société « Espace Auto » (aucun numéro
  d'immatriculation). Ces plaques sont autorisées et ne doivent pas être floutées. `habillage.py` ne floute rien
  (il n'a pas d'option de floutage : n'invente pas d'option). Si tu vois une vraie plaque avec un numéro lisible :
  passe le rush d'abord dans l'ancien `outils/montage.py` (floutage automatique, plaques bleues seulement) ou, si un numéro
  reste lisible, mets la vidéo en `A valider`.
- Taille : la vidéo finale doit faire **moins de 95 Mo** (GitHub refuse au-delà de 100 Mo). Sinon, réencode-la :
  `ffmpeg -i <vidéo> -c:v libx264 -preset veryfast -crf 26 -c:a copy -movflags +faststart <vidéo_allégée>`.
- Photos seulement (pas de vidéo) : `python3 -I outils/habillage.py --photos "p1.jpg|p2.jpg|..." --accroche "...|...|..." --modele ... --prix ... --infos ... --musique <mp3>`
  Choisis 6 photos dans cet ordre : 3/4 avant, 3/4 avant autre côté, 3/4 arrière, jante, sièges avant, sièges arrière (ou tableau de bord).
  Sans photos dans le dossier Drive, prends celles de l'annonce du site (liens wp-content/uploads/img_..._N.jpg, en taille d'origine, dans l'ordre de la page).
  Durée visée 18 à 20 s (6 photos de 2,6 s).

## Étape 5 — Agent 2 : Texte

Suis `INSTRUCTIONS-RTCE.md` (Agent 2). Écris le texte dans un fichier `texte.txt` (UTF-8, sans emoji).

## Étape 6 — Agent 3 : Contrôle

Applique la grille de `INSTRUCTIONS-RTCE.md` (Agent 3), en relisant l'annonce sur le site au moment du contrôle.
Verdict : `Validé`, `Renvoyé` (tu corriges toi-même, 2 fois maximum) ou `A valider`.

## Étape 7 — Agent 4 : Planification et dépôt

Dans les deux cas (Validé ou A valider) :
1. Copie la vidéo dans le dépôt : `pret-a-publier/` si Validé, `a-valider/` si A valider. Commit + push
   (message clair, se termine par les lignes d'attribution habituelles).
2. Choisis la date (règles Agent 4 : premier jour libre dans le journal — un jour est libre s'il n'a aucune ligne
   `Planifié`, `Envoyé à Buffer` ou `Publié` ; une ligne `A valider` ne bloque pas son jour —, jamais 2 publications le même jour,
   au plus 3 lignes `Planifié` + `Envoyé à Buffer` futures, voir étape 2) et l'heure (lun-ven 18:00, sam 11:00, dim 18:30, heure de Paris).
   Convertis en UTC avec Python (`zoneinfo`, Europe/Paris : attention au changement d'heure).
3. Fabrique la requête : `python3 -I outils/buffer_requete.py --texte texte.txt --url <lien public> --date-utc <ISO UTC>`.
4. Ajoute une ligne au journal (A à M remplies, K vide). Statut : `Planifié` si Validé, `A valider` sinon.
5. (Source A uniquement ; pour un lien d'annonce, rien à déplacer.) Déplace le fichier ou sous-dossier source du Drive : vers « 05 - Publie » si Validé, vers « 03 - A valider » sinon.
   Renomme-le en commençant par la date (AAAA-MM-JJ_...) pour le retrouver.
6. Si `A valider` : envoie un e-mail à raphaelclep@gmail.com (si la date prévue est déjà prise entre-temps, il devra la changer)
   - Objet : `[EspaceAuto] Vidéo à valider : <sujet>`
   - Corps : la raison précise, le lien public de la vidéo, le texte prévu, la date prévue, et la marche à suivre :
     « Pour publier : passe la ligne <n> du Journal de publication en Planifié. Pour refuser : passe-la en Erreur. »
   - Si la date prévue est passée quand il valide, il doit aussi la modifier : précise-le dans l'e-mail.

## Fin d'exécution

Termine par un court résumé (ce qui a été traité, statut de chaque vidéo). Si une étape a échoué de façon inattendue,
écris un e-mail à Raphaël avec l'erreur et laisse les fichiers sources dans « 01 - A traiter ».
Ne publie jamais rien qui n'est pas passé par l'agent 3.
