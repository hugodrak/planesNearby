import platform
from terminalsize import get_terminal_size
import time

block_width = 30
columns, rows = get_terminal_size()
blocks_wide = int(columns) // block_width

current_os = platform.system()


def get_color(code):
    colors = {"B": '\033[94m', "G": '\033[92m', "W": '\033[93m', "F": '\033[91m',
              "END": '\033[0m', "BOLD": '\033[1m',
              "UNDER": '\033[4m', "M": '\033[95m'}
    return colors[code]


def add_margin(data_str, length, sign):
    if len(data_str) > length:
        data_str = data_str[:length]
    return data_str.center(length, sign)


def print_blocks(blocks):
    str_blocks = []
    for block in blocks:
        template = "{title}\n{data}\n{bottom}"
        if len(block) > 1:
            data_list = []
            for val in block[1:]:
                val = str(val)
                if "$" in val:
                    val_split = val.split("$")
                    if current_os == "Windows":
                        data_list.append('|' + add_margin(val_split[0], block_width - 2, " ") + '|')
                    else:
                        color = get_color(val_split[1])
                        data_list.append(
                            f'|{color}' + add_margin(val_split[0], block_width - 2, " ") +
                            f'{get_color("END")}|')
                else:
                    data_list.append('|' + add_margin(val, block_width - 2, " ") + '|')

            data = "\n".join(data_list)
        else:
            data = '|' + add_margin("", block_width - 2, " ") + '|'
        info = {"title": add_margin(str(block[0]), block_width, "_"),
                "data": data,
                "bottom": add_margin("", block_width, "-")}
        str_blocks.append(template.format(**info))

    cols = [[] for _ in range(blocks_wide)]

    for i, block in enumerate(str_blocks):
        block_rows = block.split("\n")
        for br in block_rows:
            cols[i % blocks_wide].append(br)
    rows = []
    for col in cols:
        rows.extend([[] for r in range(1 + len(col) - len(rows)) if r > 0])
        for i, item in enumerate(col):
            rows[i].append(item)
    print("\n".join([" ".join(r) for r in rows]))


def print_stats(prev, limit, val, signs, unit, var, max_val=None):
    delta = prev - val
    if max_val:
        if abs(prev - val) > max_val // 2:
            if val < prev:
                delta = -(max_val - abs(val - prev))
            else:
                delta = (max_val - abs(val - prev))
        else:
            delta = prev - val

    # if abs(delta) > limit:
    p_delta = abs(round(delta, 2))
    if type(val) == int:
        val = format(val, ",d")

    if delta < -0.01:
        out = f"{var}: {val}{unit} |{signs[1]} {p_delta}{unit}"
    elif delta > 0.01:
        out = f"{var}: {val}{unit} |{signs[0]} {p_delta}{unit}"
    else:
        out = f"{var}: {val}{unit} |{' ' * len(signs[1])} {p_delta}{unit}"

    return out


def status_box(plane_count, weather, position, metar):
    mv = block_width - 3  # max width
    # weather, pos, metar, planes_count
    out = [["Planes", f"✈ Count. {plane_count}",
            f"TIME: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}",
            f"CLOUD FLOOR: {int(weather[0])} ft",
            f"TEMP: {int(weather[1])} °C",
            f"HUMIDITY: {int(weather[2])} %", f"My Pos: {position[0]}, {position[1]}",
            f"{metar[:mv]}",
            f"{metar[mv:mv * 2]}",
            f"{metar[mv * 2:]}"]]
    return out
