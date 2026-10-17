#pragma once

#include "zh-message.h"

// Fixed database template lookup, before internal [[key]] references expand.
ZhArg zh_database_source_arg(const std::string &key, const char *context,
                             const std::string &source);
// Description keys and embedded reference keys always remain canonical.
std::string zh_database_description(const std::string &key, const char *context);
