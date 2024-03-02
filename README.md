# hgtools

Command-line utilities for working with 2003 PS2 game Hungry Ghosts.

Installation:

pip3 install -U git+https://github.com/HungryGhostsFanTranslation/hgtools.git

Sample usage:

hgtools extract-iso ./hungry_ghosts.iso ./extracted/

hgtools unpack ./extracted/data/pack.dat ./unpacked/

hgtools pack ./unpacked/ ./extracted/data/pack.dat

hgtools decompile-hgscript ./unpacked/ ./hgscript/jp/

hgtools compile-hgscript ./hgscript/jp/ ./unpacked/

hgtools dump-graphics ./unpacked ./graphics_out

hgtools patch-graphics ./graphics_replacements unpacked