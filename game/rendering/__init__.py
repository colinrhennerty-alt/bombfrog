"""Pixel output for the game: "surface + state -> pixels" only.

Nothing here mutates game state; game.simulation owns that. Modules:
entities (sprites, shadows, debug boxes), ground (gameplay floor),
editor_view (map editor), hud (HUD, menu, game over), tile_geometry
(tile grid math), and assets / isometric_assets (cached image loading).
"""
