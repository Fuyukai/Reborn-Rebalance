Reborn Rebalance
================

*This mod is built on top of and REQUIRES the All Gens Patch, v8.0.0a.*

This project is two parts:

- A rebalance mod for Pokémon Reborn...
- ... implemented via a transpiler from TOML data into game data and Ruby code.

This project is fully documented; you can find the
`documentation online <https://reborn.sailor.li/>`_.

Currently Rebalanced
--------------------

- Pokémon species, based on several data sources:

  * The base source for rebalances is Pokémon Blaze Black 2 Redux (v1.4.0) by Drayano and AphexCubed.
    This is used for the Generation 1-5 Pokémon.
  * Then, Pokémon Photonic Sun by Buffel Salt is used for the Generation 6-7 Pokémon.
  * Finally, my own tweaks are used on top of the base tweaks.

- A small number of moves. See the list above.

- Most gym teams and other major boss teams, excluding most post-game teams.

  * Notably, a lot of boss teams have been moved up to the level cap instead of sitting three to
    four levels below it. 

- A small amount of encounter table tweaks.

Why?
----

dragon/fairy altaria. also i gave staraptor 120 spe >:)

Pre-Built Usage
---------------

Pre-built versions are available from the Releases tab of the repository.

1. Download the latest version of the *legacy* Pokémon Reborn, ***not the 19.5 version**.

   ***IF YOU DOWNLOAD THE NON-LEGACY VERSION, THINGS WILL BREAK. DO NOT DOWNLOAD THE NON-LEGACY
   VERSION.***

2. Download the `All-Gen`_ patch, and extract it over Pokémon Reborn. (The pre-patched version will
   work fine).

   This was built on top of version 8.0.0a. **Versions must match!** Otherwise, you will get cryptic
   errors or silent crashes due to trainer teams not matching.

3. Download the `E19 Music Pack`_ and install it over the All-Gen patch. Don't bother with
   ``trainertypes.dat``, it's going to be overwritten in a minute. Don't get the compatibility
   patch with All-Gen either, as once again, it's going to be overwritten in a minute.

   Alternatively, you can rebuild the ``trainer_types.toml`` file yourself so that it references
   Vanilla music.

3. Add any other mods you might want on top, provided that they are compatible with All-Gen Patch.
4. Download a pre-built release, and extract it over your patched Pokémon Reborn.

Customised Usage
----------------

After seeing my balance tweaks, do you want me to kill myself? That's fine, you can customise this
mod easily.

.. highlight:: fish

1. Clone the repository::

    git clone https://github.com/Fuyukai/Reborn-Rebalance.git

2. Install with PDM::

    cd Reborn-Rebalance; pdm install

3. Customise the files in ``data/`` has you see fit.

3. Transpile the data into Reborn's format::

    pdm run into-pbs ./data ./build

4. Copy everything inside ``./build`` to your Reborn directory::

    cp -rv ./build/* ~/Games/Reborn  # or whatever

5. (Optional) Generate the web documentation::

    pdm run build-web \
        --crop-regular-sprites --crop-form-sprites --render-maps \  # first time only
        --game-dir <path to Reborn directory> \
        ./data ./templates ./website

6. Load the game into Debug mode and run "Compile All Data".

Rebuilding Data
---------------

You may wish to import a different set of data into the system; for example, if you're developing
another major content mod you can use my web view system in order to get a nice documentation 
website.

.. code-block:: fish

    pdm run into-toml <path to your Reborn directory> <path to new data directory>

This can successfully parse the data from a clean Reborn 19.17 installation, as well as all All-Gen
installations up to version 8.0. Other mods are not guarenteed to work or import correctly; if
the PBS files are successfully ingested by the game, please open an issue and I'll adjust the
parsing code.

You'll need to import the forms manually or copy ``data/forms/`` into your data directory. (Make 
sure to remove the ``data/forms/megas/custom`` directory too to remove the All-Gen custom forms;
there's a handful scattered around the other files as well. Sorry.). 

If you have your own forms, you need to write them out manually; a lot of this is automated, 
but you'll need to explicitly write out the differences between the forms and the base Pokémon 
yourself. 

Future Plans
------------

- More boss tweaks, especially post-game.

- Add more events for freshly rebalanced Pokémon.

- Add the ability to directly compile into the game formats, instead of requiring the game to
  recompile it.

  * The Essentials """compiler""" works in one of two ways: either generating a bunch of Ruby
    code, exec()ing it, and marshalling the generated classes; or by creating some lists/dicts
    and marshalling those.

    For either way, writing direct code generation probably isn't too hard and is a future
    priority.

- Add the ability to splice events into the game code without needing to use the RPG Maker editor.

- Add support for Rejuvenation and Desolation.

  * I haven't actually *played* through either of these games so I don't know how to even
    rebalance them (or, hell, how internally unbalanced they are anyway). On the other hand,
    I've played through Reborn ~~three~~ ~~five~~ *SIX* times, so I know what I'm doing here.

Licence
-------

Most of the project is licenced under the GPL, version 3.0 or later.

The overwritten maps are licenced under the "it's complicated" licence. I won't get mad at you,
but the original authors might.

Technical Notes
---------------

- ``rtoml`` is used for reading, ``tomli-w`` is used for writing. Writing is done far less often so
  doesn't need to be fast, and produces better output.

Credits
-------

The Reborn devs - for making this game that I love to hate

Reborn forum user Fervis - for the `All-Gen`_ patch this is based off of

.. _relatively open permissions: https://www.rebornevo.com/pr/gamefaq/#borrow
.. _All-Gen: https://www.rebornevo.com/forums/topic/62201-all-gen-eevee-reborn-custom-megas/
.. _E19 Music Pack: https://www.rebornevo.com/forums/topic/61681-reborn-e19-battle-music-pack/
