from tkinter import *
import time
from planes_backend import Backend
window = Tk()

window.title("PlanesNearby")

header = Label(window, text='Hello')
header.grid(column=0, row=0)

planes = [["SAS", "abc", "20kn"], ["NORW", "cde", "40kn"], ["lufth", "grf", "13kn"]]
plane_labels = []
col = 0
for plane in planes:
    v = StringVar()
    v.set(f"{plane[0]}\n{plane[2]}")
    plane_label = Label(window, textvariable=v)
    plane_label.grid(column=col, row=1)
    col += 1
    plane_labels.append([plane_label, v])

back = Backend()


def clock():
    back.iterate()
    keys = list(back.planes.keys())
    string = back.planes[keys[0]].speed
    plane_labels[2][1].set(string)
    plane_labels[2][0].after(1000, clock)


clock()
window.mainloop()



