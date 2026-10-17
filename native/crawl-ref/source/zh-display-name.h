#pragma once

#include <string>

#include "actor.h"
#include "item-def.h"
#include "zh-message.h"

class monster;
struct monster_info;
class level_id;

// Construct a UI-only argument. canonical always retains the engine's English
// name; localized is assembled from semantic fields and exact glossary hits.
ZhArg zh_monster_arg(const std::string &key, const monster &mon,
                     description_level_type desc = DESC_THE);
ZhArg zh_monster_info_arg(const std::string &key, const monster_info &info,
                          description_level_type desc = DESC_THE);
ZhArg zh_item_arg(const std::string &key, const item_def &item,
                  description_level_type desc = DESC_A);
// Type-derived singular base for tutorial/action grammar, without an article,
// quantity, enchantment, brand or equipment suffix.
ZhArg zh_item_base_arg(const std::string &key, const item_def &item);
ZhArg zh_actor_arg(const std::string &key, const actor *who,
                   description_level_type desc = DESC_THE);
ZhArg zh_monster_type_arg(const std::string &key, monster_type type);
ZhArg zh_place_arg(const std::string &key, const level_id &place);

std::string zh_monster_display(const monster &mon,
                               description_level_type desc = DESC_THE);
std::string zh_item_display(const item_def &item,
                            description_level_type desc = DESC_A);

// UI snapshots for operation logs: quantity is the amount moved, not the stack
// left afterwards; menu colours remain engine control strings.
ZhArg zh_item_quantity_arg(const std::string &key, const item_def &item, int quantity,
                          description_level_type desc = DESC_A);
ZhArg zh_item_menu_arg(const std::string &key, const item_def &item,
                      description_level_type desc = DESC_A);
