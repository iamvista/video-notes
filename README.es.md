# video-notes

[English](README.md) · [繁體中文](README.zh-TW.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · **Español** · [Français](README.fr.md)

Un skill de [Claude Code](https://claude.com/claude-code) que convierte una **URL de
YouTube o un archivo de vídeo local** en dos archivos Markdown: una nota con los puntos
clave y una transcripción completa con marcas de tiempo.

La canalización de Python solo se encarga de obtener la transcripción. El resumen, los
puntos clave y la división en capítulos los escribe el agente tras leer la transcripción,
de modo que las notas se leen como si las hubiera tomado una persona, y no como una lista
cosida con una segunda llamada a la API.

## Por qué esta herramienta

- **Cero dependencias de pip.** Siete pequeños scripts de Python que solo usan la
  biblioteca estándar. Lo único que necesitas son herramientas de sistema que
  probablemente ya tengas: `yt-dlp`, `ffmpeg`, `curl`.
- **Eliminación limpia de duplicados en los subtítulos automáticos de YouTube.** Los
  subtítulos automáticos de dos líneas con desplazamiento de YouTube repiten casi cada
  palabra. Esto reconstruye la transcripción para que se lea de una sola vez, sin líneas
  duplicadas, gestionando los formatos de solapamiento de «crecimiento» y de «ventana
  deslizante».
- **Elige la pista en el idioma original, no una traducción automática.** YouTube ofrece
  unas 150 pistas de subtítulos traducidos automáticamente para cualquier vídeo con
  subtítulos automáticos. Esto toma deliberadamente el reconocimiento en el idioma original
  (subtítulos manuales → manual original → automático original) y deja la traducción para
  el paso de resumen, donde la fidelidad es mayor.
- **Respaldo con Whisper cuando no hay subtítulos.** Extrae audio mono de baja tasa de
  bits, lo divide en fragmentos por debajo del límite de 25 MB de la API, transcribe cada
  uno con `curl` y vuelve a unir las marcas de tiempo de los segmentos.

## Requisitos

```bash
brew install yt-dlp ffmpeg   # ejemplo de macOS; en otras plataformas usa tu gestor de paquetes
```

Python 3.9+ (solo biblioteca estándar, sin necesidad de `pip install`).

`OPENAI_API_KEY` es **opcional**: solo se lee cuando un vídeo no tiene subtítulos
utilizables y se ejecuta el respaldo con Whisper.

## Instalación (como skill de Claude Code)

Clónalo en tu directorio de skills:

```bash
git clone https://github.com/iamvista/video-notes ~/.claude/skills/video-notes
```

Luego invócalo en Claude Code:

```
/video-notes https://youtu.be/<id>
/video-notes ./talk.mp4 --out-dir ./notes --lang es
```

## Usar la CLI directamente (sin el agente)

La canalización es una CLI independiente. Genera `transcript.json`; tú das formato a las
notas como prefieras.

```bash
python3 scripts/cli.py "https://youtu.be/<id>" --lang es --out ./out
cat ./out/transcript.json
```

Esquema de `transcript.json`:

```json
{
  "meta": {"type": "youtube", "title": "...", "source": "...", "channel": "...", "duration": "MM:SS", "video_id": "..."},
  "transcript_source": "subtitles",
  "segments": [{"start": 8.16, "text": "..."}]
}
```

## Cómo funciona

```
source.py     clasifica el argumento: URL de YouTube o archivo local
meta.py       obtiene título / canal / duración (yt-dlp -J o ffprobe)
subtitles.py  obtiene y deduplica la mejor pista de subtítulos  (ruta preferida)
audio.py      extrae mp3 mono y lo fragmenta por debajo de 25 MB (respaldo)
whisper.py    transcribe cada fragmento con la API de Whisper    (respaldo)
cli.py        orquesta: primero subtítulos, Whisper si no hay
transcript.py utilidades de formato de marcas de tiempo y enlaces profundos
```

`SKILL.md` contiene las instrucciones para el agente sobre cómo convertir
`transcript.json` en los dos archivos Markdown.

## Personalizar el destino de salida

`--out-dir` es el punto de conexión para flujos de trabajo personales. Apúntalo a un
repositorio de notas y amplía el frontmatter en el paso 5 de `SKILL.md` según tus propias
convenciones; la canalización de transcripción permanece genérica.

## Pruebas

```bash
python3 -m pytest tests/
```

Pruebas unitarias que solo usan la biblioteca estándar y cubren la detección de fuentes,
la planificación de fragmentos de audio, el analizador de VTT y su deduplicación, la unión
de desfases de Whisper y las utilidades de marcas de tiempo. No requieren acceso a la red.

## Licencia

MIT — consulta [LICENSE](LICENSE).
