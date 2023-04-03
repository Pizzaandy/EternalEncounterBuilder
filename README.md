# Eternal Encounter Builder
WIP editor for .entities files in Doom Eternal

This is a set of Python scripts designed to be used to quickly modify DOOM Eternal .entities files with a declarative, domain-specific scripting language.

I'll be honest - this codebase used to look a lot better, but it's been bogged down by bad architectural decisions over time.
For anyone interested in using code from this repository, take a look at the following scripts:

oodle.py - place this script in the same location as your oodle .dll or .so to compress/decompress .entities files.

entities_parser.py and entity_tools.py - These are the big ones! Parse entities into python dictionaries, modify them, then convert them back into usable entities in plain text format. entity_tools.py contains a few other helper functions, but frankly I wouldn't recommend using them :)
