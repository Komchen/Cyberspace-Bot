import asyncio
from collections import deque

import discord
import yt_dlp
from discord.ext import commands

YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


class Song:
    def __init__(self, title: str, url: str, webpage_url: str, requester: str):
        self.title = title
        self.url = url
        self.webpage_url = webpage_url
        self.requester = requester


class GuildMusicPlayer:
    def __init__(self, bot: commands.Bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        self.queue: deque[Song] = deque()
        self.current: Song | None = None
        self.voice: discord.VoiceClient | None = None
        self._play_next = asyncio.Event()
        self._task: asyncio.Task | None = None
        self._stopped = False

    def ensure_player_loop(self) -> None:
        if self._task is None or self._task.done():
            self._stopped = False
            self._task = self.bot.loop.create_task(self._player_loop())

    async def _player_loop(self) -> None:
        while not self._stopped:
            self._play_next.clear()

            if not self.queue:
                self.current = None
                await asyncio.sleep(0.5)
                if not self.queue:
                    break
                continue

            self.current = self.queue.popleft()
            if self.voice is None or not self.voice.is_connected():
                self.current = None
                break

            source = discord.FFmpegPCMAudio(self.current.url, **FFMPEG_OPTIONS)
            self.voice.play(
                source,
                after=lambda _error: self.bot.loop.call_soon_threadsafe(
                    self._play_next.set
                ),
            )
            await self._play_next.wait()

        self.current = None
        self._task = None

    def skip(self) -> bool:
        if self.voice and self.voice.is_playing():
            self.voice.stop()
            return True
        return False

    def stop(self) -> None:
        self._stopped = True
        self.queue.clear()
        self.current = None
        if self.voice and (self.voice.is_playing() or self.voice.is_paused()):
            self.voice.stop()

    def pause(self) -> bool:
        if self.voice and self.voice.is_playing():
            self.voice.pause()
            return True
        return False

    def resume(self) -> bool:
        if self.voice and self.voice.is_paused():
            self.voice.resume()
            return True
        return False


class Music(commands.Cog):
    """Voice music playback."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.players: dict[int, GuildMusicPlayer] = {}

    def get_player(self, guild_id: int) -> GuildMusicPlayer:
        player = self.players.get(guild_id)
        if player is None:
            player = GuildMusicPlayer(self.bot, guild_id)
            self.players[guild_id] = player
        return player

    async def shutdown(self) -> None:
        for player in list(self.players.values()):
            player.stop()

    async def extract_song(self, query: str, requester: str) -> Song:
        def _extract() -> Song:
            with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
                info = ydl.extract_info(query, download=False)
                if info is None:
                    raise ValueError("Could not find that track.")
                if "entries" in info:
                    entries = [e for e in info["entries"] if e]
                    if not entries:
                        raise ValueError("Could not find that track.")
                    info = entries[0]
                stream_url = info.get("url")
                if not stream_url:
                    raise ValueError("No playable audio stream found.")
                return Song(
                    title=info.get("title") or "Unknown title",
                    url=stream_url,
                    webpage_url=info.get("webpage_url") or query,
                    requester=requester,
                )

        return await asyncio.to_thread(_extract)

    async def ensure_voice(self, ctx: commands.Context) -> discord.VoiceClient:
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            raise commands.CommandError("Join a voice channel first.")

        channel = ctx.author.voice.channel
        player = self.get_player(ctx.guild.id)

        if ctx.voice_client is None:
            player.voice = await channel.connect()
        elif ctx.voice_client.channel != channel:
            await ctx.voice_client.move_to(channel)
            player.voice = ctx.voice_client
        else:
            player.voice = ctx.voice_client

        return player.voice

    @commands.command(name="join", help="Join your current voice channel.")
    @commands.guild_only()
    async def join(self, ctx: commands.Context):
        voice = await self.ensure_voice(ctx)
        await ctx.send(f"Joined {voice.channel.mention}.")

    @commands.command(name="leave", help="Leave the voice channel and clear the queue.")
    @commands.guild_only()
    async def leave(self, ctx: commands.Context):
        player = self.get_player(ctx.guild.id)
        player.stop()
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            player.voice = None
            await ctx.send("Left the voice channel.")
        else:
            await ctx.send("I'm not in a voice channel.")

    @commands.command(name="play", help="Play a song from a YouTube URL or search query.")
    @commands.guild_only()
    async def play(self, ctx: commands.Context, *, query: str):
        await self.ensure_voice(ctx)
        player = self.get_player(ctx.guild.id)

        async with ctx.typing():
            try:
                song = await self.extract_song(query, ctx.author.display_name)
            except Exception as exc:
                await ctx.send(f"Couldn't play that: {exc}")
                return

        was_idle = player.current is None and not (
            player.voice and (player.voice.is_playing() or player.voice.is_paused())
        )
        player.queue.append(song)
        player.ensure_player_loop()

        if was_idle:
            await ctx.send(f"Playing **{song.title}**")
        else:
            await ctx.send(f"Queued **{song.title}** (#{len(player.queue)})")

    @commands.command(name="pause", help="Pause the current song.")
    @commands.guild_only()
    async def pause(self, ctx: commands.Context):
        if self.get_player(ctx.guild.id).pause():
            await ctx.send("Paused.")
        else:
            await ctx.send("Nothing is playing.")

    @commands.command(name="resume", help="Resume the paused song.")
    @commands.guild_only()
    async def resume(self, ctx: commands.Context):
        if self.get_player(ctx.guild.id).resume():
            await ctx.send("Resumed.")
        else:
            await ctx.send("Nothing is paused.")

    @commands.command(name="skip", help="Skip the current song.")
    @commands.guild_only()
    async def skip(self, ctx: commands.Context):
        if self.get_player(ctx.guild.id).skip():
            await ctx.send("Skipped.")
        else:
            await ctx.send("Nothing is playing.")

    @commands.command(name="stop", help="Stop playback and clear the queue.")
    @commands.guild_only()
    async def stop(self, ctx: commands.Context):
        self.get_player(ctx.guild.id).stop()
        await ctx.send("Stopped and cleared the queue.")

    @commands.command(name="queue", help="Show the music queue.")
    @commands.guild_only()
    async def queue(self, ctx: commands.Context):
        player = self.get_player(ctx.guild.id)
        lines: list[str] = []
        if player.current:
            lines.append(f"**Now playing:** {player.current.title}")
        if player.queue:
            lines.append("**Up next:**")
            for index, song in enumerate(list(player.queue)[:10], start=1):
                lines.append(f"{index}. {song.title} — requested by {song.requester}")
            if len(player.queue) > 10:
                lines.append(f"...and {len(player.queue) - 10} more")
        if not lines:
            await ctx.send("Queue is empty.")
            return
        await ctx.send("\n".join(lines))

    @commands.command(
        name="nowplaying",
        aliases=["np"],
        help="Show the song currently playing.",
    )
    @commands.guild_only()
    async def nowplaying(self, ctx: commands.Context):
        player = self.get_player(ctx.guild.id)
        if player.current is None:
            await ctx.send("Nothing is playing.")
            return
        song = player.current
        await ctx.send(
            f"**Now playing:** [{song.title}]({song.webpage_url})\n"
            f"Requested by {song.requester}"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
