# video-notes

[English](README.md) · [繁體中文](README.zh-TW.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · **Français**

Un skill [Claude Code](https://claude.com/claude-code) qui transforme une **URL YouTube
ou un fichier vidéo local** en deux fichiers Markdown : une note des points clés et une
transcription complète horodatée.

Le pipeline Python se charge uniquement de récupérer la transcription. Le résumé, les
points clés et le découpage en chapitres sont rédigés par l'agent après lecture de la
transcription : les notes se lisent donc comme si une personne les avait prises, et non
comme une liste assemblée par un second appel d'API.

## Pourquoi cet outil

- **Zéro dépendance pip.** Sept petits scripts Python utilisant uniquement la bibliothèque
  standard. Les seuls prérequis sont des outils système que vous avez probablement déjà :
  `yt-dlp`, `ffmpeg`, `curl`.
- **Déduplication propre des sous-titres automatiques YouTube.** Les sous-titres
  automatiques défilants sur deux lignes de YouTube répètent presque chaque mot. L'outil
  reconstruit la transcription pour qu'elle se lise d'une traite, sans lignes dupliquées,
  en gérant les chevauchements de type « croissance » et « fenêtre glissante ».
- **Choisit la piste en langue d'origine, pas une traduction automatique.** YouTube
  propose environ 150 pistes de sous-titres traduits automatiquement pour toute vidéo
  sous-titrée automatiquement. L'outil prend délibérément la reconnaissance en langue
  d'origine (sous-titres manuels → manuel d'origine → automatique d'origine) et laisse la
  traduction à l'étape de résumé, où la fidélité est meilleure.
- **Repli sur Whisper en l'absence de sous-titres.** Extrait un audio mono à faible débit,
  le découpe en segments sous la limite de 25 Mo de l'API, transcrit chacun avec `curl`,
  puis recolle les horodatages des segments.

## Prérequis

```bash
brew install yt-dlp ffmpeg   # exemple macOS ; sur d'autres plateformes, utilisez votre gestionnaire de paquets
```

Python 3.9+ (bibliothèque standard uniquement, aucun `pip install` requis).

`OPENAI_API_KEY` est **facultatif** : il n'est lu que lorsqu'une vidéo n'a pas de
sous-titres exploitables et que le repli Whisper s'exécute.

## Installation (en tant que skill Claude Code)

Clonez dans votre répertoire de skills :

```bash
git clone https://github.com/iamvista/video-notes ~/.claude/skills/video-notes
```

Puis invoquez-le dans Claude Code :

```
/video-notes https://youtu.be/<id>
/video-notes ./talk.mp4 --out-dir ./notes --lang fr
```

## Utiliser la CLI directement (sans l'agent)

Le pipeline est une CLI autonome. Il produit `transcript.json` ; vous mettez en forme les
notes comme bon vous semble.

```bash
python3 scripts/cli.py "https://youtu.be/<id>" --lang fr --out ./out
cat ./out/transcript.json
```

Schéma de `transcript.json` :

```json
{
  "meta": {"type": "youtube", "title": "...", "source": "...", "channel": "...", "duration": "MM:SS", "video_id": "..."},
  "transcript_source": "subtitles",
  "segments": [{"start": 8.16, "text": "..."}]
}
```

## Fonctionnement

```
source.py     classe l'argument : URL YouTube ou fichier local
meta.py       récupère titre / chaîne / durée (yt-dlp -J ou ffprobe)
subtitles.py  récupère et déduplique la meilleure piste de sous-titres (voie privilégiée)
audio.py      extrait un mp3 mono et le découpe sous 25 Mo               (repli)
whisper.py    transcrit chaque segment via l'API Whisper                 (repli)
cli.py        orchestre : d'abord les sous-titres, Whisper sinon
transcript.py utilitaires de formatage des horodatages et des liens profonds
```

`SKILL.md` contient les instructions destinées à l'agent pour transformer
`transcript.json` en deux fichiers Markdown.

## Personnaliser la destination de sortie

`--out-dir` est le point de raccordement pour les flux de travail personnels. Pointez-le
vers un coffre de notes et étendez le frontmatter à l'étape 5 de `SKILL.md` selon vos
propres conventions ; le pipeline de transcription reste générique.

## Tests

```bash
python3 -m pytest tests/
```

Des tests unitaires utilisant uniquement la bibliothèque standard couvrent la détection de
la source, la planification du découpage audio, l'analyseur VTT et sa déduplication, la
fusion des décalages Whisper et les utilitaires d'horodatage. Aucun accès réseau requis.

## Licence

MIT — voir [LICENSE](LICENSE).
