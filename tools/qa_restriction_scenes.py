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

# Template migration batch: real input into fresh disposable fixture copies.
RESTRICTION_SCENES.update({
 'prompt-spell-menu': 'l&wiz\r!Magic Dart\ryZ?',
 'prompt-spell-extra': 'l&wiz\r!Magic Dart\ryZ?I',
 'prompt-spell-aim': 'l&wiz\r!Magic Dart\ryZay',
 'prompt-quiver-menu': 'l&wiz\r!Magic Dart\ryQ',
 'prompt-throw-aim': 'l&wiz\r%pre_id stone q:3\rgFc',
 'terrain-binding': 'l&wiz\r(binding_sigil\rhl',
 'terrain-alarm': 'lh&wiz\r(trap_alarm\rhlh',
 'terrain-zot': 'lh&wiz\r(trap_zot\rhlh',
})
RESTRICTION_EXPECTED.update({
 'prompt-spell-menu': {'spell.prompt.menu.title','spell.prompt.menu.select'},
 'prompt-spell-extra': {'spell.prompt.menu.header.extra'},
 'prompt-spell-aim': {'spell.prompt.target.aim','spell.prompt.target.risk'},
 'prompt-quiver-menu': {'quiver.prompt.menu.title.empty'},
 'prompt-throw-aim': {'quiver.prompt.throw'},
 'terrain-binding': {'movement.confirm.binding_sigil'},
 'terrain-alarm': {'movement.confirm.trap.onto'},
 'terrain-zot': {'movement.confirm.trap.zot','prompt.confirm.typed_answer'},
})

# Target-monster details: wizard input touches only each replay's save copy.
RESTRICTION_SCENES.update({
 'monster-target-equipped': 'l&wiz\rmorc warrior perm_ench:haste; long sword . chain mail . kite shield\rx+',
 'monster-target-undead': 'l&wiz\rmwight perm_ench:slow\rx+',
 'monster-target-spell': 'l&wiz\rmorc warrior perm_ench:haste; long sword . chain mail\r&!Magic Dart\ryZay+',
 'monster-encounter': 'l&wiz\rmorc warrior; long sword . chain mail . kite shield\r.',
})
RESTRICTION_EXPECTED.update({
 'monster-target-equipped': {'target.prompt.describe.monster','target.monster.flag.hasted'},
 'monster-target-undead': {'target.prompt.describe.monster','target.monster.flag.slowed'},
 'monster-target-spell': {'target.prompt.describe.monster','target.monster.flag.hasted'},
 'monster-encounter': {'target.monster.log.encounter'},
})

RESTRICTION_SCENES.update({
 'monster-wound-living': 'l&wiz\rmrat hp:1000\r' + '&zMagic Dart\rf'*4 + 'x+',
 'monster-wound-undead': 'l&wiz\rmwight hp:1000\r&zMagic Dart\rf',
})
RESTRICTION_EXPECTED.update({
 'monster-wound-living': {'target.monster.log.wound'},
 'monster-wound-undead': {'target.monster.log.wound'},
})

RESTRICTION_SCENES['monster-long-detail']='l&wiz\rmorc warrior perm_ench:haste; long sword . chain mail . kite shield\rx+v'
RESTRICTION_EXPECTED['monster-long-detail']={'monster.detail.lore.orc_warrior_current'}

RESTRICTION_SCENES["monster-status-detail"]=RESTRICTION_SCENES["monster-long-detail"]+"!"
RESTRICTION_EXPECTED["monster-status-detail"]={"monster.status_text.asleep","monster.status_text.high_tier_stab"}

# Intrinsic special-monster detail workpackage: all wizard input runs in the
# replay harness's fresh save copy. Hydra covers regeneration, differing action
# energy and amphibious movement; acid blob combines long resistance/body prose.
RESTRICTION_SCENES.update({
 'monster-special-hydra': 'l&wiz\rmhydra\rx+v',
 'monster-special-acid-blob': 'l&wiz\rmacid blob\rx+v',
 'monster-special-jiangshi': 'l&wiz\rmjiangshi\rx+v',
 'monster-special-royal-jelly': 'l&wiz\rmRoyal Jelly\rx+v',
})
RESTRICTION_EXPECTED.update({
 'monster-special-hydra': {'monster.special.regen', 'monster.special.speed.energy',
                         'monster.special.cold_blooded.singular', 'monster.special.habitat.water'},
 'monster-special-acid-blob': {'monster.special.resists.singular',
                             'monster.special.acid_splash.singular', 'monster.special.amorphous.singular'},
 'monster-special-jiangshi': {'monster.special.speed.pauses'},
 'monster-special-royal-jelly': {'monster.special.royal_jelly.damage',
                               'monster.special.royal_jelly.polymorph'},
})

# First encounter + monster shouts: same copied ZhSmoke state, real wizard
# creation followed by normal observation. The first popup's source template is
# platform-specific, so choose -console for PTY and -tiles for local/4K SDL.
RESTRICTION_SCENES.update({
 'encounter-first-console': 'l&wiz\rmorc generate_awake\rx+st20\r',
 'encounter-first-tiles': 'l&wiz\rmorc generate_awake\rx+st20\r',
 'encounter-zero-exp': 'l&wiz\rmplant\r....&mplant\r.',
 # In targeting mode, s invokes the existing wizard (S)hout/(T)alk dialog.
 # Its second s + count asks this copied-save actor to shout exactly once.
 'shout-monster-seen': 'l&wiz\rmorc\rx+ss1\r',
 'shout-monster-animal': 'l&wiz\rmwolf\rx+ss1\r',
 'shout-monster-visual': 'l&wiz\rmjelly\rx+ss1\r',
})
RESTRICTION_EXPECTED.update({
 'encounter-first-console': {'hint.encounter.glyph'},
 'encounter-first-tiles': {'hint.encounter.first.tiles'},
 'encounter-zero-exp': {'hint.encounter.db.hint_seen_zero_exp_mon'},
 'shout-monster-seen': {'shout.monster.shout_seen.1'},
 'shout-monster-animal': {'shout.monster.howl_seen.1'},
 'shout-monster-visual': {'shout.monster.cap_j.1'},
})

