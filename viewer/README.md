# `viewer/` — visualiseur 3D à l'échelle réelle

Page statique (HTML + JS module, Three.js chargé depuis un CDN via
importmap) : aucune installation, aucun backend. Elle affiche un
`model.json` généré par `scripts/build.py` avec les vraies dimensions
(en mètres), une grille au sol de 1 m et une silhouette humaine de 1,75 m
pour juger l'échelle d'un coup d'œil.

## Chargement du modèle

```mermaid
sequenceDiagram
    participant U as Utilisateur
    participant P as Page (index.html?model=...)
    participant V as viewer.js
    participant S as Serveur statique

    alt paramètre ?model= présent
        U->>P: ouvre l'URL avec ?model=../meubles/x/model.json
        P->>V: lit le paramètre
        V->>S: fetch(model.json)
        S-->>V: JSON
    else pas de paramètre (ou file://)
        U->>V: glisse-dépose model.json (ou sélecteur de fichier)
        V->>V: FileReader (lecture locale, pas de réseau)
    end
    V->>V: construit la scène three.js (panneaux, cotes, silhouette)
    V-->>U: rendu 3D interactif (OrbitControls)
```

Le `fetch()` du mode `?model=` échoue sur `file://` (restriction CORS des
navigateurs) : il faut soit un serveur http, soit passer par le
glisser-déposer, qui fonctionne dans tous les cas.

## Utilisation locale

```bash
python3 -m http.server        # à la racine du repo
# http://localhost:8000/viewer/index.html?model=../meubles/etagere_murale/model.json
```

Ou, sans rien lancer : ouvrir `viewer/index.html` directement dans le
navigateur et glisser-déposer un `model.json`.

⚠️ Le paramètre `?model=` doit toujours être un **chemin relatif** à
`viewer/index.html` (ex. `../meubles/<nom>/model.json`), jamais un chemin
commençant par `/`. Un chemin absolu pointerait vers la racine du domaine
et casserait sur GitHub Pages, où le site est servi sous un sous-chemin
(`<utilisateur>.github.io/<repo>/...`) et non à la racine.

## Déploiement (GitHub Pages)

Aucune VM requise : c'est un site 100% statique, déployé automatiquement
par `.github/workflows/pages.yml` à chaque push (voir ce fichier).

1. La première activation nécessite quand même un passage par
   Settings → Pages → Source = **GitHub Actions** (une seule fois ; le
   workflow gère tout le reste ensuite).
2. Le viewer est alors accessible sur :
   `https://<utilisateur>.github.io/<repo>/viewer/index.html?model=../meubles/<nom>/model.json`
3. Les `model.json` doivent être commités dans le repo (ils le sont déjà
   pour `meubles/etagere_murale/` et `meubles/chariot_sous_granit/`) —
   GitHub Pages ne sait pas exécuter le Python de `atelier/`, seulement
   servir les fichiers générés.

D'autres hébergeurs statiques (Netlify, Vercel, Cloudflare Pages)
fonctionnent à l'identique.
