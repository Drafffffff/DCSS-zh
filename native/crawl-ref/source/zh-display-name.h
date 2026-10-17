#pragma once

#include <string>

#include "actor.h"
#include "item-def.h"
#include "zh-message.h"

class monster;

// Construct a UI-only argument. canonical always retains the engine's English
// name; localized is assembled from semantic fields and exact glossary hits.
ZhArg zh_monster_arg(const std::string &key, const monster &mon,
                     description_level_type desc = DESC_THE);
ZhArg zh_item_arg(const std::string &key, const item_def &item,
                  description_level_type desc = DESC_A);
ZhArg zh_actor_arg(const std::string &key, const actor *who,
                   description_level_type desc = DESC_THE);

std::string zh_monster_display(const monster &mon,
                               description_level_type desc = DESC_THE);
std::string zh_item_display(const item_def &item,
                            description_level_type desc = DESC_A);