# Unique-monster alert discards queued keys at --more--; wait for the real
# terminal prompt before opening its detail view.
RESTRICTION_FOLLOWUPS["monster-special-royal-jelly"]={"trigger":"--more--", "keys":"x+v"}

# Random speech uses the real wizard talk/shout commands on copied saves.
RESTRICTION_SCENES.update({
 'speech-imp-taunt': 'l&wiz\rmiron imp generate_awake\rx+ss20\r',
 'speech-orc-dialogue': 'l&wiz\rmorc generate_awake\rx+st20\r',
 'speech-sigmund-dialogue': 'l&wiz\rmSigmund\rx+st20\r',
})

for scene, action in [('speech-imp-taunt','x+ss20\r'),('speech-orc-dialogue','x+st20\r'),('speech-sigmund-dialogue','x+st20\r')]:
 RESTRICTION_FOLLOWUPS[scene]={'trigger':'要用手持武器攻击它','keys':' '+action}

RESTRICTION_EXPECTED.update({
 'speech-imp-taunt': {'speech.shout.imp_taunt'},
 'speech-orc-dialogue': {'speech.monspeak.68bf6884b74c8861'},
})

# Item-operation work package: actual commands, a fresh copied ZhSmoke fixture
# for every scene. Wizard item creation is an input path, never log injection.
RESTRICTION_SCENES.update({
 'item-pickup': 'l&wiz\r%pre_id stone q:3\rg',
 'item-stack': 'l&wiz\r%pre_id stone q:3\rg&%pre_id stone q:2\rg',
 'item-drop': 'l&wiz\r%pre_id stone q:3\rgdc\r',
 'item-wield': 'l&wiz\r%pre_id long sword ego:flaming\rgwc',
 'item-unwield': 'w-',
 'item-takeoff': 'Tb.....',
 'item-wear': 'Tb.....',
 'item-gold': 'l&wiz\r%gold q:123\rg',
 'item-quaff': 'l&wiz\r%pre_id potion of might\rgqm',
 'item-read': 'l&wiz\r%pre_id scroll of enchant weapon\rgrwa',
 'item-wear-menu': 'W',
})
RESTRICTION_EXPECTED.update({
 'item-pickup': {'operation.pickup.item_name'},
 'item-stack': {'operation.pickup.stack.merged'},
 'item-drop': {'operation.drop.success'},
 'item-wield': {'operation.equipment.effect.weapon_flame_on'},
 'item-unwield': {'operation.equipment.log.unequip'},
 'item-takeoff': {'equip_finish'},
 'item-wear': {'equip_start','equip_finish'},
 'item-gold': {'operation.pickup.gold.plural'},
 'item-quaff': {'operation.potion.might.fresh'},
 'item-read': {'operation.use.scroll.success','operation.use.weapon.enchant'},
 'item-wear-menu': {'operation.equipment.menu.wear_both'},
})

# A hints-mode door tutorial interrupts the copied fixture's equipment delay.
# Accept the real continuation prompt, then finish the requested operation.
RESTRICTION_FOLLOWUPS['item-takeoff'] = {'trigger':'要继续脱下衣物吗', 'keys':'Y.....'}
RESTRICTION_FOLLOWUPS['item-wear'] = {'trigger':'要继续脱下衣物吗', 'keys':'Y.....Wb.....'}

RESTRICTION_SCENES['item-inventory'] = 'i'
RESTRICTION_EXPECTED['item-inventory'] = {'operation.inventory.category.subtitle.go_to_first'}

# Six-agent batch: complete production templates, independent copied fixtures.
RESTRICTION_SCENES.update({
 'sol61-combat-swiftness': 'l&wiz\rzSwiftness\r',
 'sol61-world-invalid-stairs': 'l&wiz\r\x1bh<',
 'sol61-ability-menu': 'l&wiz\r\x1ba',
 'sol61-conduct-kill': 'l&wiz\rmrat hp:1 generate_awake\r'+'\t'*12,
})
RESTRICTION_EXPECTED.update({
 'sol61-combat-swiftness': {'sol61.combat.swift'},
 'sol61-world-invalid-stairs': {'world.stairs.invalid.up'},
 'sol61-ability-menu': {'character.ability.menu.hints','character.ability.menu.row'},
 'sol61-conduct-kill': {'character.conduct.kill.accepted'},
})
RESTRICTION_FOLLOWUPS['sol61-conduct-kill']={'trigger':'要用手持武器攻击它','keys':' '+'\t'*12}
RESTRICTION_SCENES.update({
 'sol61-unidentified-scroll': 'l&wiz\r%scroll of teleportation\rg',
 'sol61-corpse-floor': 'l&wiz\r%dart slug corpse\rhl',
 'sol61-floor-collection': 'l&wiz\r%pre_id stone q:3\r&%pre_id javelin q:2\rhl',
 'sol61-doll': 'l~-',
})
RESTRICTION_EXPECTED.update({
 'sol61-unidentified-scroll': {'sol61.name.scroll.labelled','operation.pickup.item_name'},
 'sol61-corpse-floor': {'sol61.item.floor.single','sol61.name.corpse.single'},
 'sol61-floor-collection': {'sol61.item.floor.heading','sol61.item.floor.list'},
 'sol61-doll': {'sol61.ui.doll.title','sol61.ui.doll.index','sol61.ui.doll.mode'},
})
