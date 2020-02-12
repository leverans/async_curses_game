import asyncio


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)

def get_real_maxyx(canvas):
    rows, columns = canvas.getmaxyx()  # getmaxyx на самом деле возвращает ширину и высоту
    max_y, max_x = rows - 1, columns - 1  # настоящие предельные значения
    return max_y, max_x


