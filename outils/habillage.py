"""Habillage animé EspaceAuto : intro, fiche véhicule, badge VENDUE, écran de fin (1080x1920, 30 i/s).

Usage (vidéo où quelqu'un parle, véhicule en vente) :
  python3 -I habillage.py --source rush.mp4 --sortie final.mp4 --garder-son \
      --modele "RENAULT LAGUNA ESTATE" --version "2.0 dCi 130 Zen" --prix "6 990 €" \
      --infos "156 500 km|Diesel|2015|Manuelle" --fiche-debut 1.5 --fin-source 44.5

Usage (rush court sans voix, avec musique et accroche) :
  python3 -I habillage.py --source rush.mov --sortie final.mp4 --musique m.mp3 --volume-source -10 \
      --accroche "Nouvelle arrivée|Audi RS 3|Sportback" --modele "AUDI RS 3 SPORTBACK" ...

Options utiles :
  --vendu                 : badge VENDUE permanent, fiche sans prix (tampon VENDUE), fin « Vous voulez vendre la vôtre ? »
  --debut-source / --fin-source : coupe le rush (secondes)
  --intro-superposee / --fin-superposee : l'intro / la fin se posent SUR la vidéo (le son continue), au lieu de s'ajouter
  --fiche-debut S --fiche-duree D : moment (dans la vidéo source coupée) où la fiche s'affiche
  --musique F --volume-musique dB : musique du dossier Musiques (sinon aucune musique ajoutée).
                          Par défaut -16 dB sans voix ; -22 dB quand le son d'origine est gardé.
  Musique + voix (--garder-son --musique) : la musique reste un fond sonore. Elle est baissée
  automatiquement chaque fois que quelqu'un parle (compression déclenchée par la voix), pour ne
  jamais couvrir la présentation.
  --garder-son / --volume-source dB : son d'origine (voix) conservé
Produit aussi <sortie>_planche.jpg (12 images réparties) pour le contrôle.
"""
import argparse, math, os, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ICI = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
POL = '/usr/share/fonts/truetype/google-fonts/Poppins-'
OR, BLANC, GRIS, NOIR = (201, 165, 92), (255, 255, 255), (185, 180, 170), (22, 20, 16)
TEL, VILLE, SITE = '06 30 26 06 86', 'Ronchin', 'espaceautomp.fr'


def police(g, t):
    return ImageFont.truetype(POL + g + '.ttf', t)


# ---------- courbes d'animation ----------
def cl(t): return min(max(t, 0.0), 1.0)
def sortie(t): return 1 - (1 - cl(t)) ** 3                      # démarre vite, se pose en douceur
def rebond(t):                                                   # dépasse un peu puis revient (effet « pop »)
    t = cl(t); c = 1.70158 * 1.3; return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2
def entre(t, a, d): return (t - a) / d


# ---------- fond et logo ----------
def _fond():
    y, x = np.mgrid[0:H, 0:W]
    d = np.sqrt(((x - W / 2) / W) ** 2 + ((y - H * 0.45) / H) ** 2)
    k = np.clip(d / 0.75, 0, 1)[..., None]
    return ((1 - k) * np.array([50, 45, 36]) + k * np.array([12, 12, 12])).astype(np.float32)


FOND = _fond()
_L = Image.open(os.path.join(ICI, '..', 'ressources', 'logo_blanc.png')).convert('RGBA')
_L = _L.resize((_L.width * 4, _L.height * 4), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 80, 2))
SYMBOLE, MOT = _L.crop((0, 0, 72 * 4, _L.height)), _L.crop((85 * 4, 0, _L.width, _L.height))
ECART = 13 * 4


def fond_anime(t):
    """Fond noir dégradé avec un halo doré qui respire."""
    p = 0.5 + 0.5 * math.sin(t * 2.2)
    y, x = np.ogrid[0:H, 0:W]
    halo = np.exp(-(((x - W / 2) / 420.0) ** 2 + ((y - H * 0.45) / 520.0) ** 2))[..., None]
    return np.clip(FOND + halo * np.array(OR) * (0.10 + 0.06 * p), 0, 255)


