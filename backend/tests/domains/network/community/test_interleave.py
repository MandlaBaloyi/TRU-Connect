"""
Keeping a rail a market rather than one wholesaler's shelf.

TWO PROTECTIONS THAT SOUND LIKE ONE, and the tests keep them apart:

  THE CEILING   how many cards one supplier may hold at all.
  THE RUN       how many may sit next to each other.

A rail can honour the ceiling and still fail the reader -- four cards
from MacMan then four from Lepelle is two shopfronts stapled together,
and the eye sees the block before it counts the cards.

WHAT THESE DEFEND, worst consequence first:

  NO TIER MAY PASS THE PROPORTIONAL CEILING. It is the floor beneath
  the pricing lever (V2_16). If a MAX supplier's absolute cap could
  exceed 40% of a rail, money would have bought domination, which is
  the one thing the whole demand-first design exists to prevent.

  RANKING SURVIVES INTERLEAVING. The incoming order carries the demand
  engine's weights and affordability. A shuffle would solve the layout
  problem by throwing away the reason the rail exists.

  NOTHING IS DROPPED TO AVOID ADJACENCY. The run rule is a layout
  preference; the ceiling is the real protection.
"""
from __future__ import annotations

from src.domains.network.community.algorithms import interleave


def _cards(*owners) -> list:
    """One card per owner, ids in incoming order so ranking is visible."""
    return [{"id": str(i), "supplierId": owner} for i, owner in enumerate(owners)]


def _owners(cards) -> list:
    return [c["supplierId"] for c in cards]


class TestTheProportionalCeilingNoTierCanPass:
    def test_it_binds_a_generous_absolute_cap_down(self):
        """A MAX supplier's 5 becomes 4 on a 12-card rail. THE PRICING
        LEVER STOPS AT THE FLOOR."""
        assert interleave.effective_cap(absolute_cap=5, rail_size=12) == 4

    def test_a_modest_absolute_cap_binds_instead(self):
        """Today everybody is 3, and 3 is below 40% of 12 -- so the
        absolute cap is what actually bites, and the ceiling is holding
        a door nobody is pushing on yet."""
        assert interleave.effective_cap(absolute_cap=3, rail_size=12) == 3

    def test_it_binds_harder_on_a_short_rail(self):
        """2 cards out of 5 from one supplier is already lopsided."""
        assert interleave.effective_cap(absolute_cap=5, rail_size=5) == 2

    def test_it_never_returns_zero(self):
        """A rail so short that 40% rounds to nothing would show
        nothing at all -- trading a lopsided rail for an empty one,
        which is strictly worse and not what the ceiling is for."""
        assert interleave.effective_cap(absolute_cap=3, rail_size=1) == 1
        assert interleave.effective_cap(absolute_cap=3, rail_size=0) >= 1


class TestTheCeilingItself:
    def test_a_dominant_supplier_is_trimmed(self):
        cards = _cards("a", "a", "a", "a", "a", "b", "c")

        kept = interleave.cap_per_supplier(cards, 2)

        assert _owners(kept) == ["a", "a", "b", "c"]

    def test_order_is_preserved(self):
        cards = _cards("a", "b", "a", "c", "a")

        kept = interleave.cap_per_supplier(cards, 3)

        assert [c["id"] for c in kept] == ["0", "1", "2", "3", "4"]


class TestRunsAreBrokenWithoutLosingTheRanking:
    def test_a_block_becomes_alternating(self):
        cards = _cards("a", "a", "a", "b", "b", "c")

        arranged = interleave.break_up_runs(cards)

        for first, second in zip(_owners(arranged), _owners(arranged)[1:]):
            assert first != second, f"two {first} cards adjacent in {_owners(arranged)}"

    def test_the_best_card_still_leads(self):
        """A card only ever moves LATER, and only far enough to break a
        streak -- so whatever ranked first still ranks first."""
        cards = _cards("a", "a", "b")

        arranged = interleave.break_up_runs(cards)

        assert arranged[0]["id"] == "0"

    def test_nothing_is_dropped_when_one_supplier_is_all_there_is(self):
        """The run rule is a layout preference. Dropping stock to avoid
        two adjacent cards would be the layout tail wagging the
        catalogue dog."""
        cards = _cards("a", "a", "a")

        arranged = interleave.break_up_runs(cards)

        assert len(arranged) == 3
        assert _owners(arranged) == ["a", "a", "a"]

    def test_a_trailing_remainder_is_kept(self):
        """Two suppliers, lopsided: b runs out and a's remainder has
        nowhere to interleave with. It still all appears."""
        cards = _cards("a", "a", "a", "a", "b")

        arranged = interleave.break_up_runs(cards)

        assert len(arranged) == 5
        assert _owners(arranged).count("a") == 4


class TestArrangeDoesAllThreeInTheRightOrder:
    def test_cap_then_interleave_then_trim(self):
        cards = _cards("a", "a", "a", "a", "b", "b", "c", "c")

        arranged = interleave.arrange(cards, absolute_cap=3, limit=6)

        assert len(arranged) == 6
        counts = {o: _owners(arranged).count(o) for o in set(_owners(arranged))}
        assert max(counts.values()) <= 3

    def test_a_rail_asked_for_twelve_returns_twelve_when_twelve_exist(self):
        """TRIMMING LAST is what makes this true. Trimming before the
        cap would return fewer than asked whenever a dominant supplier's
        cards were removed after the cut."""
        cards = _cards(*(["a", "b", "c", "d"] * 5))

        arranged = interleave.arrange(cards, absolute_cap=5, limit=12)

        assert len(arranged) == 12

    def test_no_supplier_exceeds_forty_percent_of_the_rail(self):
        """THE PROPERTY THAT MUST HOLD WHATEVER ELSE CHANGES."""
        cards = _cards(*(["a"] * 20 + ["b"] * 3 + ["c"] * 3))

        arranged = interleave.arrange(cards, absolute_cap=10, limit=10)

        assert _owners(arranged).count("a") <= 4

    def test_it_survives_an_empty_rail(self):
        assert interleave.arrange([], absolute_cap=3, limit=12) == []
