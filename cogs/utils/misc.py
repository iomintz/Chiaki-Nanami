import aiohttp
import enum
import imghdr
import os
import random
import xml.etree.cElementTree as et

from datetime import timezone
from discord import utils, Colour, Status

def code_say(bot, msg):
    return bot.say(code_msg(msg))

def code_msg(msg):
    return '```\n{}```'.format(msg)

def cycle_shuffle(iterable):
    saved = [elem for elem in iterable]
    while True:
        random.shuffle(saved)
        for element in saved:
              yield element


status_colors = {
    Status.online         : Colour(0x43b581),
    Status.offline        : Colour(0x747f8d),
    Status.idle           : Colour(0xfaa61a),
    Status.dnd            : Colour(0xf04747),
    Status.do_not_disturb : Colour(0xf04747),
    Status.invisible      : Colour(0x747f8d),
    }

def status_color(status):
    return status_colors.get(status, Colour.default())

def filter_attr(iterable, **attrs):
    def predicate(elem):
        for attr, val in attrs.items():
            nested = attr.split('__')
            obj = elem
            for attribute in nested:
                obj = getattr(obj, attribute)

            if obj != val:
                return False
        return True

    return filter(predicate, iterable)

@utils.deprecated("discord.utils.cached_property")
class lazy_property(object):
    '''
    Meant to be used for lazy evaluation of an object attribute.
    Property should represent non-mutable data, as it replaces itself.
    '''

    def __init__(self,fget):
        self.fget = fget
        self.func_name = fget.__name__


    def __get__(self, obj, cls):
        if obj is None:
            return None
        value = self.fget(obj)
        setattr(obj, self.func_name, value)
        return value

def str_swap(string, swap1, swap2):
    return string.replace(swap1, '%temp%').replace(swap2, swap1).replace('%temp%', swap2)

def str_join(delim, iterable):
    return delim.join(map(str, iterable))

def test_svg(h, f):
    try:
        for event, el in et.iterparse(f, (b'start',)):
            tag = el.tag
            break
    except et.ParseError:
        pass
    if tag == b'{http://www.w3.org/2000/svg}svg':
        return 'svg'

imghdr.tests.append(test_svg)

async def image_from_url(url, fname=None, session=None):
    if session is None:
        session = aiohttp.ClientSession()
    if fname is None:
        random_thing = random.randrange(10 ** 8)
        fname = "tmp-{}".format(str(random_thing).zfill(8))
    async with session.get(url) as response:
        with open(fname, 'wb') as f:
            while True:
                chunk = await response.content.read(1024)
                if not chunk:
                    break
                f.write(chunk)

        ext = "." + imghdr.what(fname)
        os.rename(fname, fname + ext)
        fname += ext
        with open(fname , 'rb') as f:
            return f, fname

def nice_time(time):
    # Hopefully I can get a timezone-specific version.
    # I don't think that's possible though.
    new_time = time.replace(tzinfo=timezone.utc)
    return new_time.strftime("%Y/%m/%d %r (%Z)")

def parse_int(maybe_int, base=10):
    try:
        return int(maybe_int, base)
    except ValueError:
        return None

def full_succinct_duration(secs):
	m, s = divmod(secs, 60)
	h, m = divmod(m, 60)
	d, h = divmod(h, 24)
	w, d = divmod(d, 7)
	unit_list = [(w, 'weeks'), (d, 'days'), (h, 'hours'), (m, 'mins'), (s, 'seconds')]
	return ', '.join(f"{round(n)} {u}" for n, u in unit_list if n)
