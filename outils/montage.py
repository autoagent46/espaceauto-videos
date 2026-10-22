"""Montage vertical EspaceAuto : intro + vidéo (plaques floutées, logo) + écran de fin + musique.

Usage :
  python3 -I montage.py --source rush.mp4 --musique musique.mp3 --sortie final.mp4 \
      --intro "Vous cherchez|un véhicule|d'exception ?" [--garder-son] [--sans-floutage] [--duree-max 90]

- La dernière ligne de --intro s'affiche en doré.
- --garder-son : garde la voix de la vidéo et met la musique très bas dessous (vidéo où quelqu'un parle).
- Produit aussi <sortie>_planche.jpg (12 images réparties sur la vidéo) pour vérifier le résultat à l'œil.
"""
import argparse, os, subprocess, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
from plaques import detect  # noqa: E402

W, H, FPS = 1080, 1920, 30
POLICE = '/usr/share/fonts/truetype/google-fonts/Poppins-'
OR, BLANC, GRIS, NOIR = (196, 163, 90), (245, 242, 235), (170, 165, 155), (26, 24, 20)


def police(graisse, taille):
    try:
        return ImageFont.truetype(POLICE + graisse + '.ttf', taille)
    except OSError:
        return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', taille)


def fond():
    y, x = np.mgrid[0:H, 0:W]
    d = np.sqrt(((x - W / 2) / W) ** 2 + ((y - H * 0.42) / H) ** 2)
    t = np.clip(d / 0.75, 0, 1)[..., None]
    c = (1 - t) * np.array([52, 46, 36]) + t * np.array([17, 17, 17])
    return Image.fromarray(c.astype('uint8')).convert('RGBA')


FOND = fond()
LOGO = Image.open(os.path.join(ICI, '..', 'ressources', 'logo_blanc.png')).convert('RGBA')


