from terminalsize import get_terminal_size
import time

SYMBOLS = {"Blank": " ","VertLine": "─","HorLine": "│","DownLink": "┬","Cross": "┼","UpLink": "┴",
           "RightLink": "├","LeftLink": "┤","LeftTop": "┌", "LeftBottom": "└",
           "RightTop": "┐", "RightBottom": "┘"}


COLORS = {"BLUE": '\033[94m', "GREEN": '\033[92m', "YELLOW": '\033[93m', "RED": '\033[91m',
          "END": '\033[0m', "BOLD": '\033[1m',
          "UNDER": '\033[4m', "MAGENTA": '\033[95m'}

def get_color_string(line, code):
    return COLORS[code] + line + COLORS["END"]


class Boxer:
    def __init__(self):
        self.width, self.height = get_terminal_size()

    def form_box(self, width, height, data):
        matrix = []
        x1, y1 = 0, 0
        x2, y2 = width-1, height-1
        for ri in range(height):
            row = []
            for ci in range(width):
                char = "E"
                if ri == y1:
                    if ci == x1:
                        char = SYMBOLS["LeftTop"]
                    elif ci == x2:
                        char = SYMBOLS["RightTop"]
                    else:
                        char = SYMBOLS["VertLine"]

                elif ri == y2:
                    if ci == x1:
                        char = SYMBOLS["LeftBottom"]
                    elif ci == x2:
                        char = SYMBOLS["RightBottom"]
                    else:
                        char = SYMBOLS["VertLine"]
                elif ci == x1 or ci == x2:
                    char = SYMBOLS["HorLine"]
                elif ci == x1 + 1 and ri == y1 + 1:
                    char = data
                else:
                    char = SYMBOLS["Blank"]


                row.append(char)
            matrix.append(row)
        return matrix

    def form_grid(self, w, h, count):
        matrix = []
        x1, y1 = 0, 0
        x2, y2 = self.width-1, self.height-1
        pad = 0
        cols = x2 // (w+pad)
        rows = count // cols + 1

        temp_data = [0 for x in range(count)]

        box_list = [self.form_box(w, h, str(bi)) for bi in range(count)]
        start = 0
        end = cols
        for ri in range(rows):
            for br in range(h):
                row = []
                for box in box_list[start:end]:
                    row.extend(box[br])
                matrix.append(row)
            start = end
            end += cols
            if end > count:
                end = count

        return matrix

    def draw_grid(self, w, h, count, color=None):
        grid = self.form_grid(w, h, count)
        self.draw(grid, color)

    def draw_box(self, width, height, color=None):
        box = self.form_box(width, height)
        self.draw(box, color)

    def clear(self):
        mat = [[" "*self.width]*self.height]
        self.draw(mat)

    def draw(self, mat, color=None):
        rows = len(mat)
        cols = len(mat[0])
        if rows > self.height or cols > self.width:
            raise ValueError("Specified hight and width is to big!")
        for r in mat:
            if color:
                print(get_color_string("".join(r), color))
            else:
                print("".join(r))



B = Boxer()
#B.draw_box(150,30, "BLUE")
# time.sleep(2)
# B.clear()
B.draw_grid(30, 7, 10)
