"""Real wizard setup and UI input, only for replay scripts' copied saves."""
RESTRICTION_SCENES = {
 'flow-talisman-protean-ready': 'l&wiz\rSShapeshifting\r6\r&%level:1 pre_id protean talisman\rgPcY.....',
 'spell-reason-confused': 'l&wiz\r!Magic Dart\ry&\x04conf\r1000\rIa',
 'flow-talisman-protean': 'l&wiz\r%level:1 pre_id protean talisman\rgPc',
 'flow-talisman-transform': 'l&wiz\r%level:1 pre_id quill talisman\rgPc.....',

 'restriction-teleport-anchor': 'l&wiz\r%pre_id scroll of teleportation\r&\x04dimension anchor\r1000\rxrva',
 'restriction-invisibility': 'l&wiz\r%pre_id potion of invisibility\r&\x04corona\r1000\rxrva',
 'restriction-berserk': 'l&wiz\r%pre_id potion of berserk rage\r&\x04berserk cooldown\r1000\rxrva',
 'restriction-transform-roots': 'l&wiz\r%pre_id potion of lignification\rg qLY&%pre_id scroll of teleportation\rxrva',
 'log-berserk': 'l&wiz\r%pre_id potion of berserk rage\rg qB',
}
RESTRICTION_EXPECTED = {
 'flow-talisman-protean-ready': {'talisman.protean.transforms','log.delay.fixed.c8feee978c02'},
 'spell-reason-confused': {'spell.reason.too_confused','spell.player.casting_useless'},
 'flow-talisman-protean': {'talisman.reason.unstable'},
 'flow-talisman-transform': {'log.delay.fixed.c8feee978c02'},

 'restriction-teleport-anchor': {'player.no_tele.anchor', 'player.no_tele.teleport'},
 'restriction-invisibility': {'item.reason.invisibility.backlit_current'},
 'restriction-berserk': {'item.reason.drink.berserk_recovering'},
 'restriction-transform-roots': {'player.no_tele.roots', 'player.no_tele.teleport'},
 'log-berserk': {'shared.log.berserk.red_vision', 'shared.log.berserk.mighty'},
}
