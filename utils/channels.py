"""Helpers for resolving announcement / greeting channels."""

from __future__ import annotations

import discord

from utils.storage import load_guild


def announce_channel(guild: discord.Guild) -> discord.TextChannel | None:
    data = load_guild(guild.id)
    channel_id = data.get("announce_channel_id")
    if channel_id:
        channel = guild.get_channel(int(channel_id))
        if isinstance(channel, discord.TextChannel):
            return channel
    if isinstance(guild.system_channel, discord.TextChannel):
        return guild.system_channel
    me = guild.me
    for channel in guild.text_channels:
        if me and channel.permissions_for(me).send_messages:
            return channel
    return None


def officers_channel(guild: discord.Guild) -> discord.TextChannel | None:
    data = load_guild(guild.id)
    channel_id = data.get("officers_channel_id")
    if channel_id:
        channel = guild.get_channel(int(channel_id))
        if isinstance(channel, discord.TextChannel):
            return channel
    return announce_channel(guild)
