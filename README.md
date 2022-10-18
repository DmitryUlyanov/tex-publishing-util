This small script helps you to prepare a `LaTeX` project for publication e.g. on ArXiv or in a journal. The script is able to do the things you usually do manually before submission:

* __Clean up__: removes files that are not necessary for the project (e.g. outdated graphics, draft `.tex` files, etc.)
* __png -> jpg conversion__: reduces size to satisfy size limits of the submissions 
* __flattening__: creates a single `.tex` document by expanding `\input` and similar macros; copies graphics from subdirs and edit their path in `.tex` doc.

[![asciicast](https://asciinema.org/a/PgZuigtA6H0XphDOmZTpK3c4R.png)](https://asciinema.org/a/PgZuigtA6H0XphDOmZTpK3c4R?speed=3)

**Disclaimer**: The result can be not perfect, so check `diff` files carefully. 
**But** the script mostly works well. 

# Dependencies

- `latexmk`
- `mkjobtexmf`
- `latexpand`
- `python3.6`
- `huepy` : `pip install huepy`
- `glob2` : `pip install glob2`

On Ubuntu, one can install the first three via: `sudo apt-get install texlive-extra-utils latexmk`.

# Usage 

```bash
usage: main.py [-h] --project-dir PROJECT_DIR --main-file MAIN_FILE --save-dir
               SAVE_DIR [--remove-redundant-files] [--remove-comments]
               [--flatten] [--convert-to-jpg] [--quality QUALITY] [--debug]

optional arguments:
  -h, --help            show this help message and exit
  --project-dir PROJECT_DIR
  --main-file MAIN_FILE
  --save-dir SAVE_DIR   Where to save the processed project.
  --remove-redundant-files
                        Clean up redundant files
  --remove-comments     Remove comments within the .tex files.
  --flatten             Converts the project to a one without any folders.
  --convert-to-jpg      Convert image files to jpg.
  --quality QUALITY     Conversion quality.
  --debug               Do not suppress the intermediate output.

```

Basically you do it like this:
```bash
python tex-publishing-util.py --project-dir path/to/dir --main-file main.tex --save-dir out --remove-redundant-files --remove-comments  --flatten --convert-to-jpg
```

Tested __only__ on Ubuntu 16.04, will most likely do not work on Windows without editing (PR is welcome).
