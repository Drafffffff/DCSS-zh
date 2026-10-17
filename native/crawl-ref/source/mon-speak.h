/**
 * @file
 * @brief Functions to handle speaking monsters
**/

#pragma once

#include "mpr.h"

void maybe_mons_speaks(monster* mons);
bool mons_speaks(monster* mons);
bool mons_speaks_msg(monster* mons, const string &msg,
                     const msg_channel_type def_chan = MSGCH_TALK,
                     const bool silence = false);
bool invalid_msg(const monster &mon, string msg);

#include "zh-speech.h"
bool mons_speaks_msg(monster *mon, const ZhSpeech &speech,
                     msg_channel_type channel = MSGCH_TALK, bool silence = false);
