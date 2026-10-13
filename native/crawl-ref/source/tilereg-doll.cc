#include "AppHdr.h"

#ifdef USE_TILE_LOCAL

#include "tilereg-doll.h"

#include "macro.h"
#include "player.h"
#include "state.h"
#include "stringutil.h"
#include "rltiles/tiledef-player.h"
#include "tilefont.h"
#include "tilepick-p.h"
#include "ui.h"
#include "zh-localization.h"

using namespace ui;

DollEditRegion::DollEditRegion(ImageManager *im, FontWrapper *font) :
    m_font_buf(font),
    m_tile_buf(&im->get_texture(TEX_PLAYER), 17),
    m_cur_buf(&im->get_texture(TEX_PLAYER), 17)
{
    sx = sy = 0;
    dx = dy = 32;
    mx = my = 1;

    m_font = font;

    m_doll_idx = 0;
    m_cat_idx = TILEP_PART_BASE;
    m_copy_valid = false;
}

void DollEditRegion::clear()
{
    m_shape_buf.clear();
    m_tile_buf.clear();
    m_cur_buf.clear();
    m_font_buf.clear();
}

static int _get_next_part(int cat, int part, int inc)
{
    // Can't increment or decrement on show equip.
    if (part == TILEP_SHOW_EQUIP)
        return part;

    // Increment max_part by 1 to include the special value of "none".
    // (Except for the base, for which "none" is disallowed.)
    int max_part = tile_player_part_count[cat] + 1;
    int offset   = tile_player_part_start[cat];

    if (cat == TILEP_PART_BASE)
    {
        offset   = tilep_species_to_base_tile(you.species, you.experience_level);
        max_part = tile_player_count(offset);
    }

    ASSERT(inc > -max_part || inc == -1);

    // Translate the "none" value into something we can do modulo math with.
    if (part == 0)
    {
        part = offset;
        inc--;
    }

    // Valid part numbers are in the range [offset, offset + max_part - 1].
    int ret = (part + max_part + inc - offset) % (max_part);

    if (cat != TILEP_PART_BASE && ret == max_part - 1)
    {
        // "none" value.
        return 0;
    }
    else
    {
        // Otherwise, valid part number.
        return ret + offset;
    }
}

namespace
{
const char *doll_commands[][4] = {
    { "Change parts", "←/→", "Confirm choice", "Enter" },
    { "Change category", "↑/↓", "Copy doll", "Ctrl-C" },
    { "Change doll", "0-9, Shift+←/→", "Paste copied doll", "Ctrl-V" },
    { "Change doll mode", "m", "Randomise doll", "Ctrl-R" },
    { "Save menu", "Esc, Ctrl-S", "Toggle equipment", "*" },
    { "Quit menu", "q, Ctrl-Q", "", "" },
};
const char *doll_categories[TILEP_PART_MAX] = {
    "Base", "Shadow", "Halo", "Ench", "Cloak", "Boots", "Legs", "Body",
    "Gloves", "LHand", "RHandWpn", "RHand", "Hair", "Beard", "Helm", "DrcWing"
};
const char *doll_modes[TILEP_MODE_MAX] = {
    "Current Equipment", "Custom Doll", "Job Defaults"
};
struct DollLayout
{
    int cell, line, gap, left, info, footer, width, height;
    int command_x[4];
};
DollLayout doll_layout(FontWrapper *font)
{
    const auto width = [font](const string &text) {
        return static_cast<int>(font->string_width(text.c_str()));
    };
    DollLayout l;
    l.line = font->char_height() + 4;
    l.gap = max(12, l.line);
    int minimum_cell = font->char_height() * 3 / 2;
    for (const char *label : { "Custom", "Default", "Equip" })
        minimum_cell = max(minimum_cell, (width(zh_translate(label)) + 1) / 2);
    // Tile transforms always use an integer multiple of the original 32px.
    l.cell = max(32, (minimum_cell + 31) / 32 * 32);
    l.left = max(10 * l.cell, width(zh_translate("Doll index %d / %d")) + 6 * static_cast<int>(font->char_width()));
    for (const char *mode : doll_modes)
        l.left = max(l.left, width(zh_translate("Doll Mode: %s")) + width(zh_translate(mode)));
    int category_width = 0;
    for (const char *category : doll_categories)
        category_width = max(category_width, width(zh_translate(category)));
    l.info = category_width + width(" -> : ") + max(width(zh_translate("(show equip)")), width("99999/99999"));
    l.footer = max(7 * l.cell + 4 * l.line, TILEP_PART_MAX * l.line) + l.gap;
    int column_widths[4] = {};
    for (const auto &row : doll_commands)
        for (int col = 0; col < 4; ++col)
            column_widths[col] = max(column_widths[col], width(col % 2 ? string(row[col]) : zh_translate(row[col])));
    int command_width = 0;
    for (int col = 0; col < 4; ++col)
    {
        l.command_x[col] = command_width;
        command_width += column_widths[col] + l.gap;
    }
    l.width = max(l.left + l.gap + l.info, command_width);
    l.height = l.footer + 6 * l.line;
    return l;
}
}