def poser_logo(img, largeur, cy, alpha=1.0):
    l = LOGO.resize((largeur, int(LOGO.size[1] * largeur / LOGO.size[0])), Image.LANCZOS)
    if alpha < 1:
        a = np.array(l); a[..., 3] = (a[..., 3] * alpha).astype('uint8'); l = Image.fromarray(a)
    img.alpha_composite(l, ((W - l.size[0]) // 2, int(cy - l.size[1] / 2)))


def centrer(d, y, s, f, couleur, espace=0):
    if espace:
        tw = sum(d.textlength(c, font=f) for c in s) + espace * (len(s) - 1); x = (W - tw) / 2
        for c in s:
            d.text((x, y), c, font=f, fill=couleur); x += d.textlength(c, font=f) + espace
    else:
        d.text(((W - d.textlength(s, font=f)) / 2, y), s, font=f, fill=couleur)


def doux(t):
    return 1 - (1 - min(max(t, 0), 1)) ** 3


def avec_alpha(rgb, a):
    return rgb + (int(255 * a),)


def intro(t, lignes):
    img = FOND.copy(); poser_logo(img, 300, 110)
    c = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(c)
    lw = int(220 * doux((t - 0.1) / 0.5)); d.rectangle(((W - lw) // 2, 690, (W + lw) // 2, 695), fill=OR)
    f = police('Bold', 92 if max(len(s) for s in lignes) <= 16 else 72)
    for i, s in enumerate(lignes):
        q = doux((t - 0.15 * i) / 0.6)
        centrer(d, 740 + i * 115 + int(40 * (1 - q)), s, f, avec_alpha(OR if i == len(lignes) - 1 else BLANC, q))
    img.alpha_composite(c); return img


def fin(t):
    img = FOND.copy(); c = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(c)
    q = doux(t / 0.6); poser_logo(img, 760, 700 - int(30 * (1 - q)), q)
    centrer(d, 790, 'CONSEIL ET VENTE AUTOMOBILE', police('Regular', 30), avec_alpha(GRIS, doux((t - 0.2) / 0.5)), espace=6)
    lw = int(120 * doux((t - 0.3) / 0.4)); d.rectangle(((W - lw) // 2, 870, (W + lw) // 2, 874), fill=OR)
    centrer(d, 900, 'Ronchin', police('Medium', 44), avec_alpha(OR, doux((t - 0.35) / 0.5)))
    q2 = doux((t - 0.5) / 0.5)
    if q2 > 0:
        y0 = 1010 + int(30 * (1 - q2))
        d.rounded_rectangle((W / 2 - 300, y0, W / 2 + 300, y0 + 110), radius=55, fill=avec_alpha(OR, q2))
        centrer(d, y0 + 18, '06 30 26 06 86', police('Bold', 60), avec_alpha(NOIR, q2))
    centrer(d, 1170, 'espaceautomp.fr', police('Medium', 44), avec_alpha(BLANC, doux((t - 0.7) / 0.5)))
    img.alpha_composite(c); return img


def remplir_vertical(f):
    """Recadre et met à l'échelle pour remplir 1080x1920 sans bandes noires."""
    h, w = f.shape[:2]; s = max(W / w, H / h)
    f = cv2.resize(f, (int(w * s + 0.5), int(h * s + 0.5)), interpolation=cv2.INTER_LANCZOS4)
    y0 = (f.shape[0] - H) // 2; x0 = (f.shape[1] - W) // 2
    return f[y0:y0 + H, x0:x0 + W]


def flouter(f, boites, marge=0.15):
    H0, W0 = f.shape[:2]
    for x, y, w, h in boites:
        mx, my = int(w * marge), int(h * marge * 1.6)
        x0, y0 = max(0, x - mx), max(0, y - my); x1, y1 = min(W0, x + w + mx), min(H0, y + h + my)
        roi = f[y0:y1, x0:x1]
        if roi.size:
            petit = cv2.resize(roi, (max(1, (x1 - x0) // 10), max(1, (y1 - y0) // 10)))
            f[y0:y1, x0:x1] = cv2.GaussianBlur(cv2.resize(petit, (x1 - x0, y1 - y0)), (0, 0), 6)
    return f


def debut_musique(chemin):
    """Première seconde où la musique est vraiment lancée (évite un long fondu d'ouverture)."""
    for s in range(0, 30):
        r = subprocess.run(['ffmpeg', '-nostats', '-ss', str(s), '-t', '1', '-i', chemin, '-af', 'volumedetect', '-f', 'null', '-'],
                           capture_output=True, text=True).stderr
        for ligne in r.splitlines():
            if 'mean_volume' in ligne and float(ligne.split(':')[1].split()[0]) > -16:
                return s
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', required=True); p.add_argument('--musique', required=True)
    p.add_argument('--sortie', required=True); p.add_argument('--intro', default="Vous cherchez|un véhicule|d'exception ?")
    p.add_argument('--garder-son', action='store_true'); p.add_argument('--sans-floutage', action='store_true')
    p.add_argument('--duree-max', type=float, default=90)
    a = p.parse_args()
    lignes = a.intro.split('|')

    cap = cv2.VideoCapture(a.source); fps_src = cap.get(cv2.CAP_PROP_FPS) or 30
    n_src = int(min(cap.get(cv2.CAP_PROP_FRAME_COUNT), a.duree_max * fps_src))
    boites = []
    if not a.sans_floutage:  # passe 1 : détection
        for _ in range(n_src):
            ok, f = cap.read()
            if not ok: break
            boites.append(detect(f))
        cap.release(); cap = cv2.VideoCapture(a.source)
    fen = 7
    n_intro, n_fin, XF = int(2.2 * FPS), int(3.5 * FPS), 8
    n_clip = int(n_src / fps_src * FPS)
    tmp = a.sortie + '.video.mp4'
    pr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '19', '-preset', 'medium', tmp], stdin=subprocess.PIPE)
    haut = np.zeros((H, W, 1), np.float32); haut[:260, :, 0] = np.linspace(0.55, 0, 260)[:, None]
    fil = Image.new('RGBA', (W, H)); poser_logo(fil, 300, 110); fil = np.array(fil).astype(np.float32); fa = fil[..., 3:] / 255
    cache = {'i': -1, 'f': None}

    def image_clip(k):  # k = index d'image à 30 i/s ; lecture séquentielle de la source
        j = min(int(k * fps_src / FPS), n_src - 1)
        while cache['i'] < j:
            ok, f = cap.read()
            if not ok: break
            cache['i'] += 1
            if boites:
                bx = [b for t in range(max(0, cache['i'] - fen), min(len(boites), cache['i'] + fen + 1)) for b in boites[t]]
                f = flouter(f, bx)
            cache['f'] = f
        f = remplir_vertical(cv2.cvtColor(cache['f'], cv2.COLOR_BGR2RGB)).astype(np.float32) * (1 - haut)
        return (f * (1 - fa) + fil[..., :3] * fa).astype('uint8')

    premiere_clip = image_clip(0)
    planche = []
    segs = [('intro', n_intro), ('clip', n_clip), ('fin', n_fin)]
    total = sum(n for _, n in segs); pas = max(1, total // 12); compteur = 0
    for s, (nom, n) in enumerate(segs):
        for i in range(n):
            if nom == 'intro': fr = np.array(intro(i / FPS, lignes).convert('RGB'))
            elif nom == 'clip': fr = premiere_clip if i == 0 else image_clip(i)
            else: fr = np.array(fin(i / FPS).convert('RGB'))
            if s + 1 < len(segs) and i >= n - XF:
                suiv = premiere_clip if segs[s + 1][0] == 'clip' else np.array(fin(0).convert('RGB'))
                al = (i - (n - XF) + 1) / (XF + 1); fr = (fr.astype(np.float32) * (1 - al) + suiv.astype(np.float32) * al).astype('uint8')
            if compteur % pas == 0 and len(planche) < 12: planche.append(cv2.resize(fr, (270, 480)))
            pr.stdin.write(fr.tobytes()); compteur += 1
    pr.stdin.close(); pr.wait()
    duree = total / FPS
    ms = debut_musique(a.musique)
    if a.garder_son:
        filtre = (f"[1:a]atrim=0:{duree},asetpts=PTS-STARTPTS,volume=-20dB,afade=t=out:st={duree-2}:d=2[m];"
                  f"[2:a]adelay={int(n_intro / FPS * 1000)}|{int(n_intro / FPS * 1000)},loudnorm=I=-16[v];[v][m]amix=inputs=2:duration=first:normalize=0[a]")
        entrees = ['-i', tmp, '-ss', str(ms), '-i', a.musique, '-i', a.source]
    else:
        filtre = f"[1:a]atrim=0:{duree},asetpts=PTS-STARTPTS,volume=-4dB,afade=t=in:d=0.3,afade=t=out:st={duree-1.7}:d=1.7[a]"
        entrees = ['-i', tmp, '-ss', str(ms), '-i', a.musique]
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *entrees, '-filter_complex', filtre, '-map', '0:v', '-map', '[a]',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', str(duree), '-movflags', '+faststart', a.sortie], check=True)
    os.remove(tmp)
    while len(planche) % 6: planche.append(np.zeros_like(planche[0]))
    pl = np.vstack([np.hstack(planche[k:k + 6]) for k in range(0, len(planche), 6)])
    Image.fromarray(pl).save(os.path.splitext(a.sortie)[0] + '_planche.jpg', quality=85)
    print(f'OK {a.sortie} {duree:.1f} s, plaques détectées sur {sum(1 for b in boites if b)}/{len(boites)} images')


if __name__ == '__main__':
    main()
