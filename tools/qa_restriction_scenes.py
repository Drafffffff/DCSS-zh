"""Real wizard setup and UI input, only for replay scripts' copied saves."""
RESTRICTION_SCENES = {
 'restriction-teleport-anchor': 'l&wiz\r%pre_id scroll of teleportation\r&\x04dimension anchor\r1000\rxrva',
 'restriction-invisibility': 'l&wiz\r%pre_id potion of invisibility\r&\x04corona\r1000\rxrva',
 'restriction-berserk': 'l&wiz\r%pre_id potion of berserk rage\r&\x04berserk cooldown\r1000\rxrva',
 'restriction-transform-roots': 'l&wiz\r%pre_id potion of lignification\rg qLY&%pre_id scroll of teleportation\rxrva',
 'log-berserk': 'l&wiz\r%pre_id potion of berserk rage\rg qB',
}
RESTRICTION_EXPECTED = {
 'restriction-teleport-anchor': {'player.no_tele.anchor', 'player.no_tele.teleport'},
 'restriction-invisibility': {'item.reason.invisibility.backlit_current'},
 'restriction-berserk': {'item.reason.drink.berserk_recovering'},
 'restriction-transform-roots': {'player.no_tele.roots', 'player.no_tele.teleport'},
 'log-berserk': {'shared.log.berserk.red_vision', 'shared.log.berserk.mighty'},
}
