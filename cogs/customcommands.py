# Once again json sucks
# This can't be used because of weird namedtuple serialization issues
# So a dict is required
#from collections import namedtuple
from discord.ext import commands
from operator import itemgetter

from .utils import checks
from .utils.database import Database

CC_FILE_NAME = "customcommands.json"
class CustomReactions:
    def __init__(self, bot):
        self.bot = bot
        self.db = Database.from_json(CC_FILE_NAME, default_factory=dict)

    def _pages(self, server):
        pages = []
        page = []
        result_len = 0
        page_append, pages_append = page.append, pages.append
        for trig, react in sorted(self.db[server].items(), key=itemgetter(0)):
            # If there is a cleaner way of doing this, please tell me.
            result = trig + " => " + react
            page_append(result)
            result_len += len(result)
            if result_len >= 1500:
                pages_append(page)
                page.clear()
        pages_append(page)
        return pages
    
    @commands.group(aliases=["customcomm", "cc", "cr", "custreact"])
    async def customcommand(self):
        """Namespace for the custom commands"""
        pass

    @customcommand.command(pass_context=True)
    @checks.admin_or_permissions()
    async def add(self, ctx, trigger, *, reaction : str):
        """Adds a new custom reaction/trigger (depending on what bot you use)

        The trigger must be put in quotes if you want spaces in your trigger.
        """
        server = ctx.message.server
        print(server)
        if trigger in self.db[server]:
            # TODO: Add multiple custom commands for the same trigger
            # (similar to Nadeko)
            return await self.bot.say("{} already has a reaction".format(trigger))
        self.db[server][trigger.lower()] = reaction
        await self.bot.say("Custom command added")
        
                
    @customcommand.command(pass_context=True)
    async def list(self, ctx, page=0):
        server = ctx.message.server or "global"
        await self.bot.say('\n'.join(self._pages(server)[page]))
    
    @customcommand.command(pass_context=True, aliases=['delete', 'del', 'rem',])
    @checks.admin_or_permissions()
    async def remove(self, ctx, *, ccid : str):
        """Removes a new custom reaction/trigger (depending on what bot you use)

        The trigger must be put in quotes if you want spaces in your trigger.
        """
        storage = self.db[ctx.message.server]
        if not storage:
            await self.bot.say("There are no commands for this server")
            return
        try:
            storage.pop(ccid.lower())
        except KeyError:
            await self.bot.say("{} was never a custom command".format(ccid))
        else:
            await self.bot.say("{} command removed".format(ccid))

    @customcommand.command(pass_context=True)
    @checks.admin_or_permissions()
    async def edit(self, ctx, ccid, *, new_react : str):
        ccid = ccid.lower()
        server = ctx.message.server
        storage = self.db[server]
        if not storage:
            await self.bot.say("There are no commands for this server")
            return
        if ccid not in storage:
            return await self.bot.say("Command {} doesn't ~~edit~~ exits".format(ccid))

        self.db[server][ccid.lower()] = new_react
        await self.bot.say("{} command edited".format(ccid))

    @customcommand.command(pass_context=True, hidden=True)
    @checks.is_owner()
    async def addg(self, ctx, trigger, *, msg : str):
        if not ctx.message.channel.is_private:
            return
        self.db["global"][trigger] = msg

    @customcommand.command(pass_context=True, hidden=True)
    @checks.is_owner()
    async def remg(self, ctx, trigger):
        if not ctx.message.channel.is_private:
            return
        try:
            self.db["global"].pop(ccid.lower())
        except KeyError:
            return await self.bot.say("{} was never a custom command".format(ccid))
            
    async def on_message(self, msg):
        storage = self.db[msg.server] or self.db["global"]
        reaction = storage.get(msg.content.lower())
        if reaction is not None:
            await self.bot.send_message(msg.channel, reaction)
        
def setup(bot):
    bot.add_cog(CustomReactions(bot))
