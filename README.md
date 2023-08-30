# Eternal Encounter Builder
WIP editor for .entities files in Doom Eternal

This is a set of Python scripts designed to be used to quickly modify DOOM Eternal .entities files with a simple domain-specific scripting language.

As interest in the game slowed down, I added more specific features for the projects I was working on.
For anyone interested in using code from this repository, take a look at the following scripts:

oodle.py - place this script in the same location as your oodle .dll or .so to compress/decompress .entities files.

entities_parser.py and entity_tools.py - These are the big ones! Parse entities into python dictionaries, modify them, then convert them back into usable entities in plain text format. entity_tools.py contains a few other helper functions, but frankly I wouldn't recommend using them :)