int DollEditRegion::preferred_width() const { return doll_layout(m_font).width; }
int DollEditRegion::preferred_height() const { return doll_layout(m_font).height; }

void DollEditRegion::render()
{
#ifdef DEBUG_TILES_REDRAW
    cprintf("rendering DollEditRegion\n");
#endif
    VColour grey(128, 128, 128, 255);

    m_cur_buf.clear();
    m_tile_buf.clear();
    m_shape_buf.clear();
    m_font_buf.clear();

    // Max items to show at once.
    const int max_show = 9;

    // Layout options (units are in 32x32 squares)
    const int left_gutter    = 0;
    const int item_line      = 0;
    const int edit_doll_line = 2;
    const int doll_line      = 6;
    const DollLayout layout = doll_layout(m_font);
    const int cell = layout.cell;
    dx = dy = cell;

    const int center_x = left_gutter + max_show / 2;

    // Pack current doll separately so it can be drawn repeatedly.
    {
        dolls_data temp = m_dolls[m_doll_idx];
        fill_doll_equipment(temp);
        pack_doll_buf(m_cur_buf, temp, 0, 0, false, false);
    }

    // Draw set of dolls.
    for (int i = 0; i < NUM_MAX_DOLLS; i++)
    {
        int x = left_gutter + i;
        int y = doll_line;

        if (m_mode == TILEP_MODE_LOADING && m_doll_idx == i)
            m_tile_buf.add(TILEP_CURSOR, x, y);

        dolls_data temp = m_dolls[i];
        fill_doll_equipment(temp);
        pack_doll_buf(m_tile_buf, temp, x, y, false, false);

        m_shape_buf.add(x, y, x + 1, y + 1, grey);
    }

    // Draw current category of parts.
    int max_part = tile_player_part_count[m_cat_idx];
    if (m_cat_idx == TILEP_PART_BASE)
    {
        tileidx_t idx = tilep_species_to_base_tile(you.species, you.experience_level);
        max_part = tile_player_count(idx) - 1;
    }

    int show = min(max_show, max_part);
    int half_show = show / 2;
    for (int i = -half_show; i <= show - half_show; i++)
    {
        int x = center_x + i;
        int y = item_line;

        if (i == 0)
            m_tile_buf.add(TILEP_CURSOR, x, y);

        int part = _get_next_part(m_cat_idx, m_part_idx, i);
        ASSERT(part != TILEP_SHOW_EQUIP);
        if (part)
            m_tile_buf.add(part, x, y);

        m_shape_buf.add(x, y, x + 1, y + 1, grey);
    }

    m_shape_buf.add(left_gutter, edit_doll_line, left_gutter + 2, edit_doll_line + 2, grey);
    m_shape_buf.add(left_gutter + 3, edit_doll_line, left_gutter + 4, edit_doll_line + 1, grey);
    m_shape_buf.add(left_gutter + 5, edit_doll_line, left_gutter + 6, edit_doll_line + 1, grey);
    m_shape_buf.add(left_gutter + 7, edit_doll_line, left_gutter + 8, edit_doll_line + 1, grey);
    {
        const char *labels[] = { "Custom", "Default", "Equip" };
        for (int i = 0; i < 3; ++i)
        {
            const string label = zh_translate(labels[i]);
            const float label_x = (left_gutter + 3.5f + 2 * i) * cell
                                - m_font->string_width(label.c_str()) / 2.0f;
            m_font_buf.add(label, VColour::white, label_x,
                           (edit_doll_line + 1) * cell);
        }
    }

    set_transform();
    m_shape_buf.draw();
    m_tile_buf.draw();

    {
        GLW_3VF trans(sx + cell * left_gutter, sy + cell * edit_doll_line, 0);
        GLW_3VF scale(2 * cell, 2 * cell, 1);
        glmanager->set_transform(trans, scale);
    }

    m_cur_buf.draw();

    {
        dolls_data temp;
        temp = m_job_default;
        fill_doll_equipment(temp);
        pack_doll_buf(m_cur_buf, temp, 2, 0, false, false);

        for (unsigned int i = 0; i < TILEP_PART_MAX; ++i)
            temp.parts[i] = TILEP_SHOW_EQUIP;
        fill_doll_equipment(temp);
        pack_doll_buf(m_cur_buf, temp, 4, 0, false, false);

        if (m_mode == TILEP_MODE_LOADING)
            m_cur_buf.add(TILEP_CURSOR, 0, 0);
        else if (m_mode == TILEP_MODE_DEFAULT)
            m_cur_buf.add(TILEP_CURSOR, 2, 0);
        else if (m_mode == TILEP_MODE_EQUIP)
            m_cur_buf.add(TILEP_CURSOR, 4, 0);
    }

    {
        GLW_3VF trans(sx + cell * (left_gutter + 3), sy + cell * edit_doll_line, 0);
        GLW_3VF scale(cell, cell, 1);
        glmanager->set_transform(trans, scale);
    }

    m_cur_buf.draw();

    // Add text.
    const char *part_name = "(none)";
    if (m_part_idx == TILEP_SHOW_EQUIP)
        part_name = "(show equip)";


    {
        GLW_3VF trans(sx, sy);
        GLW_3VF scale(1, 1, 1);
        glmanager->set_transform(trans, scale);
    }

    string item_str = zh_translate(doll_categories[m_cat_idx]) + ": "
                    + (m_part_idx && m_part_idx != TILEP_SHOW_EQUIP
                       ? make_stringf("%d/%d", static_cast<int>(m_part_idx - tile_player_part_start[m_cat_idx] + 1),
                                      tile_player_part_count[m_cat_idx])
                       : zh_translate(part_name));
    float item_name_x = left_gutter * static_cast<float>(cell);
    float item_name_y = (item_line + 1) * static_cast<float>(cell);
    m_font_buf.add(item_str, VColour::white, item_name_x, item_name_y);

    string doll_name;
    doll_name = make_stringf(zh_translate("Doll index %d / %d").c_str(), m_doll_idx, NUM_MAX_DOLLS - 1);
    float doll_name_x = left_gutter * static_cast<float>(cell);
    float doll_name_y = (doll_line + 1) * static_cast<float>(cell);
    m_font_buf.add(doll_name, VColour::white, doll_name_x, doll_name_y);

    doll_name = make_stringf(zh_translate("Doll Mode: %s").c_str(),
                             zh_translate(doll_modes[m_mode]).c_str());
    doll_name_y += layout.line * 2.0f;
    m_font_buf.add(doll_name, VColour::white, doll_name_x, doll_name_y);

    // Add current doll information:
    string info_str;
    float info_x = layout.left + layout.gap;
    float info_y = 0.0f;

    for (int i = 0 ; i < TILEP_PART_MAX; i++)
    {
        int part = m_dolls[m_doll_idx].parts[i];
        int disp = part;
        if (disp)
            disp = disp - tile_player_part_start[i] + 1;
        int maxp = tile_player_part_count[i];

        const string category = zh_translate(doll_categories[i]);
        const string value = part == TILEP_SHOW_EQUIP ? zh_translate("(show equip)")
                           : !part ? zh_translate("(none)")
                           : make_stringf("%d/%d", disp, maxp);
        const string prefix = m_cat_idx == i ? "-> " : "   ";
        info_str = prefix + category + ": " + value;
        m_font_buf.add(info_str, VColour::white, info_x, info_y);
        info_y += layout.line;
    }

    // Measure translated labels and keys independently; whitespace padding is
    // neither a reliable pixel width nor suitable for full-width CJK glyphs.
    for (int row = 0; row < 6; ++row)
        for (int col = 0; col < 4; ++col)
            m_font_buf.add(col % 2 ? string(doll_commands[row][col])
                                       : zh_translate(doll_commands[row][col]), VColour::white,
                           layout.command_x[col], layout.footer + row * layout.line);

    m_font_buf.draw();
    glmanager->reset_transform();
}

