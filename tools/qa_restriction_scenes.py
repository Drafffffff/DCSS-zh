"""Real wizard setup and UI input, only for replay scripts' copied saves."""
RESTRICTION_SCENES = {
 'external-passwall': 'l&wiz\rzPasswall\r.',
 'external-inner-flame': 'l&wiz\rzInner Flame\rh.',
 'external-simulacrum': 'l&wiz\rzSimulacrum\rh.',
 'external-crocodile': 'l&wiz\rzSurprising Crocodile\rh.',
 'external-wall-jump': 'l&wiz\r_Wu Jian\r',
 'channel-flame-wave': 'l&wiz\rzFlame Wave\rfhh',
 'channel-bee': 'l&wiz\rmorc\r&zLaunch Clockwork Bee\rfhh',
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
 'external-passwall': {'target.external.passwall.select_wall'},
 'external-inner-flame': {'target.external.inner_flame.unseen'},
 'external-simulacrum': {'target.external.simulacrum.unseen'},
 'external-crocodile': {'target.external.crocodile.no_target'},
 'external-wall-jump': {'target.external.wall_jump.adjacent'},
 'channel-flame-wave': {'spell.channel.reminder.flame_wave','spell.channel.stop.flame_wave'},
 'channel-bee': {'spell.channel.reminder.clockwork_bee','spell.channel.stop.clockwork_bee'},
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

# Religion conversion forces more prompts and discards queued ready() input.
# After accepting those prompts, wait for the completed hints line and settle
# for 0.5 seconds before sending these keys to this copied-save child only.
RESTRICTION_FOLLOWUPS = {
 'external-wall-jump': {
  'trigger': '也可以查看你在神祗眼里的地位和神祗赐给你的神力',
  'keys': '&^60\raahh.',
 },
}
