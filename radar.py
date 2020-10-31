import numpy as np

## TODO: add airports within bbox to radar

def print_matrix(matrix):
    print(" -"*len(matrix[0]))
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
            else:
                if remove > 0:
                    remove -= 1
                    val = ""
                else:
                    val = " "
            str_row.append(val)
        print("|" + " ".join(str_row) + "|")
    print(" -"*len(matrix[0]))


def get_index(bbox, res, plane, shape):
    if bbox[1] < plane[0] < bbox[0] and bbox[2] < plane[1] < bbox[3]:
        row = int(abs(bbox[0]-plane[0])//res)
        col = int(abs(plane[1]-bbox[2])//res)
        if row >= shape[0] or col >= shape[1]:
            return None
        return row, col
    else:
        return None


def draw_radar(bbox_raw, my_pos, planes_pos, res=0.09, airports=None):
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
    print_matrix(matrix)
