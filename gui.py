from tkinter import *
import time
from planes_backend import Backend
window = Tk()

window.title("PlanesNearby")

header = Label(window, text='Hello')
header.grid(column=0, row=0)

#planes = [["SAS", "abc", "20kn"], ["NORW", "cde", "40kn"], ["lufth", "grf", "13kn"]]
back = Backend()
back.iterate()
pids = back.planes.keys()
plane_labels = []
col = 0
for pid in pids:
    plane = back.planes[pid]
    v = StringVar()
    v.set(f"{plane.company}\n{plane.speed}")
    plane_label = Label(window, textvariable=v)
    plane_label.grid(column=col, row=1)
    col += 1
    plane_labels.append([plane_label, v])

def clock():
    back.iterate()
    keys = list(back.planes.keys())
    print("N")
    for i, key in enumerate(keys):
        string = back.planes[key].speed
        plane_labels[i][1].set(string)
        plane_labels[i][0].after(1000, clock)


clock()
window.mainloop()
