from tkinter import *
import time
from tkinter import messagebox
import asyncio
from planes_backend import Backend
import threading


back = Backend()


def _asyncio_thread(async_loop):
    async_loop.run_until_complete(do_urls())
    # async_loop.run_forever(do_urls())


def do_tasks(async_loop):
    """ Button-Event-Handler starting the asyncio part. """
    threading.Thread(target=_asyncio_thread, args=(async_loop,)).start()


async def update():
    back.iterate()
    return True


async def do_urls():
    """ Creating and starting 10 tasks. """
    task = asyncio.create_task(update())
    # tasks = [asyncio.create_task(one_url(url))]
    res = await task
    for key in back.planes.keys():
        print(back.planes[key].speed)
        INFO_STRING.set(str(back.planes[key].speed))
        break



def do_freezed():
    messagebox.showinfo(message='Tkinter is reacting.')

def main(async_loop):

    window = Tk()

    window.title("PlanesNearby")
    Button(master=window, text='Asyncio Tasks', command=lambda: do_tasks(async_loop)).pack()
    Button(master=window, text='Freezed???', command=do_freezed).pack()
    Label(master=window, text='Hello').pack()
    global INFO_STRING
    INFO_STRING = StringVar()
    #INFO_STRING.set(f"NONE")
    Label(master=window, textvariable=INFO_STRING).pack()
    window.mainloop()


if __name__ == "__main__":
    async_loop = asyncio.get_event_loop()
    main(async_loop)


