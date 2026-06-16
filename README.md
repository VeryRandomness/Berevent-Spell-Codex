IF YOU HAVE ISSUES WITH VIBE-CODING, THIS WAS 100% MADE WITH CLAUDE

You can either download the whole repo or just BereventSpellCodex.exe. If you download the whole repo you can build the .exe yourself using build.bat if you have python installed to PATH.

BEREVENT SPELL CODEX  -  standalone player app
================================================

A self-contained desktop window with:
  - Spell Library      : all SRD spells, search by name/text, filter by
                         level / school / class, full detail view
  - Necklace Generator : pick any attributes and get the glyph + binary
                         necklace live

The glyph and necklace use the same logic as the campaign tracker, so they
match exactly. This app is completely separate - it does not touch or need the
tracker.


BUILDING THE .EXE  (do this once, on a Windows PC)
--------------------------------------------------
PyInstaller can only build a Windows .exe ON Windows, so the exe is produced
here rather than handed over pre-built.

  1. Install Python 3 from https://www.python.org/downloads/
     IMPORTANT: tick "Add python.exe to PATH" in the installer.
  2. Double-click  build.bat
  3. When it finishes, your app is:   dist\BereventSpellCodex.exe

That single .exe is fully portable - copy it anywhere and run it. Players need
nothing installed (no Python, no dependencies).


DISTRIBUTING TO PLAYERS
-----------------------
Just send them  dist\BereventSpellCodex.exe.

First launch notes (normal for any unsigned indie .exe):
  - Windows SmartScreen may say "Windows protected your PC" -> click
    "More info" -> "Run anyway".
  - Some antivirus tools flag PyInstaller one-file exes as a false positive.
    If that happens, allow/whitelist it, or build with --onedir instead of
    one-file (edit the .spec) to reduce flags.


RUNNING FROM SOURCE (optional, for testing without building)
------------------------------------------------------------
  python app.py
(requires Python 3 with Tkinter, which is included in the standard Windows
Python installer.)


FILES
-----
  app.py                 the Tkinter window / UI
  glyph_core.py          necklace generation, SRD mapping, glyph geometry
  data/spells.json       SRD spell list (5e SRD, OGL)
  data/attribute_ordering/*.txt   attribute -> necklace ordering
  BereventSpellCodex.spec PyInstaller build recipe
  build.bat              one-click Windows build


CREDITS
-------
Glyph / necklace system: SpellWriting by GorillaOfDestiny (MIT) -
see data/SPELLWRITING_LICENSE.
Spell data: System Reference Document 5.1 (Open Game License).
