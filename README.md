# Scores

Metadata tooling for the editions stored in this repository.

## CLI commands

- `poetry run extract <edition-dir>` – parse MusicXML files in an edition directory and refresh the edition README front matter.
- `poetry run index [root-dir]` – generate/refresh `index.yaml` files for every composer and the global `editions/index.yaml`, and inject an "Index" table into the corresponding README files.
- `poetry run schema [--format json|yaml] [--out path]` – export the JSON schema for `editions/index.yaml` (defaults to `editions/schema.json`).

## Development

- Install Poetry 1.9+ and run `poetry config virtualenvs.in-project true --global` once to keep the virtualenv in `.venv`.
- Install dependencies with `poetry install`.
- Run the test-suite with `poetry run pytest`.

## Index

| Composer name | Edition title | PDF | MusicXML |
| --- | --- | --- | --- |
| Albert, H | Ach, lasst uns Gott doch einig leben | [PDF](editions/albert-h/arien-1-01/arien-1-01.pdf) | [MusicXML](editions/albert-h/arien-1-01/arien-1-01.musicxml) |
| Albert, H | Ploratus nimios sanctorum funera spernunt | [PDF](editions/albert-h/arien-1-02/arien-1-02.pdf) | [MusicXML](editions/albert-h/arien-1-02/arien-1-02.musicxml) |
| Bach, CPE | An den Schlaf | [PDF](editions/bach-cpe/wq202-h-an-den-schlaf/wq202-h-an-den-schlaf.pdf) | [MusicXML](editions/bach-cpe/wq202-h-an-den-schlaf/wq202-h-an-den-schlaf.musicxml) |
| Bach, CPE | Prüfung am Abend | [PDF](editions/bach-cpe/wq194-7-prufung-am-abend/wq194-7-prufung-am-abend.pdf) | [MusicXML](editions/bach-cpe/wq194-7-prufung-am-abend/wq194-7-prufung-am-abend.musicxml) |
| Carissimi, G | O dulcissimum Mariae nomen | [PDF](editions/carissimi-g/o-dulcissimum/o-dulcissimum.pdf) | [MusicXML](editions/carissimi-g/o-dulcissimum/o-dulcissimum.musicxml) |
| Carissimi, G | O dulcissimum Mariae nomen | [PDF](editions/carissimi-g/o-dulcissimum-gm/o-dulcissimum-gm.pdf) | [MusicXML](editions/carissimi-g/o-dulcissimum-gm/o-dulcissimum-gm.musicxml) |
| Erlebach, PH | An Jammer und Beschwerlichkeit, da fehlt es hier zu keiner Zeit. | [PDF](editions/erlebach-ph/harmonische-freude-2-15/harmonische-freude-2-15.pdf) | [MusicXML](editions/erlebach-ph/harmonische-freude-2-15/harmonische-freude-2-15.musicxml) |
| Erlebach, PH | An Jammer und Beschwerlichkeit, da fehlt es hier zu keiner Zeit. | [PDF](editions/erlebach-ph/harmonische-freude-2-15-Bm/harmonische-freude-2-15-Bm.pdf) | [MusicXML](editions/erlebach-ph/harmonische-freude-2-15-Bm/harmonische-freude-2-15-Bm.musicxml) |
| Erlebach, PH | Des Prahlers Worte, die zwar gleißen, sind nicht stracks echtes Gold zu heißen | [PDF](editions/erlebach-ph/harmonische-freude-2-16/harmonische-freude-2-16.pdf) | [MusicXML](editions/erlebach-ph/harmonische-freude-2-16/harmonische-freude-2-16.musicxml) |
| Erlebach, PH | Die Zeit verkehret, was uns beschweret | [PDF](editions/erlebach-ph/harmonische-freude-1-26/harmonische-freude-1-26.pdf) | [MusicXML](editions/erlebach-ph/harmonische-freude-1-26/harmonische-freude-1-26.musicxml) |
| Erlebach, PH | Die Zeit verkehret, was uns beschweret | [PDF](editions/erlebach-ph/harmonische-freude-1-26-Bm/harmonische-freude-1-26-Bm.pdf) | [MusicXML](editions/erlebach-ph/harmonische-freude-1-26-Bm/harmonische-freude-1-26-Bm.musicxml) |
| Erlebach, PH | Sonata V in E minor (for Violin, Viola da Gamba & Basso Continuo) | [PDF](editions/erlebach-ph/sonata-5/erlebach_ph-sonata_5-v2025-10-21.pdf) | [MusicXML](editions/erlebach-ph/sonata-5/erlebach_ph-sonata_5 - Full score - 01 Adagio.musicxml) |
| Krieger, JP | Einsamkeit, du Qual der Herzen | [PDF](editions/krieger-jp/einsamkeit-du-qual/einsamkeit-du-qual.pdf) | [MusicXML](editions/krieger-jp/einsamkeit-du-qual/einsamkeit-du-qual.musicxml) |
| Krieger, JP | Einsamkeit, du Qual der Herzen | [PDF](editions/krieger-jp/einsamkeit-du-qual-Bb/einsamkeit-du-qual-Bb.pdf) | [MusicXML](editions/krieger-jp/einsamkeit-du-qual-Bb/einsamkeit-du-qual-Bb.musicxml) |
| Landi, S | Superbi colli | [PDF](editions/landi-s/superbi-colli/superbi-colli.pdf) | [MusicXML](editions/landi-s/superbi-colli/superbi-colli-01.musicxml) |
| Melani, A | Quae est ista | [PDF](editions/melani-a/quae-est-ista/quae-est-ista-v3.pdf) | [MusicXML](editions/melani-a/quae-est-ista/quae-est-ista-v3.musicxml) |
| Sweelinck, JP | Ehre sei Gott | [PDF](editions/sweelinck-jp/ehre-sei-gott/ehre-sei-gott.pdf) | [MusicXML](editions/sweelinck-jp/ehre-sei-gott/ehre-sei-gott.musicxml) |


