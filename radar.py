import numpy as np


def print_matrix(matrix):
    print(" -"*len(matrix[0]))
    for row in matrix:
        str_row = []
        remove = 0
        for col in row:
            if col == 1:
                val = "웃"
                remove += 1
            elif col == 2:
                val = "•"
            else:
                if remove > 0:
                    remove -= 1
                    val = ""
                else:
                    val = " "
            str_row.append(val)
        print("|" + " ".join(str_row) + "|")
    print(" -"*len(matrix[0]))


def get_index(bbox, res, pos, shape):
    if bbox[1] < pos[0] < bbox[0] and bbox[2] < pos[1] < bbox[3]:
        row = int(abs(bbox[0]-pos[0])//res)
        col = int(abs(pos[1]-bbox[2])//res)
        if row >= shape[0] or col >= shape[1]:
            return None
        return row, col
    else:
        return None


def draw_radar(bbox_raw, my_pos, planes_pos, res=0.09):
    bbox = [float(val) for val in bbox_raw.split(",")]

    rows = int(abs(bbox[0]-bbox[1])//res)
    columns = int(abs(bbox[2]-bbox[3])//res)
    matrix = np.full((rows, columns), 0, dtype=int)
    shape = matrix.shape

    pos = get_index(bbox, res, my_pos, shape)
    if pos:
        row, col = pos[0], pos[1]
        matrix[row][col] = 1

    for plane in planes_pos:
        pos = get_index(bbox, res, plane, shape)
        if pos:
            row, col = pos[0], pos[1]
            matrix[row][col] = 2
    print_matrix(matrix)
