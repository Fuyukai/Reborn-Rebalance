Custom Forms
============

Custom forms in Reborn are a bit messy, but the transpiler (mostly) abstracts them away.

Format
------
A form is a single TOML file in any subdirectory of this directory, with the following keys:

- ``form_mapping`` - a table of int form IDs to form names. The IDs seem to be used internally, and
  also form an index into the sprite file.
- ``custom_init`` - a block of Ruby code used for custom initialisation.
- ``mega_form`` - defines the form used for mega evolutions.

Then, a set of tables with the key ``form.<form name>`` (where form name matches the name in
the form mapping) that override properties of the base species. The valid properties are:

- ``primary_type`` and ``secondary_type``
- ``base_stats``
- ``pokedex_entry``
- ``raw_abilities``
- ``raw_level_up_moves``
- ``evo_data``

The transpiler will convert these into Ruby code and place them into ``MultipleForms.rb``
automatically.

Layout
------

I organised the forms into the provided folder structure:

- ``legends`` for legendaries with differing forms, e.g. the Therian genies.
- ``mythicals`` for similar as above e.g. Shaymin
- ``megas`` for mega evolutions
- ``regional`` for regional forms, divdided into region subfolders (or, placed in the root for meowth lol).
- anything that doesn't cleanly fit into these categories in the root folder.

You don't have to use these folders, but it's convenient.

Sprites
-------

Transpiler sprites and game sprites are unrelated to eachother. The sprite cropping code assumes
a (192\*form_count\*2)x384 image, and will crop them into tiles appropriately.

Gender different forms need to be manually cropped from the ``NUMf.png`` files.

The output name format is ``battler_<4 digit dex number>_<form>{_shiny}.png``.

Notes
-----

Overriding abilities or level-up moves will *overwrite* the entire list, not just add them.

Due to game engine limitations (i.e. TMs are coded backwards) you can't override
the TMs for a Pokémon. All forms can learn the same TMs as the parent species.

Due to game engine silliness ``evo_data`` is a tuple of (int, int, int), unlike the species data.
Additionally, a lot of evolution data related to forms is hardcoded (yay!). As far as I can tell,
these rules apply:

- Common species (e.g. Petilil) changes into different forms => Hardcoded
- Different form evolves into different form (e.g. alolapix into alolatales) => Uses ``evo_data``