int DollEditRegion::handle_mouse(wm_mouse_event &/*event*/)
{
    return 0;
}

class UIDollEditor : public Widget
{
public:
    UIDollEditor(DollEditRegion *_reg) : reg(_reg) {};
    ~UIDollEditor() {};

    virtual void _render() override;
    virtual SizeReq _get_preferred_size(Direction dim, int prosp_width) override;
    virtual void _allocate_region() override;
private:
    DollEditRegion *reg;
};

SizeReq UIDollEditor::_get_preferred_size(Direction dim, int /*prosp_width*/)
{
    if (!dim)
        return { reg->preferred_width(), reg->preferred_width() };
    else
        return { reg->preferred_height(), reg->preferred_height() };
}

void UIDollEditor::_render()
{
    reg->render();
}

void UIDollEditor::_allocate_region()
{
    reg->sx = m_region.x;
    reg->sy = m_region.y;
}

void DollEditRegion::run()
{
    // Initialise equipment setting.
    dolls_data equip_doll;
    for (unsigned int i = 0; i < TILEP_PART_MAX; ++i)
         equip_doll.parts[i] = TILEP_SHOW_EQUIP;

    // Initialise job default.
    m_job_default = equip_doll;
    tilep_race_default(you.species, you.experience_level, &m_job_default);
    tilep_job_default(you.char_class, &m_job_default);

    // Read predefined dolls from file.
    for (dolls_data &doll : m_dolls)
         doll = equip_doll;

    m_mode = TILEP_MODE_LOADING;
    m_doll_idx = -1;

    if (!load_doll_data("dolls.txt", m_dolls, NUM_MAX_DOLLS,
                        &m_mode, &m_doll_idx))
    {
        m_doll_idx = 0;
    }

    bool update_part_idx = true;

    bool done = false;
    auto doll_ui = make_shared<UIDollEditor>(this);

    auto vbox = make_shared<Box>(Widget::VERT);
    vbox->set_cross_alignment(Widget::CENTER);
    auto title = make_shared<Text>(formatted_string("Doll Editor", YELLOW));
    title->set_margin_for_sdl(0, 0, 20, 0);
    vbox->add_child(std::move(title));
    vbox->add_child(doll_ui);
    auto popup = make_shared<ui::Popup>(std::move(vbox));

    popup->on_keydown_event([this, &done, &doll_ui, &update_part_idx](const KeyEvent& ev) {
        const auto key = ev.key();
        command_type cmd = key_to_command(key, KMC_DOLL);

        switch (cmd)
        {
        case CMD_DOLL_QUIT:
            return done = true;
        case CMD_DOLL_RANDOMIZE:
            create_random_doll(m_dolls[m_doll_idx]);
            break;
        case CMD_DOLL_SELECT_NEXT_DOLL:
        case CMD_DOLL_SELECT_PREV_DOLL:
        {
            const int bonus = (cmd == CMD_DOLL_SELECT_NEXT_DOLL ? 1
                                        : NUM_MAX_DOLLS - 1);

            m_doll_idx = (m_doll_idx + bonus) % NUM_MAX_DOLLS;
            update_part_idx = true;
            if (m_mode != TILEP_MODE_LOADING)
                m_mode = TILEP_MODE_LOADING;
            break;
        }
        case CMD_DOLL_SELECT_NEXT_PART:
        case CMD_DOLL_SELECT_PREV_PART:
        {
            const int bonus = (cmd == CMD_DOLL_SELECT_NEXT_PART ? 1
                                        : TILEP_PART_MAX - 1);

            m_cat_idx = (m_cat_idx + bonus) % TILEP_PART_MAX;
            update_part_idx = true;
            break;
        }
        case CMD_DOLL_CHANGE_PART_NEXT:
        case CMD_DOLL_CHANGE_PART_PREV:
            if (m_part_idx != TILEP_SHOW_EQUIP)
            {
                const int dir = (cmd == CMD_DOLL_CHANGE_PART_NEXT ? 1 : -1);
                m_part_idx = _get_next_part(m_cat_idx, m_part_idx, dir);
            }
            m_dolls[m_doll_idx].parts[m_cat_idx] = m_part_idx;
            break;
        case CMD_DOLL_TOGGLE_EQUIP:
            if (m_dolls[m_doll_idx].parts[m_cat_idx] == TILEP_SHOW_EQUIP)
                m_dolls[m_doll_idx].parts[m_cat_idx] = m_part_idx;
            else
                m_dolls[m_doll_idx].parts[m_cat_idx] = TILEP_SHOW_EQUIP;
            break;
        case CMD_DOLL_CONFIRM_CHOICE:
            if (m_mode != TILEP_MODE_LOADING)
                m_mode = TILEP_MODE_LOADING;
            break;
        case CMD_DOLL_COPY:
            m_doll_copy  = m_dolls[m_doll_idx];
            m_copy_valid = true;
            break;
        case CMD_DOLL_PASTE:
            if (m_copy_valid)
                m_dolls[m_doll_idx] = m_doll_copy;
            break;
        case CMD_DOLL_TAKE_OFF:
            m_part_idx = 0;
            m_dolls[m_doll_idx].parts[m_cat_idx] = 0;
            break;
        case CMD_DOLL_TAKE_OFF_ALL:
            for (int i = 0; i < TILEP_PART_MAX; i++)
            {
                switch (i)
                {
                case TILEP_PART_BASE:
                case TILEP_PART_SHADOW:
                case TILEP_PART_HALO:
                case TILEP_PART_ENCH:
                case TILEP_PART_DRCWING:
                    break;
                default:
                    m_dolls[m_doll_idx].parts[i] = 0;
                };
            }
            break;
        case CMD_DOLL_TOGGLE_EQUIP_ALL:
            for (int i = 0; i < TILEP_PART_MAX; i++)
                m_dolls[m_doll_idx].parts[i] = TILEP_SHOW_EQUIP;
            break;
        case CMD_DOLL_JOB_DEFAULT:
            m_dolls[m_doll_idx] = m_job_default;
            break;
        case CMD_DOLL_CHANGE_MODE:
            m_mode = (tile_doll_mode)(((int)m_mode + 1) % TILEP_MODE_MAX);
        default:
            if (key == '0')
                m_doll_idx = 0;
            else if (key >= '1' && key <= '9')
                m_doll_idx = key - '1' + 1;
            else
                break;

            if (m_mode != TILEP_MODE_LOADING)
                m_mode = TILEP_MODE_LOADING;
            ASSERT(m_doll_idx < NUM_MAX_DOLLS);
            break;
        }
        done = cmd == CMD_DOLL_SAVE;
        doll_ui->_expose();
        return true;
    });

    ui::push_layout(std::move(popup), KMC_DOLL);
    while (!done && !crawl_state.seen_hups)
    {
        if (update_part_idx)
        {
            m_part_idx = m_dolls[m_doll_idx].parts[m_cat_idx];
            if (m_part_idx == TILEP_SHOW_EQUIP)
                m_part_idx = 0;
            update_part_idx = false;
        }
        ui::pump_events();
    }
    ui::pop_layout();

    save_doll_data(m_mode, m_doll_idx, &m_dolls[0]);

    // Update player with the current doll.
    switch (m_mode)
    {
    case TILEP_MODE_LOADING:
        player_doll = m_dolls[m_doll_idx];
        break;
    case TILEP_MODE_DEFAULT:
        player_doll = m_job_default;
        break;
    default:
    case TILEP_MODE_EQUIP:
        player_doll = equip_doll;
    }
}

#endif
