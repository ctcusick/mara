"""
Room-related commands
"""
from mara.contrib.commands import MATCH_WORD

from . import constants
from .. import commands

__all__ = ['cmd_exits', 'cmd_where', 'gen_nav_cmds']


@commands.define_command()
def cmd_exits(event):
    "List available exits"
    event.user.write(event.user.room.exits.get_desc())


def gen_nav_cmd(service, commands, verb, direction):
    """
    Build and register a navigational command to move a user between rooms
    
    Events must have a ``user`` attribute (see contrib.users.event_add_user),
    which must have the contrib.rooms.store.RoomUserMixin (or provide a similar
    interface).
    """
    def command(event):
        event.user.move(direction)
    commands.register(verb, command, group='nav')


def gen_nav_cmds(service, commands):
    """
    Build and register navigation commands for users to move between rooms
    """
    # Build directions
    for direction in constants.DIRECTIONS:
        gen_nav_cmd(service, commands, direction, direction)

    # Add aliases
    for alias, direction in constants.SHORT_DIRECTIONS.items():
        gen_nav_cmd(service, commands, alias, direction)


@commands.define_command(args=r'(\w+)?', syntax='<user>')
def cmd_where(event, username=None):
    if not username:
        event.user.write('You are %s' % event.user.room.get_short())
        return
    
    user = event.user.manager.get_active_by_name(username)
    event.user.write('%s is %s' % (user.name, user.room.get_short()))
