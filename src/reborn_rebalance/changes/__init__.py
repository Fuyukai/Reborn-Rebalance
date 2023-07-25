from reborn_rebalance.changelog import Changelog
from reborn_rebalance.changes import _0_7_0
from reborn_rebalance.pbs.catalog import EssentialsCatalog


def build_changelog(catalog: EssentialsCatalog) -> Changelog:
    log = Changelog(catalog=catalog)

    with log.version("0.7.0") as _070:
        _0_7_0.build_changes(_070)

    return log
