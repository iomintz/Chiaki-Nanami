import asyncio
import discord
import inspect
import itertools
import random
import re

from collections import Counter
from datetime import datetime
from discord.ext import commands

from cogs.utils.database import Database
from cogs.utils.misc import cycle_shuffle, full_succinct_duration

# You are free to change this if you want.
DEFAULT_CMD_PREFIX = '->'
description = '''A test for the Chiaki bot (totally not a ripoff of Nadeko)'''
MAX_FORMATTER_WIDTH = 90

def cog_prefix(cmd):
    cog = cmd.instance
    return (DEFAULT_CMD_PREFIX if cog is None
            else getattr(cog, '__prefix__', DEFAULT_CMD_PREFIX))

def str_prefix(cmd):
    prefix = cog_prefix(cmd)
    return prefix if isinstance(prefix, str) else '|'.join(prefix)

class ChiakiFormatter(commands.HelpFormatter):
    def _add_subcommands_to_page(self, max_width, commands):
        commands = ((str_prefix(cmd) + name, cmd) for name, cmd in commands
                    if name not in cmd.aliases)
        super()._add_subcommands_to_page(max_width, commands)

    @property
    def clean_prefix(self):
        return super().clean_prefix if self.is_bot() or self.is_cog() else str_prefix(self.command)

    def format(self):
        """Handles the actual behaviour involved with formatting.
        To change the behaviour, this method should be overridden.
        Returns
        --------
        list
            A paginated output of the help command.
        """
        from discord.ext import commands
        self._paginator = commands.Paginator()
        # we need a padding of ~80 or so

        description = self.command.description if not self.is_cog() else inspect.getdoc(self.command)
        if description:
            # <description> portion
            self._paginator.add_line(description, empty=True)

        if isinstance(self.command, commands.Command):
            # <signature portion>
            signature = self.get_command_signature()
            self._paginator.add_line(signature, empty=True)

            # <long doc> section
            if self.command.help:
                self._paginator.add_line(self.command.help, empty=True)

            # end it here if it's just a regular command
            if not self.has_subcommands():
                self._paginator.close_page()
                return self._paginator.pages

        max_width = self.max_name_size

        def category(tup):
            cmd = tup[1]
            prefix = cog_prefix(cmd)
            # we insert the zero width space there to give it approximate
            # last place sorting position.
            return f'{cmd.cog_name} (Prefix: {prefix})' if cmd.cog_name is not None else '\u200bNo Category:'

        if self.is_bot():
            data = sorted(self.filter_command_list(), key=category)
            for category, commands in itertools.groupby(data, key=category):
                # there simply is no prettier way of doing this.
                commands = list(commands)
                if len(commands) > 0:
                    self._paginator.add_line(category)

                self._add_subcommands_to_page(max_width, commands)
        else:
            prefix = getattr(type(self.command), '__prefix__', DEFAULT_CMD_PREFIX)
            self._paginator.add_line('Commands:')
            self._add_subcommands_to_page(max_width, self.filter_command_list())

        # add the ending note
        self._paginator.add_line()
        ending_note = self.get_ending_note()
        self._paginator.add_line(ending_note)
        return self._paginator.pages

def _find_prefix_by_cog(bot, message):
    if not message.content:
        return DEFAULT_CMD_PREFIX

    first_word = message.content.split()[0]
    try:
        maybe_cmd = re.search(r'(\w+)', first_word).group(1)
    except AttributeError:
        return DEFAULT_CMD_PREFIX

    cmd = bot.get_command(maybe_cmd)
    if cmd is None:
        return DEFAULT_CMD_PREFIX

    return cog_prefix(cmd)

class ChiakiBot(commands.Bot):
    def __init__(self, command_prefix, formatter=None, description=None, pm_help=False, **options):
        super().__init__(command_prefix, formatter, description, pm_help, **options)

        self.loop.create_task(self.change_game())
        self.loop.create_task(self.dump_db_cycle())
        self.loop.create_task(self._start_time())

        self.commands_counter = Counter()
        self.persistent_counter = Database.from_json("stats.json")
        self.databases = [(self.persistent_counter, None)]

    async def _start_time(self):
        await self.wait_until_ready()
        self.start_time = datetime.now()

    def add_database(self, db, unload=None):
        self.databases.append((db, unload))

    # literally the only reason why I created a subclass
    async def dump_databases(self):
        for db, unload in self.databases:
            if unload is not None:
                unload()
            await db.dump()

    async def logout(self):
        self.commands_counter.update(self.persistent_counter)
        self.persistent_counter.update(self.commands_counter)
        await self.dump_databases()
        await super().logout()

    def get_member(self, id):
        return discord.utils.get(self.get_all_members(), id=id)

    # Just some looping functions
    async def change_game(self):
        await self.wait_until_ready()
        GAME_CHOICES = cycle_shuffle([
        'Gala Omega',
        'Dangan Ronpa: Trigger Happy Havoc',
        'Super Dangan Ronpa 2',
        'NDRV3',
        'with Hajime Hinata',
        'with hope',
        'hope',
        'without despair',
        'with Nadeko',
        'with Usami',
        ])
        while not self.is_closed:
            name = next(GAME_CHOICES)
            await self.change_presence(game=discord.Game(name=name))
            await asyncio.sleep(random.uniform(0.5, 10) * 60)

    async def dump_db_cycle(self):
        await self.wait_until_ready()
        while not self.is_closed:
            await self.dump_databases()
            print("all databases successfully dumped")
            await asyncio.sleep(600)

    @property
    def uptime(self):
        return datetime.now() - self.start_time

    @property
    def str_uptime(self):
        return full_succinct_duration(self.uptime.total_seconds())

# main bot
def chiaki_bot():
    return ChiakiBot(command_prefix=_find_prefix_by_cog,
                     formatter=ChiakiFormatter(width=MAX_FORMATTER_WIDTH),
                     description=description, pm_help=None
                    )
