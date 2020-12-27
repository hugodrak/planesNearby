import numpy as np


def shape_radar_matrix(matrix):
    out = []
    out.append(" -"*len(matrix[0]) + " ")
    for row in matrix:
        str_row = []
        remove = 0
        for col in row:
            if col == 9999:
                val = "웃"
                remove += 1
            elif col == 9998:
                val = "A"
            elif col > 0:
                val = str(col)
                if len(val) > 1:
                    remove += len(val) - 1
            else:
                if remove > 0:
                    remove -= 1
                    val = ""
                else:
                    val = " "
            str_row.append(val)
        out.append("|" + " ".join(str_row) + "|")
    out.append(" -"*len(matrix[0]) + " ")
    return out


def print_matrix_lines(radar_lines, height_lines):
    lines = max([len(radar_lines), len(height_lines)])
    offset = len(radar_lines) - len(height_lines)
    for r_i in range(lines):
        if r_i+offset < 0:
            print(" "*len(radar_lines[0]) + height_lines[r_i])
        elif r_i < offset:
            print(radar_lines[r_i])
        else:
            if offset >= 0:
                print(radar_lines[r_i] + height_lines[r_i-offset])
            else:
                print(radar_lines[r_i+offset] + height_lines[r_i])


def get_index(bbox, res, plane, shape):
    if bbox[1] < plane[0] < bbox[0] and bbox[2] < plane[1] < bbox[3]:
        row = int(abs(bbox[0]-plane[0])//res)
        col = int(abs(plane[1]-bbox[2])//res)
        if row >= shape[0] or col >= shape[1]:
            return None
        return row, col
    else:
        return None


def draw_radar(bbox_raw, my_pos, planes_pos, airports, planes, res=0.09):
    bbox = [float(val) for val in bbox_raw.split(",")]

    rows = int(abs(bbox[0]-bbox[1])//res)
    columns = int(abs(bbox[2]-bbox[3])//res)
    matrix = np.full((rows, columns), 0, dtype=int)
    shape = matrix.shape

    for plane in planes_pos:
        ppos = get_index(bbox, res, plane, shape)
        if ppos:
            row, col = ppos[0], ppos[1]
            matrix[row][col] = plane[2]

    for airport in airports:
        ap_pos = get_index(bbox, res, airport, shape)
        if ap_pos:
            row, col = ap_pos[0], ap_pos[1]
            matrix[row][col] = 9998

    fig_pos = get_index(bbox, res, my_pos, shape)
    if fig_pos:
        row, col = fig_pos[0], fig_pos[1]
        matrix[row][col] = 9999

    radar_lines = shape_radar_matrix(matrix)
    heigh_lines = height_view(planes)
    print_matrix_lines(radar_lines, heigh_lines)


def shape_height_chart(heights):
    rows = len(heights.keys())
    columns = 3
    for _, val in heights.items():
        if len(val) > columns:
            columns = len(val)

    matrix = np.full((rows, columns), 0, dtype=int)

    keys = list(heights.keys())[::-1]

    for r_i in range(rows):
        ids = heights[keys[r_i]]
        for c_i in range(columns):
            if c_i < len(ids):
                matrix[r_i][c_i] = ids[c_i]
    out = [" FL: IDS"]
    for r_i in range(rows):
        fl = str(int(keys[r_i])*10)
        if len(fl) < 3:
            fl = ("0"*(3-len(fl)))+fl
        line = [f" {fl}-"]
        for column in matrix[r_i]:
            if column == 0:
                line.append(" ")
            else:
                line.append(f" {str(column)}")
        out.append("".join(line))
    return out


def find_nearest_int(table, value):
    i = 0
    for it, t_val in enumerate(table):
        if abs(value-t_val) < abs(value-table[i]):
            i = it
    return table[i]


def height_view(planes):
    # heigh, id , lat, lon
    heights = {}
    heights_list = list(range(8)) + list(range(8, 20, 2)) + list(range(20, 50, 5))
    for h in heights_list:
        heights[h] = []
    for plane in planes:
        rh = float(plane.height/1000)
        heights[find_nearest_int(heights_list, rh)].append(plane.id)

    return shape_height_chart(heights)
