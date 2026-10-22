/**
 * EspaceAuto : copie automatiquement les rushes du Drive (« 01 - A traiter ») vers le dépôt GitHub privé
 * autoagent46/espaceauto-rushes, pour que l'agent Claude puisse les récupérer (le connecteur Drive est limité à 10 Mo).
 *
 * Installation (une seule fois) :
 *  1. Paramètres du projet (roue dentée) > Propriétés du script > ajouter GITHUB_TOKEN = <ton jeton GitHub>
 *  2. Choisir la fonction « installer » en haut, cliquer sur Exécuter, accepter les autorisations.
 */

const PROPRIETAIRE = 'autoagent46';
const DEPOT = 'espaceauto-rushes';
const DOSSIERS = {
  'Presentation': '1Lkz5YI12sUq89yOoJhNCMGP19P-4nXGk',
  'Livraison': '18ldhMvkCcuwnaUJVF6t9uScSLEIVZAsm',
  'Conseil': '1Ig14rQSeqsnYFHsSpIh5ijtc95Ddo4Dy',
  'Autre': '1sZYQYw6GiO7btnyO5L6jDvwDr9rQURPd',
};
const TAILLE_MAX = 35 * 1024 * 1024; // au-delà, la limite de 50 Mo par envoi de Google est dépassée

function installer() {
  ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('copierVersGitHub').timeBased().everyMinutes(15).create();
  copierVersGitHub();
}

function copierVersGitHub() {
  const props = PropertiesService.getScriptProperties();
  const jeton = props.getProperty('GITHUB_TOKEN');
  if (!jeton) throw new Error('GITHUB_TOKEN manquant dans les propriétés du script');
  const debut = Date.now();

  for (const [type, id] of Object.entries(DOSSIERS)) {
    const dossier = DriveApp.getFolderById(id);
    traiter(dossier.getFiles(), type, '_');
    const sous = dossier.getFolders();
    while (sous.hasNext()) {
      const s = sous.next();
      traiter(s.getFiles(), type, s.getName());
    }
  }

  function traiter(fichiers, type, sousDossier) {
    while (fichiers.hasNext()) {
      if (Date.now() - debut > 4.5 * 60 * 1000) return; // limite de 6 min par exécution
      const f = fichiers.next();
      const cle = 'f_' + f.getId();
      if (props.getProperty(cle)) continue; // déjà copié
      if (f.getSize() > TAILLE_MAX) {
        props.setProperty(cle, 'trop_gros');
        const mo = Math.round(f.getSize() / 1048576);
        f.setDescription('Trop lourd pour la copie automatique (' + mo + ' Mo, maximum 35 Mo)');
        MailApp.sendEmail(Session.getEffectiveUser().getEmail(),
          '[EspaceAuto] Vidéo trop lourde : ' + f.getName(),
          'La vidéo « ' + f.getName() + ' » (' + type + ') fait ' + mo + ' Mo. ' +
          'La copie automatique est limitée à 35 Mo : raccourcis-la ou filme en 1080p, puis dépose la nouvelle version.');
        continue;
      }
      const chemin = [type, nettoyer(sousDossier), f.getId() + '__' + nettoyer(f.getName())].join('/');
      const reponse = UrlFetchApp.fetch(
        'https://api.github.com/repos/' + PROPRIETAIRE + '/' + DEPOT + '/contents/' + encodeURI(chemin), {
          method: 'put',
          contentType: 'application/json',
          headers: { Authorization: 'Bearer ' + jeton, Accept: 'application/vnd.github+json' },
          payload: JSON.stringify({ message: 'Rush ' + chemin, content: Utilities.base64Encode(f.getBlob().getBytes()) }),
          muteHttpExceptions: true,
        });
      if (reponse.getResponseCode() < 300) {
        props.setProperty(cle, chemin);
        f.setDescription('Copié vers GitHub : ' + chemin);
        console.log('Copié : ' + chemin);
      } else {
        console.error('Échec ' + chemin + ' : ' + reponse.getResponseCode() + ' ' + reponse.getContentText().slice(0, 300));
      }
    }
  }
}

function nettoyer(s) {
  return s.normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^A-Za-z0-9._-]+/g, '-');
}
