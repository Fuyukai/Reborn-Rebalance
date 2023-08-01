Adding New Pokémon
------------------

This is a quick guide to adding new Pokémon species to the transpiler and thus the game.

First, add a new entry under the ``data/species/<dir>`` directory. Dir can be any arbitrary
directory, as the deserialiser simply globs all folders; but it's recommended that you use a
different one to the provided generations, e.g. ``custom``. The file should be named
``<4-digit dex id>_<name>.toml``.

Then, open it in your editor of choice. You need to fill in the fields with the schema defined in
``pokemon.py``, under ``PokemonSpecies``. Some fields are optional and may be omitted; some fields
are strictly provided for round-tripping with the original PBS input from All-Gen Patch and
should be omitted (``form_names``, ``regional_numbers``, and ``shape``).

You then need to add the battler sprites in a 384x384 4-tile image to the game; you can find
out how elsewhere. Re-run sprite generation to have them show up on the web docs, and finally
re-run PBS generation.