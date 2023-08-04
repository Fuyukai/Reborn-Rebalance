Reborn Rebalance
================

*This mod is built on top of and REQUIRES the All Gens Patch, v3.5.0a.*

This project is two parts:

- A rebalance mod for Pokémon Reborn...
- ... implemented via a 🏳️‍⚧️piler from TOML data into Essentials PBS (2010 ver) and Ruby code.

This project is fully documented; you can find the
`documentation online <https://reborn.veriny.tf/>`_.

Currently Rebalanced
--------------------

- Pokémon species, based on several data sources:

  * The base source for rebalances is Pokémon Blaze Black 2 Redux (v1.4.0) by Drayano and AphexCubed.
    This is used for the Generation 1-5 Pokémon.
  * Then, Pokémon Photonic Sun by Buffel Salt is used for the Generation 6-7 Pokémon.
  * Finally, my own tweaks are used on top of the base tweaks.

- A small number of moves. See the list above.

Why?
----

dragon/fairy altaria. also i gave staraptor 120 spe >:)

Pre-Built Usage
---------------

Pre-built versions are available from the Releases tab of the repository.

1. Download Pokémon Reborn v19.16 via the updater. (Any download in the last year will be fine.)
2. Download the `All-Gen`_ patch, and extract it over Pokémon Reborn. (The pre-patched version will
   work fine).

   This was built on top of version 3.5.0a, but any version should theoretically work. This mod
   mostly contains new game data and new events, but minimal code changes.

3. Download the `E19 Music Pack`_ and install it over the All-Gen patch. Don't bother with
   ``trainertypes.dat``, it's going to be overwritten in a minute. Don't get the compatibility
   patch with All-Gen either, as once again, it's going to be overwritten in a minute.

3. Add any other mods you might want on top, provided that they are compatible with All-Gen Patch.
4. Download a pre-built release, and extract it over your patched Pokémon Reborn.

Customised Usage
----------------

After seeing my balance tweaks, do you want me to kill myself? That's fine, you can customise this
mod easily. Edit the files in ``data`` as appropriate, then do the following:

.. highlight:: fish

1. Clone the repository:::

    git clone https://github.com/Fuyukai/Reborn-Rebalance.git

2. Install with Poetry:::

    cd Reborn-Rebalance; poetry install

3. (Optional, if you're building the web documentation) Generate the standard sprites:::

    poetry run gen-sprites <path to your installation directory>

4. Transpile the data into Reborn's format:::

    poetry run into-pbs ./data ./build

5. Copy everything inside ``./build`` to your Reborn directory:::

    cp -rv ./build/* ~/Games/Reborn  # or whatever

6. (Optional) Generate the web documentation:::

    poetry run gen-web

Then, you need to run Pokémon Reborn in debug mode (or, with Debug enabled), and run the
``pbCompilePokemonData`` command.

Future Plans
------------

- Add more events for freshly rebalanced Pokémon.
- Add the ability to directly compile into the game formats, instead of requiring the game to
  recompile it.

  * The Essentials """compiler""" works in one of two ways: either generating a bunch of Ruby
    code, exec()ing it, and marshalling the generated classes; or by creating some lists/dicts
    and marshalling those.

    For either way, writing direct code generation probably isn't too hard and is a future
    priority.

  * The latest Reborn `dev blog`_ says that this was the plan internally anyway, but that was
    (as of writing) almost exactly a year ago. It probably won't matter in the end.

- Add the ability to splice events into the game code without needing to use the RPG Maker editor.

  * This also achieves semi-universal compatibility with all future versions of All-Gen Patch,
    as I don't have to worry about overwritten maps not including new changes.

- Add support for Rejuvenation and Desolation.

  * Reborn is a finished project and is (afaik) unlikely to get any other major content updates.
    This makes it generally "safe" for rebalancing, as I don't have to worry about my changes
    suddenly getting undone. I also know roughly how internally unbalanced Reborn is (quite a bit,
    tbh) and where to adjust things.

    Rejuv and Deso are *not* finished, meaning they are subject to future balance changes and
    any work that might be put in

  * Rejuvenation doesn't (yet) use the dict-based form syntax, so the form code generation won't
    work. Everything else should work fine, provided you only copy over the ``pokemon.txt`` and
    ``tms.txt``; or, you can regenerate all of the data from their provided PBS files. You'll
    have to add all of the Aevian forms yourself for now.

  * Desolation doesn't seem to provide PBS files, so you can't re-generate the data based on it.
    If they do, then somebody let me know and I will see about how hard it would be to support it.

  * I haven't actually *played* through either of these games so I don't know how to even
    rebalance them (or, hell, how internally unbalanced they are anyway).

- Hardcode the paths less and split the project out into a general "Reborn-engine transpiler"
  project and a "Reborn-only rebalance" project.

Licence
-------

This project is licenced under the CC0. You can do whatever you want with it! I don't mind.

Credits
-------

The Reborn devs - for making this game that I love to hate

Reborn forum user Haru,, - for making the `modding guide`_ that I referenced for parts of the transpiler

Reborn forum user Fervis - for the `All-Gen`_ patch this is based off of

GitHub user Solistra - for `rvpacker`_, which I stole the definition of ``Table`` from when writing the map renderer

.. _relatively open permissions: https://www.rebornevo.com/pr/gamefaq/#borrow
.. _dev blog: https://www.rebornevo.com/pr/development/records/hey-whats-going-on-r103/
.. _All-Gen: https://www.rebornevo.com/forums/topic/62201-all-gen-eevee-reborn-custom-megas/
.. _E19 Music Pack: https://www.rebornevo.com/forums/topic/61681-reborn-e19-battle-music-pack/
.. _modding guide: https://www.rebornevo.com/forums/topic/65080-modding-tutorial-reborn-e19/
.. _rvpacker: https://github.com/Solistra/rvpacker