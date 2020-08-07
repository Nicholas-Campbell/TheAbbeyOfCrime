# The Abbey of Crime

*The Abbey of Crime* is an unofficial English translation of the Spanish Amstrad CPC game *La Abadía del Crimen*, which was released by the software house Opera Soft in 1987. *La Abadía del Crimen* is considered to be one of the finest Spanish games to be released for 8-bit computers, but because it included a lot of text in Spanish, it meant that Amstrad CPC fans were unable to fully appreciate its qualities.

In October 2017, a user on the [CPCWiki forum](https://www.cpcwiki.eu/forum/) called khaz initiated a project to translate *La Abadía del Crimen* to English, by patching the original Spanish version of the game. With the assistance of other members of the forum, a translation was completed successfully and was released in late November 2017.

This repository contains a set of Python 3 scripts to help in producing the translated version:

* `extract.py` extracts images and text from an original disk image file of *La Abadía del Crimen*. The images are saved as PNG files and can then be modified using a graphics editor. The text is saved as Z80 assembler source code files, which can be modified using a text editor.
* `patch.py` reads an original disk image file, assembles the modified Z80 assembler source code files, imports the resulting object code binary files and modified images, and saves the patched disk image file and a snapshot for use in Amstrad CPC emulators.
* `config.py` contains filepaths and configuration variables for both the `extract.py` and `patch.py` scripts.
* `cpcdiskimage.py` and `cpcsnapshot.py` are modules containing classes and methods for manipulating and converting Amstrad CPC disk images and snapshots respectively.
* `cpcimage.py` is a module containing functions to enable images to be converted to and from the Amstrad CPC's own format.

There are also some files that are stored in directories:

* `asm` contains the Z80 assembler source code for the patches. The code extracted from *La Abadía del Crimen* is also saved in this directory by default.
* `images` contains modified images for use in *The Abbey of Crime* (the loading screen and in-game status bar). The `unused` subdirectory contains three loading screens that contain the CPCWiki logo that were not used in the final release (see [this post on the CPCWiki forum](https://www.cpcwiki.eu/forum/games/la-abadia-del-crimen-in-english/msg150969/#msg150969)).
* `khaz` contains miscellaneous files that were provided by khaz while the project was in progress, including a complete disassembly of the Amstrad CPC version by Manuel Abadia and English instructions for playing the game.

## Requirements ##

* An original disk image of *La Abadía del Crimen*. For copyright reasons, this repository does not contain any original disk image files, but you can download one by visiting any of the web sites below:
  * [CPC-POWER](https://www.cpc-power.com/)
  * [CPCRulez](https://cpcrulez.fr/)
* [Python 3](https://www.python.org/)
* [Pillow](https://python-pillow.org/) ‒ a Python library for manipulating image files
* [Pasmo](http://pasmo.speccy.org/) ‒ a Z80 assembler. The `config.py` script contains the location of the Pasmo executable file (by default, the same directory as the Python scripts).

## Compiling *The Abbey of Crime*

1. Open a command prompt.
2. Run `extract.py` by typing `python extract.py abadia.dsk`, where `abadia.dsk` is the name of the original disk image file of *La Abadía del Crimen*. This should write Z80 assembler source code files to the `asm` directory and the loading screen and the in-game status bar to the `images` directory. By default, the names of these files end with `_es`, which is the ISO 639-1 code for the Spanish language.
3. You can now modify the source code files and images as appropriate ‒ or you can use the existing modified files in the repository. Look at the `config.py` script to check what filenames to use for the modified files. By default, the names of the modified files end with `_en` ‒ the ISO 639-1 code for the English language. For example, the modified loading screen needs to be saved in the `images` directory as `abadia_loading_screen_en.png`.
4. Run `patch.py` by typing `python patch.py abadia.dsk abbey.dsk abbey.sna`, where `abadia.dsk` is the name of the original disk image file of *La Abadía del Crimen*, `abbey.dsk` is the name of the patched disk image to be saved, and `abbey.sna` is the name of the patched snapshot to be saved. If you wish, you can leave out the filename for either the patched disk image or the patched snapshot, which means that it will not be saved.

You should now be able to play the patched versions by opening an Amstrad CPC emulator.

* If you want to use the patched disk image, open the disk image in drive A of the emulator, then type `|CPM` to load the game.
* If you want to use the patched snapshot, load the snapshot in the emulator and the game should begin automatically.

## Contributors

*The Abbey of Crime* is the result of contributions from several people:

* khaz initiated and led the project and did most of the work to patch the game.
* Alberto Riera (||C|-|E||) provided initial English translations of the in-game messages.
* Nicholas Campbell offered advice on how to patch the game, proofread the English translations of the text, and provided modified versions of the loading screen and status bar.
* Manuel Pazos gave permission for some letters in the fonts in his remake, [*La Abadía del Crimen Extensum*](http://www.abadiadelcrimenextensum.com/), to be used in the introduction and ending sequences.

## Further information

If you want to find out more about this project and the game, or you have played the game and are stuck, please follow some of the links below:

* [The original discussion on the CPCWiki forum about translating *La Abadía del Crimen*](https://www.cpcwiki.eu/forum/games/la-abadia-del-crimen-in-english/msg149893/#msg149893)
* [Announcement on the CPCWiki forum of the release of *The Abbey of Crime*](https://www.cpcwiki.eu/forum/games/la-abadia-del-crimen-the-abbey-of-crime-finally-in-english!/) ‒ the game can be downloaded by following this link
* [*La Abadía del Crimen* article on Wikipedia](https://en.wikipedia.org/wiki/La_Abad%C3%ADa_del_Crimen)
* [Video by It's a Pixel Thing about the history of *La Abadía del Crimen*](https://www.youtube.com/watch?v=MdhsqMFRQMo)
* [Longplay video by Metr81](https://www.youtube.com/watch?v=uDBDAVxwIxo)
* [Longplay video by Retro Danuart](https://www.youtube.com/watch?v=wpCv8OngE1g)
* [Map of the abbey and walkthrough (in Spanish)](https://archive.org/download/World_of_Spectrum_June_2017_Mirror/World%20of%20Spectrum%20June%202017%20Mirror.zip/World%20of%20Spectrum%20June%202017%20Mirror/sinclair/games-maps/a/AbadiaDelCrimenLa.jpg) ‒ originally published in *MicroHobby* magazine № 162
