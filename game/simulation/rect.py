import math
from dataclasses import dataclass


def _round_half_away_from_zero(value):
    """pygame.Rect's property setters (.center =, .midbottom =, ...) round
    half away from zero (2.5 -> 3, -2.5 -> -3), not Python's round() which
    uses banker's rounding (2.5 -> 2, -2.5 -> -2) — verified empirically
    against pygame.Rect, since this isn't documented behavior."""
    return math.floor(value + 0.5) if value >= 0 else math.ceil(value - 0.5)


@dataclass(frozen=True)
class Rect:
    """Domain-owned axis-aligned box — no pygame dependency.

    Mirrors the subset of pygame.Rect's API game.simulation actually uses,
    so entity/collision logic never needs to import pygame. Rendering
    translates this to a pygame.Rect at the one deliberate ACL boundary
    (Camera.apply_rect).

    Coordinates are truncated to int on construction — matching
    pygame.Rect(x, y, w, h)'s own C-style int cast on direct construction.
    This differs from pygame.Rect's *property setters* (.midbottom = ...,
    .center = ..., .topleft = ...), which round the assigned point instead
    of truncating it — from_midbottom/from_center/moved_topleft below
    round their anchor argument for the same reason before delegating to
    the constructor, so this type reproduces both of pygame.Rect's rules
    rather than only one. Getting this wrong silently shifts hitbox edges
    and collision results at fractional coordinates (verified empirically
    against pygame.Rect: direct construction truncates, e.g. 1.9 -> 1;
    property-setter assignment rounds, e.g. 1.9 -> 2, -1.9 -> -2).
    """

    x: int
    y: int
    width: int
    height: int

    def __post_init__(self):
        object.__setattr__(self, "x", int(self.x))
        object.__setattr__(self, "y", int(self.y))
        object.__setattr__(self, "width", int(self.width))
        object.__setattr__(self, "height", int(self.height))

    @classmethod
    def from_midbottom(cls, mid_x, bottom_y, width, height) -> "Rect":
        mid_x = _round_half_away_from_zero(mid_x)
        bottom_y = _round_half_away_from_zero(bottom_y)
        return cls(mid_x - width / 2, bottom_y - height, width, height)

    @classmethod
    def from_center(cls, center_x, center_y, width, height) -> "Rect":
        center_x = _round_half_away_from_zero(center_x)
        center_y = _round_half_away_from_zero(center_y)
        return cls(center_x - width / 2, center_y - height / 2, width, height)

    @property
    def center(self):
        return (self.x + self.width / 2, self.y + self.height / 2)

    @property
    def centerx(self):
        return self.x + self.width / 2

    @property
    def centery(self):
        return self.y + self.height / 2

    @property
    def midbottom(self):
        return (self.x + self.width / 2, self.y + self.height)

    @property
    def size(self):
        return (self.width, self.height)

    def recentered(self, center_x, center_y) -> "Rect":
        return Rect.from_center(center_x, center_y, self.width, self.height)

    def moved_topleft(self, x, y) -> "Rect":
        return Rect(_round_half_away_from_zero(x), _round_half_away_from_zero(y), self.width, self.height)

    def colliderect(self, other: "Rect") -> bool:
        return (
            self.x < other.x + other.width
            and self.x + self.width > other.x
            and self.y < other.y + other.height
            and self.y + self.height > other.y
        )