def reflet(img, x0, y0, w, h, q):
    """Bande lumineuse qui balaie une zone (q de 0 à 1)."""
    if not 0 < q < 1: return
    band = Image.new('L', (w, h), 0); d = ImageDraw.Draw(band)
    cx = int(-0.3 * w + q * 1.6 * w)
    d.polygon([(cx - 45, h), (cx, 0), (cx + 45, 0), (cx, h)], fill=120)
    sub = img.crop((x0, y0, x0 + w, y0 + h)); a = sub.split()[3]
    lum = Image.new('RGBA', (w, h), (255, 245, 220, 0)); lum.putalpha(Image.fromarray(np.minimum(np.array(band), np.array(a))))
    img.alpha_composite(lum, (x0, y0))


def logo_anime(img, t, cx, cy, largeur, depart=0.0, avec_reflet=True):
    """Le symbole tourne et grossit au centre, puis glisse à gauche pendant que « ESPACE AUTO » se dévoile."""
    t = t - depart
    if t <= 0: return
    dest, img = img, Image.new('RGBA', (W, H))
    ech = largeur / _L.width
    sw, mw, hh = int(SYMBOLE.width * ech), int(MOT.width * ech), int(_L.height * ech)
    total = sw + int(ECART * ech) + mw
    q1 = rebond(entre(t, 0, 0.55)); q2 = sortie(entre(t, 0.45, 0.55))
    s = max(0.01, q1)
    sym = SYMBOLE.resize((max(1, int(sw * s * 1.15)), max(1, int(hh * s * 1.15))), Image.LANCZOS)
    sym = sym.rotate(-150 * (1 - sortie(entre(t, 0, 0.6))), resample=Image.BICUBIC, expand=True)
    a = np.array(sym); a[..., 3] = (a[..., 3] * cl(t / 0.25)).astype('uint8'); sym = Image.fromarray(a)
    sx_centre = cx - sw / 2; sx_final = cx - total / 2
    sx = sx_centre + (sx_final - sx_centre) * q2
    img.alpha_composite(sym, (int(sx + sw / 2 - sym.width / 2), int(cy - sym.height / 2)))
    if q2 > 0:
        mot = MOT.resize((mw, hh), Image.LANCZOS)
        mx = int(sx_final + sw + ECART * ech)                     # position finale du mot
        gauche = max(0, int(sx + sw + ECART * ech) - mx)           # le mot ne passe jamais sous le symbole
        droite = int(mw * q2)
        if droite > gauche:
            img.alpha_composite(mot.crop((gauche, 0, droite, hh)), (mx + gauche, int(cy - hh / 2)))
    if avec_reflet:
        reflet(img, int(cx - total / 2) - 20, int(cy - hh / 2) - 10, total + 40, hh + 20, entre(t, 1.0, 0.6))
    dest.alpha_composite(img)


def texte_c(d, y, s, f, rgba, x_dec=0, espace=0):
    if espace:
        tw = sum(d.textlength(c, font=f) for c in s) + espace * (len(s) - 1); x = (W - tw) / 2 + x_dec
        for c in s: d.text((x, y), c, font=f, fill=rgba); x += d.textlength(c, font=f) + espace
    else:
        d.text(((W - d.textlength(s, font=f)) / 2 + x_dec, y), s, font=f, fill=rgba)


def aa(rgb, q): return tuple(rgb) + (int(255 * cl(q)),)


