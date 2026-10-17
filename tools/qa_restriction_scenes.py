"""Real wizard setup and UI input, only for replay scripts' copied saves."""
RESTRICTION_SCENES = {
 'transform-cycle': 'l&wiz\r%level:1 pre_id quill talisman\rgPc.....Pc.....',

 'miscast-single': 'l&wiz\r!Fire Storm\ryIa',
 'miscast-multiple': 'l&wiz\r!Malign Gateway\ryIa',
 'target-notification': 'l&wiz\r!Magic Dart\ryZay' + 'l'*12,
 'pickup-tutorial': 'l&wiz\r%pre_id stone q:1\r.ll',

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
 'transform-cycle': {'transform.log.sharp_quills_grow_all_over_your_body','transform.log.your_quills_recede_back_into_your_body'},

 'miscast-single': {'spell.miscast.parent.single'},
 'miscast-multiple': {'spell.miscast.parent.multiple'},
 'target-notification': {'target.reason.you_cannot_see_that_place'},
 'pickup-tutorial': {'hints.pickup.first_object'},

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
