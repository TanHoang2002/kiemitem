import logging
from typing import TYPE_CHECKING

from src.item import ASPECT_UPGRADES_LABEL
from src.item.data.affix import Affix, AffixType
from src.item.models import FilterResult, MatchedFilter
from src.settings import AspectFilterType, UnfilteredUniquesType, get_settings

if TYPE_CHECKING:
    from src.item.filter.matching import FilterContext
    from src.item.models import Item

LOGGER = logging.getLogger(__name__)


def _format_num(value: float | None) -> str:
    if value is None:
        return "?"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _format_affix_detail(affix: Affix) -> str:
    """One-line human-readable summary: 'name = value (range min-max) [TYPE]'."""
    parts: list[str] = [affix.name or "(unknown)"]
    if affix.value is not None:
        parts.append(f"= {_format_num(affix.value)}")
    if affix.min_value is not None or affix.max_value is not None:
        parts.append(f"(range {_format_num(affix.min_value)}-{_format_num(affix.max_value)})")
    if affix.type == AffixType.greater:
        parts.append("[GA]")
    elif affix.type == AffixType.tempered:
        parts.append("[tempered]")
    elif affix.type == AffixType.rerolled:
        parts.append("[rerolled]")
    elif affix.type == AffixType.inherent:
        parts.append("[inherent]")
    return " ".join(parts)


class FilterEquipmentMixin:
    def _check_affixes(self: FilterContext, item: Item) -> FilterResult:
        res = FilterResult(keep=False, matched=[])
        if not self.affix_filters:
            return FilterResult(keep=False, matched=[])
        non_tempered_affixes = [affix for affix in item.affixes if affix.type != AffixType.tempered]
        for profile_name, profile_filter in self.affix_filters.items():
            for filter_item in profile_filter:
                filter_name = next(iter(filter_item.root.keys()))
                filter_spec = filter_item.root[filter_name]
                if not self._match_item_type(filter_spec.item_type, item.item_type):  # check item type
                    continue
                if filter_spec.rarities and item.rarity not in filter_spec.rarities:  # check item rarity
                    continue
                if not self._match_item_power(filter_spec.min_power, item.power):  # check item power
                    continue
                if not self._match_greater_affix_count(  # check greater affixes
                    filter_spec.min_greater_affix_count, non_tempered_affixes
                ):
                    continue
                if not self._check_unique_aspects_for_item(item, filter_spec.unique_aspect):
                    continue
                matched_affixes = []
                if filter_spec.affix_pool:
                    matched_affixes = self._match_affixes_count(
                        filter_spec.affix_pool, non_tempered_affixes, filter_spec.min_greater_affix_count
                    )
                    if not matched_affixes:
                        continue
                matched_inherents = []
                if filter_spec.inherent_pool:
                    matched_inherents = self._match_affixes_count(
                        filter_spec.inherent_pool, item.inherent, filter_spec.min_greater_affix_count
                    )
                    if not matched_inherents:
                        continue
                all_matches = matched_affixes + matched_inherents
                match_details = ", ".join(_format_affix_detail(affix) for affix in all_matches)
                LOGGER.info(
                    f"{item.original_name} -- Matched {profile_name}.Affixes.{filter_name} ({len(all_matches)} affixes): {match_details}"
                )
                if filter_spec.unique_aspect:  # show the matched unique aspect
                    LOGGER.info(f"{item.original_name} -- Matched {profile_name}.Affixes.{filter_name}: Unique aspect")
                res.keep = True
                res.matched.append(
                    MatchedFilter(f"{profile_name}.{filter_name}", all_matches, bool(filter_spec.unique_aspect))
                )
        return res

    def _check_aspect_upgrades(self: FilterContext, item: Item) -> FilterResult:
        res = FilterResult(keep=False, matched=[])
        if item.codex_upgrade and self.aspect_upgrade_filters:
            for profile_name, profile_filter in self.aspect_upgrade_filters.items():
                if item.aspect and any(name == item.aspect.name for name in profile_filter):
                    LOGGER.info(f"{item.original_name} -- Matched build-specific aspects that updates codex")
                    res.keep = True
                    res.matched.append(MatchedFilter(f"{profile_name}.{ASPECT_UPGRADES_LABEL}", aspect_match=True))
            if res.keep:
                return res
        if get_settings().general.keep_aspects == AspectFilterType.none or (
            get_settings().general.keep_aspects == AspectFilterType.upgrade and not item.codex_upgrade
        ):
            return res
        LOGGER.info(f"{item.original_name} -- Matched Aspects that updates codex")
        res.keep = True
        res.matched.append(MatchedFilter(ASPECT_UPGRADES_LABEL, aspect_match=True))
        return res

    def _check_global_unique_filter(self: FilterContext, item: Item) -> FilterResult:
        res = FilterResult(keep=False, matched=[])
        if not self.global_unique_filters:
            keep = get_settings().general.handle_uniques != UnfilteredUniquesType.junk
            return FilterResult(keep, [])
        for profile_name, profile_filter in self.global_unique_filters.items():
            for filter_item in profile_filter:
                if item.aspect is None:
                    continue
                if not self._match_item_power(filter_item.min_power, item.power):
                    continue
                if not self._match_greater_affix_count(filter_item.min_greater_affix_count, item.affixes):
                    continue
                if not self._match_item_roll_is_in_percent_range(filter_item.min_percent_of_aspect, item.aspect):
                    continue
                aspect_detail = item.aspect.name or "(unnamed aspect)"
                if item.aspect.value is not None:
                    aspect_detail = f"{aspect_detail} = {_format_num(item.aspect.value)}"
                    if item.aspect.min_value is not None or item.aspect.max_value is not None:
                        aspect_detail += (
                            f" (range {_format_num(item.aspect.min_value)}-{_format_num(item.aspect.max_value)})"
                        )
                affix_detail = ", ".join(_format_affix_detail(a) for a in item.affixes)
                LOGGER.info(
                    f"{item.original_name} -- Matched {profile_name}.GlobalUniques: aspect={aspect_detail}"
                    + (f"; affixes: {affix_detail}" if affix_detail else "")
                )
                res.keep = True
                matched_full_name = f"{profile_name}.{item.aspect.name}"
                if filter_item.profile_alias:
                    matched_full_name = f"{filter_item.profile_alias}.{item.aspect.name}"
                res.matched.append(MatchedFilter(matched_full_name, aspect_match=True))
        return res