def pilule(img, cx, cy, s, f, fg, bg, ech=1.0, alpha=1.0, contour=False):
    """Pastille arrondie avec texte, mise à l'échelle autour de son centre."""
    if ech <= 0.02 or alpha <= 0: return
    d0 = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    tw = d0.textlength(s, font=f); bw, bh = int(tw + 80), int(f.size * 1.75)
    p = Image.new('RGBA', (bw, bh)); d = ImageDraw.Draw(p)
    if contour: d.rounded_rectangle((2, 2, bw - 3, bh - 3), radius=bh // 2, outline=bg + (255,), width=4, fill=(0, 0, 0, 110))
    else: d.rounded_rectangle((0, 0, bw - 1, bh - 1), radius=bh // 2, fill=bg + (255,))
    d.text(((bw - tw) / 2, bh / 2 - f.size * 0.62), s, font=f, fill=fg + (255,))
    p = p.resize((max(1, int(bw * ech)), max(1, int(bh * ech))), Image.LANCZOS)
    a = np.array(p); a[..., 3] = (a[..., 3] * cl(alpha)).astype('uint8')
    img.alpha_composite(Image.fromarray(a), (int(cx - p.width / 2), int(cy - p.height / 2)))
    return bw


# ---------- les écrans ----------
def ecran_intro(t, accroche, duree):
    img = Image.fromarray(fond_anime(t).astype('uint8')).convert('RGBA')
    if not accroche:  # intro courte : logo seul
        logo_anime(img, t, W / 2, H * 0.46, 720)
        cq = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(cq)
        q = sortie(entre(t, 0.85, 0.5))
        texte_c(d, H * 0.46 + 70, 'CONSEIL ET VENTE AUTOMOBILE', police('Medium', 32), aa(GRIS, q), espace=int(4 + 14 * (1 - q)))
        img.alpha_composite(cq)
    else:  # logo en haut puis accroche ligne par ligne
        logo_anime(img, t, W / 2, 230, 520)
        lw = int(240 * sortie(entre(t, 0.7, 0.5)))
        if lw > 0: ImageDraw.Draw(img).rounded_rectangle(((W - lw) / 2, 700, (W + lw) / 2, 707), radius=3, fill=OR)
        f = police('Bold', 104 if max(map(len, accroche)) <= 14 else 84)
        for i, s in enumerate(accroche):
            q = rebond(entre(t, 0.85 + 0.18 * i, 0.55)); qa = cl(entre(t, 0.85 + 0.18 * i, 0.25))
            couleur = OR if i >= 1 else BLANC
            calque = Image.new('RGBA', (W, 200)); dc = ImageDraw.Draw(calque)
            texte_c(dc, 20, s, f, aa(couleur, qa))
            e = 0.7 + 0.3 * q
            c2 = calque.resize((int(W * e), int(200 * e)), Image.LANCZOS)
            img.alpha_composite(c2, (int((W - c2.width) / 2), int(760 + i * 140 + 60 * (1 - q) + (200 - c2.height) / 2)))
    sortie_fondu(img, t, duree)
    return img


def sortie_fondu(img, t, duree):
    k = cl((t - (duree - 0.25)) / 0.25)
    if k > 0:
        n = Image.new('RGBA', (W, H), (0, 0, 0, int(120 * k))); img.alpha_composite(n)


def ecran_fin(t, vendu):
    img = Image.fromarray(fond_anime(t + 3).astype('uint8')).convert('RGBA')
    logo_anime(img, t, W / 2, 660, 700)
    cq = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(cq)
    q = sortie(entre(t, 0.7, 0.4)); texte_c(d, 715, 'CONSEIL ET VENTE AUTOMOBILE', police('Medium', 30), aa(GRIS, q), espace=int(3 + 12 * (1 - q)))
    l1, l2 = ('Vous voulez vendre la vôtre ?', "On s'occupe de tout.") if vendu else ('Envie de la découvrir ?', 'Appelez-nous pour un essai.')
    for i, (s, f, c) in enumerate([(l1, police('Bold', 58), BLANC), (l2, police('Medium', 48), OR)]):
        q = sortie(entre(t, 0.95 + 0.15 * i, 0.45))
        texte_c(d, 860 + i * 82 + int(50 * (1 - q)), s, f, aa(c, q))
    img.alpha_composite(cq)
    qp = rebond(entre(t, 1.35, 0.5))
    pouls = 1 + 0.035 * max(0, math.sin((t - 1.9) * 5)) if t > 1.9 else 1
    pilule(img, W / 2, 1130, TEL, police('Bold', 64), NOIR, OR, ech=qp * pouls, alpha=cl(entre(t, 1.35, 0.15)))
    cq = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(cq)
    q = sortie(entre(t, 1.7, 0.5)); texte_c(d, 1240 + int(30 * (1 - q)), f'{VILLE}  ·  {SITE}', police('Medium', 44), aa(BLANC, q))
    img.alpha_composite(cq)
    return img


def calque_fiche(t, a):
    """Fiche du véhicule en bas de l'écran. t = temps depuis l'apparition."""
    D = a.fiche_duree; img = Image.new('RGBA', (W, H))
    if t < 0 or t > D: return None
    out = sortie(entre(t, D - 0.45, 0.45))          # 0 -> 1 pendant la sortie
    dy = int(260 * out ** 2); al = 1 - out
    # dégradé bas
    hg = 700; g = np.zeros((hg, W, 4), np.uint8); g[..., 3] = (np.linspace(0, 235, hg) ** 1.0)[:, None] * cl(t / 0.3) * al
    img.alpha_composite(Image.fromarray(g), (0, H - hg))
    cq = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(cq)
    y0 = H - 560 + dy
    # trait doré qui s'allonge
    lw = int(160 * sortie(entre(t, 0.05, 0.4))); d.rounded_rectangle(((W - lw) / 2, y0, (W + lw) / 2, y0 + 6), radius=3, fill=aa(OR, al))
    # modèle : dévoilement de gauche à droite
    fm = police('Bold', 72 if len(a.modele) <= 20 else 60)
    cm = Image.new('RGBA', (W, 110)); texte_c(ImageDraw.Draw(cm), 0, a.modele, fm, aa(BLANC, al))
    v = int(W * sortie(entre(t, 0.1, 0.5)))
    if v > 0: img.alpha_composite(cm.crop((0, 0, v, 110)), (0, y0 + 30))
    q = sortie(entre(t, 0.35, 0.4))
    if a.version: texte_c(d, y0 + 125 + int(25 * (1 - q)), a.version, police('Medium', 48), aa(OR, q * al))
    img.alpha_composite(cq)
    # prix (pop) ou tampon VENDUE
    yp = y0 + 265
    if a.vendu:
        e = 1.6 - 0.6 * sortie(entre(t, 0.55, 0.35)); qa = cl(entre(t, 0.55, 0.2))
        pilule(img, W / 2, yp, 'VENDUE', police('Bold', 66), NOIR, OR, ech=e, alpha=qa * al)
    elif a.prix:
        pilule(img, W / 2, yp, a.prix, police('Bold', 70), NOIR, OR, ech=rebond(entre(t, 0.55, 0.5)), alpha=cl(entre(t, 0.55, 0.15)) * al)
    # caractéristiques en pastilles, une par une
    infos = [s for s in a.infos.split('|') if s] if a.infos else []
    if infos:
        f = police('Medium', 40); d0 = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
        largeurs = [d0.textlength(s, font=f) + 80 for s in infos]; gap = 18
        lignes, cur = [[]], 0
        for i, wd in enumerate(largeurs):
            if cur + wd > W - 80 and lignes[-1]: lignes.append([]); cur = 0
            lignes[-1].append(i); cur += wd + gap
        for li, idx in enumerate(lignes):
            tot = sum(largeurs[i] for i in idx) + gap * (len(idx) - 1); x = (W - tot) / 2
            for i in idx:
                q = rebond(entre(t, 0.9 + 0.13 * i, 0.45))
                pilule(img, x + largeurs[i] / 2, yp + 140 + li * 95, infos[i], f, BLANC, OR, ech=q, alpha=cl(entre(t, 0.9 + 0.13 * i, 0.15)) * al, contour=True)
                x += largeurs[i] + gap
    return img


def calque_badge(t):
    if t < 0: return None
    img = Image.new('RGBA', (W, H))
    e = 1.8 - 0.8 * sortie(entre(t, 0, 0.35))
    pilule(img, W - 170, 150, 'VENDUE', police('Bold', 46), NOIR, OR, ech=e, alpha=cl(t / 0.15))
    return img


# ---------- vidéo ----------
def remplir(f):
    h, w = f.shape[:2]; s = max(W / w, H / h)
    f = cv2.resize(f, (int(w * s + .5), int(h * s + .5)), interpolation=cv2.INTER_LANCZOS4)
    y0, x0 = (f.shape[0] - H) // 2, (f.shape[1] - W) // 2
    return f[y0:y0 + H, x0:x0 + W]


def poser(fr, calque):
    if calque is None: return fr
    c = np.asarray(calque, dtype=np.float32); al = c[..., 3:] / 255
    return (fr * (1 - al) + c[..., :3] * al)



def photos_vers_clip(chemins, sortie, par_photo=2.6, xf=0.5):
    """Diaporama vertical à partir de photos d'annonce (souvent horizontales) :
    fond = photo floutée et assombrie, photo nette au centre avec un lent zoom et un léger glissement."""
    prep = []
    for c in chemins:
        im = Image.open(c).convert('RGB')
        s = max(W / im.width, H / im.height)
        fond = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
        fond = fond.crop(((fond.width - W) // 2, (fond.height - H) // 2, (fond.width - W) // 2 + W, (fond.height - H) // 2 + H))
        fond = np.asarray(fond.filter(ImageFilter.GaussianBlur(40)), dtype=np.float32) * 0.45
        lw = int(W * 0.94); lh = int(im.height * lw / im.width)
        if lh > H * 0.62: lh = int(H * 0.62); lw = int(im.width * lh / im.height)
        net = im.resize((int(lw * 1.12), int(lh * 1.12)), Image.LANCZOS)
        masque = Image.new('L', (lw, lh), 0); ImageDraw.Draw(masque).rounded_rectangle((0, 0, lw - 1, lh - 1), radius=28, fill=255)
        prep.append((fond, net, masque, lw, lh))
    n_par = int(par_photo * FPS); n_xf = int(xf * FPS)
    total = len(prep) * n_par - (len(prep) - 1) * n_xf
    pr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'veryfast', sortie], stdin=subprocess.PIPE)

    def image(i, k):
        fond, net, masque, lw, lh = prep[i]; q = k / max(1, n_par - 1)
        z = 1.0 + 0.10 * q; sens = 1 if i % 2 == 0 else -1
        w2, h2 = int(lw * z), int(lh * z)
        r = net.resize((w2, h2), Image.BILINEAR)
        dx = int((w2 - lw) / 2 + sens * (w2 - lw) * 0.35 * (q - 0.5))
        r = r.crop((dx, (h2 - lh) // 2, dx + lw, (h2 - lh) // 2 + lh))
        img = Image.fromarray(fond.astype('uint8'))
        cy = int(H * 0.40)
        ombre = Image.new('RGBA', (W, H)); ImageDraw.Draw(ombre).rounded_rectangle(((W - lw) // 2 + 8, cy - lh // 2 + 18, (W + lw) // 2 + 8, cy + lh // 2 + 18), radius=28, fill=(0, 0, 0, 140))
        img = img.convert('RGBA'); img.alpha_composite(ombre.filter(ImageFilter.GaussianBlur(18)))
        img.paste(r, ((W - lw) // 2, cy - lh // 2), masque)
        return np.asarray(img.convert('RGB'), dtype=np.float32)

    for f in range(total):
        i = min(f // (n_par - n_xf), len(prep) - 1); k = f - i * (n_par - n_xf)
        fr = image(i, k)
        if i + 1 < len(prep) and k >= n_par - n_xf:
            al = (k - (n_par - n_xf)) / n_xf; fr = fr * (1 - al) + image(i + 1, k - (n_par - n_xf)) * al
        pr.stdin.write(np.clip(fr, 0, 255).astype('uint8').tobytes())
    pr.stdin.close(); pr.wait()
    return total / FPS

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', default=None); p.add_argument('--photos', default='', help='photos séparées par |, à la place de --source')
    p.add_argument('--par-photo', type=float, default=2.6); p.add_argument('--sortie', required=True)
    p.add_argument('--modele', default=''); p.add_argument('--version', default=''); p.add_argument('--prix', default='')
    p.add_argument('--infos', default=''); p.add_argument('--accroche', default='')
    p.add_argument('--vendu', action='store_true')
    p.add_argument('--debut-source', type=float, default=0); p.add_argument('--fin-source', type=float, default=None)
    p.add_argument('--intro-superposee', action='store_true'); p.add_argument('--fin-superposee', action='store_true')
    p.add_argument('--fiche-debut', type=float, default=1.0); p.add_argument('--fiche-duree', type=float, default=7.0)
    p.add_argument('--musique', default=None); p.add_argument('--volume-musique', type=float, default=None)
    p.add_argument('--garder-son', action='store_true'); p.add_argument('--volume-source', type=float, default=None)
    p.add_argument('--duree-max', type=float, default=90)
    a = p.parse_args()
    if a.photos:
        a.source = a.sortie + '.photos.mp4'
        photos_vers_clip([c for c in a.photos.split('|') if c], a.source, a.par_photo)
        a.garder_son = False; a.volume_source = None
    elif not a.source: raise SystemExit('--source ou --photos obligatoire')
    accroche = [s for s in a.accroche.split('|') if s]
    d_intro = 3.4 if accroche else 1.8
    d_fin = 3.6
    XF = 0.3

    cap = cv2.VideoCapture(a.source); fps_s = cap.get(cv2.CAP_PROP_FPS) or 30
    n_tot = cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps_s
    fin_s = min(a.fin_source or n_tot, n_tot); d_clip = fin_s - a.debut_source
    cap.set(cv2.CAP_PROP_POS_MSEC, a.debut_source * 1000)
    # place de chaque bloc sur la ligne de temps
    t_clip = 0 if a.intro_superposee else d_intro - XF
    t_fin = t_clip + d_clip - (d_fin if a.fin_superposee else XF)
    duree = t_fin + d_fin
    if duree > a.duree_max + 0.05: raise SystemExit(f'Durée {duree:.1f} s > {a.duree_max} s : coupe davantage le rush.')
    tmp = a.sortie + '.video.mp4'
    pr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-preset', 'veryfast', tmp], stdin=subprocess.PIPE)
    etat = {'j': -1, 'f': None}

    def image_clip(tc):
        j = int(tc * fps_s)
        while etat['j'] < j:
            ok, f = cap.read()
            if not ok: break
            etat['j'] += 1; etat['f'] = f
        return remplir(cv2.cvtColor(etat['f'], cv2.COLOR_BGR2RGB)).astype(np.float32)

    n = int(round(duree * FPS)); planche = []; pas = max(1, n // 12)
    for k in range(n):
        t = k / FPS
        fr = None
        if t_clip <= t < t_clip + d_clip:
            tc = t - t_clip
            fr = image_clip(tc)
            fr = poser(fr, calque_fiche(tc - a.fiche_debut, a))
            if a.vendu: fr = poser(fr, calque_badge(tc - (d_intro if a.intro_superposee else 0.4)))
        if t < d_intro:  # intro
            ii = np.asarray(ecran_intro(t, accroche, d_intro).convert('RGB'), dtype=np.float32)
            if fr is None: fr = ii
            else:
                al = 1.0 if t < d_intro - XF else (d_intro - t) / XF
                fr = fr * (1 - al) + ii * al
        if t >= t_fin:  # fin
            ff = np.asarray(ecran_fin(t - t_fin, a.vendu).convert('RGB'), dtype=np.float32)
            al = cl((t - t_fin) / XF)
            fr = ff if fr is None else fr * (1 - al) + ff * al
        fr = np.clip(fr, 0, 255).astype('uint8')
        if k % pas == 0 and len(planche) < 12: planche.append(cv2.resize(fr, (270, 480)))
        pr.stdin.write(fr.tobytes())
    pr.stdin.close(); pr.wait(); cap.release()

    # son
    entrees, filtres, mix = ['-i', tmp], [], []
    if a.garder_son or a.volume_source is not None:
        vs = a.volume_source if a.volume_source is not None else 0
        entrees += ['-ss', str(a.debut_source), '-t', str(d_clip), '-i', a.source]
        ms = int(t_clip * 1000)
        voix = a.musique is not None
        filtres.append(f'[1:a]volume={vs}dB,afade=t=in:d=0.25,afade=t=out:st={max(0, d_clip - 0.4)}:d=0.4,adelay={ms}|{ms},apad'
                       + (',asplit=2[s][cle]' if voix else '[s]')); mix.append('[s]')
    if a.musique:
        voix = bool(mix)
        vm = a.volume_musique if a.volume_musique is not None else (-22 if voix else -16)
        i = 2 if voix else 1
        entrees += ['-i', a.musique]
        base = f'[{i}:a]atrim=0:{duree},asetpts=PTS-STARTPTS,aresample=44100,aformat=channel_layouts=stereo,volume={vm}dB,afade=t=in:d=0.4,afade=t=out:st={duree - 2}:d=2'
        if voix:  # fond sonore : la musique s'efface quand la voix est présente
            filtres.append(base + '[mb]')
            filtres.append('[cle]aresample=44100,aformat=channel_layouts=stereo[cle2]')
            filtres.append('[mb][cle2]sidechaincompress=threshold=0.01:ratio=8:attack=30:release=500:makeup=1:level_sc=4[m]')
        else:
            filtres.append(base + '[m]')
        mix.append('[m]')
    if not mix:
        entrees += ['-f', 'lavfi', '-t', str(duree), '-i', 'anullsrc=r=44100:cl=stereo']; filtres.append('[1:a]anull[a]')
    elif len(mix) == 1: filtres[-1] = filtres[-1].rsplit('[', 1)[0] + '[a]'
    else: filtres.append(f'{"".join(mix)}amix=inputs={len(mix)}:duration=longest:normalize=0[a]')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *entrees, '-filter_complex', ';'.join(filtres), '-map', '0:v', '-map', '[a]',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-t', f'{duree:.3f}', '-movflags', '+faststart', a.sortie], check=True)
    os.remove(tmp)
    if a.photos: os.remove(a.source)
    while len(planche) % 6: planche.append(np.zeros_like(planche[0]))
    pl = np.vstack([np.hstack(planche[i:i + 6]) for i in range(0, len(planche), 6)])
    Image.fromarray(pl).save(os.path.splitext(a.sortie)[0] + '_planche.jpg', quality=85)
    print(f'OK {a.sortie} {duree:.1f} s')


if __name__ == '__main__':
    main()
