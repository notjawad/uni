import discord
import aiosqlite
import yaml
import aiohttp
import os, json

from discord.ext import commands
from PIL import Image, ImageDraw


def load_config():
    with open("config.yml", "r", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)
    return config


config = load_config()


def ms_to_hours(ms):
    hours, remainder = divmod(ms, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    seconds, _ = divmod(remainder, 1000)
    return f"{hours}h {minutes}m {seconds}s"


class ListenerPaginator(discord.ui.View):
    def __init__(self, data, track):
        super().__init__()
        self.data = data
        self.track = track
        self.current_page = 0

    @discord.ui.button(label="First", emoji="⏮️", style=discord.ButtonStyle.secondary)
    async def first_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        self.current_page = 0
        await interaction.response.edit_message(
            embed=self.get_page_content(), view=self
        )

    @discord.ui.button(
        label="Previous", emoji="⬅️", style=discord.ButtonStyle.secondary
    )
    async def previous_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(
                embed=self.get_page_content(), view=self
            )

    @discord.ui.button(label="Next", emoji="➡️", style=discord.ButtonStyle.secondary)
    async def next_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        if self.current_page < len(self.data) - 1:
            self.current_page += 1
            await interaction.response.edit_message(
                embed=self.get_page_content(), view=self
            )

    @discord.ui.button(label="Last", emoji="⏭️", style=discord.ButtonStyle.secondary)
    async def last_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        self.current_page = len(self.data) - 1
        await interaction.response.edit_message(
            embed=self.get_page_content(), view=self
        )

    def get_page_content(self):
        item = self.data[self.current_page]
        embed = discord.Embed(
            description=item["user"]["profile"]["bio"] or "No bio",
            color=discord.Color.embed_background(),
        )

        if item["user"]["image"]:
            embed.set_thumbnail(url=item["user"]["image"])

        embed.set_author(
            name=f"{self.track.title} by {self.track.artist}",
            url=self.track.track_url,
            icon_url=self.track.album_cover_url,
        )

        embed.add_field(
            name="User",
            value=f"{item['user']['displayName']} ([Open in Spotify](https://open.spotify.com/user/{item['user']['id']}))",
        )
        embed.add_field(
            name="Streams",
            value=f"{item['streams']}x ({ms_to_hours(item['playedMs'])})",
        )

        embed.set_footer(text=f"Page {self.current_page + 1}/{len(self.data)}")

        return embed


class Misc(commands.Cog):
    def __init__(self, bot_: discord.Bot):
        self.bot = bot_
        self.db_path = "kino.db"
        self.bot.loop.create_task(self.setup_db())

    async def setup_db(self):
        self.conn = await aiosqlite.connect(self.db_path)

    async def channel_autocomplete(self, ctx: discord.ApplicationContext):
        return [
            discord.OptionChoice(name=channel.name, value=str(channel.id))
            for channel in ctx.guild.text_channels
        ]

    async def role_autocomplete(self, ctx: discord.ApplicationContext):
        return [
            discord.OptionChoice(name=role.name, value=str(role.id))
            for role in ctx.guild.roles
        ]

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        async with self.conn.cursor() as cur:
            await cur.execute(
                "SELECT message FROM afk WHERE user_id = ?", (message.author.id,)
            )
            afk_message = await cur.fetchone()
            if afk_message:
                await message.channel.send(
                    f"Welcome back {message.author.mention}! AFK status removed.",
                    delete_after=5,
                )
                await cur.execute(
                    "DELETE FROM afk WHERE user_id = ?", (message.author.id,)
                )

            if message.mentions:
                for user in message.mentions:
                    await cur.execute(
                        "SELECT message FROM afk WHERE user_id = ?", (user.id,)
                    )
                    afk_message = await cur.fetchone()
                    if afk_message:
                        embed = discord.Embed(
                            description=f"Hello {message.author.mention}, {user.mention} is currently AFK.",
                            color=config["COLORS"]["INFO"],
                        )
                        embed.add_field(
                            name="AFK Message", value=afk_message[0], inline=False
                        )
                        await message.channel.send(embed=embed, delete_after=5)
        await self.conn.commit()

    @discord.slash_command(
        name="quickpoll",
        description="Add up/down arrow to message initiating a poll",
    )
    async def quickpoll(
        self,
        ctx: discord.ApplicationContext,
        message_id=discord.Option(str, "Message ID to add emojis to.", required=True),
        emoji_type=discord.Option(
            str,
            "Emoji type to add to message.",
            required=True,
            choices=[
                discord.OptionChoice(name="Up/Down Arrow", value="updown"),
                discord.OptionChoice(name="Green Check/Red X", value="yesno"),
                discord.OptionChoice(name="Thumbs Up/Down", value="thumbs"),
            ],
        ),
    ):
        emoji_pairs = { 
            "updown": ("⬆️", "⬇️"),
            "yesno": ("✅", "❌"),
            "thumbs": ("👍", "👎") 
        }  # fmt: skip

        message = await ctx.channel.fetch_message(int(message_id))
        emojis = emoji_pairs.get(emoji_type, ())
        for emoji in emojis:
            await message.add_reaction(emoji)

        await ctx.respond("Done.", ephemeral=True, delete_after=5)

    @discord.slash_command(
        name="afk",
        description="Set an AFK status for when you are mentioned",
    )
    async def _afk(
        self,
        ctx: discord.ApplicationContext,
        message=discord.Option(
            str, "Message to display when you are mentioned", required=True
        ),
    ):
        async with self.conn.cursor() as cur:
            await cur.execute(
                "CREATE TABLE IF NOT EXISTS afk (user_id INTEGER PRIMARY KEY, message TEXT)"
            )
            await cur.execute("SELECT 1 FROM afk WHERE user_id = ?", (ctx.author.id,))
            if await cur.fetchone():
                await cur.execute("DELETE FROM afk WHERE user_id = ?", (ctx.author.id,))
                await ctx.respond("AFK status removed.", ephemeral=True)
            else:
                await cur.execute(
                    "INSERT INTO afk (user_id, message) VALUES (?, ?)",
                    (ctx.author.id, message),
                )
                await ctx.respond("AFK status set.", ephemeral=True)
        await self.conn.commit()

    async def popular_movies_autocomplete(self, ctx: discord.ApplicationContext):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.themoviedb.org/3/discover/movie",
                params={
                    "language": "en-US",
                    "page": "1",
                    "sort_by": "popularity.desc",
                },
                headers={
                    "Authorization": f"Bearer {config['TMDB_API_KEY']}",
                    "accept": "application/json",
                },
            ) as response:
                data = await response.json()

        return [
            discord.OptionChoice(
                name="Popular Movies Right Now", value="0"
            ),  # Non-selectable placeholder
            *[
                discord.OptionChoice(name=movie["title"], value=str(movie["title"]))
                for movie in data["results"]
            ],
        ]

    _movie = discord.commands.SlashCommandGroup(
        name="movie",
        description="Movie related commands",
    )

    @_movie.command(
        name="watch",
        description="Get a link to watch a movie.",
    )
    async def _watch(
        self,
        ctx: discord.ApplicationContext,
        movie=discord.Option(
            str,
            "Movie to watch",
            required=True,
            autocomplete=popular_movies_autocomplete,
        ),
        include_adult=discord.Option(
            bool, "Include adult movies (True by default)", required=False, default=True
        ),
    ):
        if movie == "0":
            return await ctx.respond(
                "Um, you selected the placeholder option. Please select a movie.",
                ephemeral=True,
            )

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.themoviedb.org/3/search/movie",
                params={
                    "query": movie,
                    "language": "en-US",
                    "include_adult": str(include_adult).lower(),
                },
                headers={
                    "Authorization": f"Bearer {config['TMDB_API_KEY']}",
                    "accept": "application/json",
                },
            ) as response:
                data = await response.json()

        if not data["results"]:
            return await ctx.respond("No results found.", ephemeral=True)

        genre_dict = {
            "Action": 28,
            "Adventure": 12,
            "Animation": 16,
            "Comedy": 35,
            "Crime": 80,
            "Documentary": 99,
            "Drama": 18,
            "Family": 10751,
            "Fantasy": 14,
            "History": 36,
            "Horror": 27,
            "Music": 10402,
            "Mystery": 9648,
            "Romance": 10749,
            "Science Fiction": 878,
            "TV Movie": 10770,
            "Thriller": 53,
            "War": 10752,
            "Western": 37,
        }

        movie = data["results"][0]

        watch_url = f"https://movie-web.app/media/tmdb-movie-{movie['id']}-{movie['title'].replace(' ', '-').lower()}"
        embed = discord.Embed(
            title=movie["title"],
            description=movie["overview"],
            color=config["COLORS"]["SUCCESS"],
        )
        embed.set_thumbnail(
            url=f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
        )

        embed.add_field(
            name="Genres",
            value=", ".join(
                [
                    genre_name
                    for genre_name, genre_id in genre_dict.items()
                    if genre_id in movie["genre_ids"]
                ]
            ),
        )

        embed.add_field(
            name="Vote Average",
            value=f"{round(movie['vote_average'] * 2) / 2} ({movie['vote_count']})",
        )

        watch_button = discord.ui.Button(
            style=discord.ButtonStyle.link, label="Watch", url=watch_url
        )
        view = discord.ui.View()
        view.add_item(watch_button)
        await ctx.respond(embed=embed, view=view)

    @discord.slash_command(
        name="invites",
        description="View all active invites in the server",
    )
    async def _invites(self, ctx: discord.ApplicationContext):
        invites = await ctx.guild.invites()
        embed = discord.Embed(
            title=f"Active Invites ({len(invites)})",
            color=config["COLORS"]["INFO"],
        )
        for invite in invites:
            embed.add_field(
                name=invite.code,
                value=f"**Creator**: {invite.inviter.mention}\n**Uses**: {invite.uses}\n**Channel**: {invite.channel.mention}",
            )
        await ctx.respond(embed=embed)

    @discord.slash_command(
        name="tts",
        description="Sends a .mp3 file of text speech",
    )
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def _tts(
        self,
        ctx: discord.ApplicationContext,
        text=discord.Option(str, "Text to speak", required=True),
        voice=discord.Option(
            str,
            "Voice to speak with",
            required=False,
            choices=[
                discord.OptionChoice(name="Brian", value="Brian"),
                discord.OptionChoice(name="Emma", value="Emma"),
                discord.OptionChoice(name="Ivy", value="Ivy"),
                discord.OptionChoice(name="Joey", value="Joey"),
                discord.OptionChoice(name="Justin", value="Justin"),
                discord.OptionChoice(name="Kendra", value="Kendra"),
                discord.OptionChoice(name="Kimberly", value="Kimberly"),
                discord.OptionChoice(name="Matthew", value="Matthew"),
                discord.OptionChoice(name="Salli", value="Salli"),
            ],
        ),
    ):
        await ctx.defer()

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://ttsmp3.com/makemp3_new.php",
                data={
                    "msg": text,
                    "lang": voice,
                    "source": "ttsmp3",
                    "quality": "hi",
                    "speed": "0",
                    "action": "process",
                },
            ) as response:
                data = await response.json()

            async with session.get(data["URL"]) as response:
                with open("tts.mp3", "wb") as file:
                    file.write(await response.read())

            await ctx.respond(file=discord.File("tts.mp3"))
            os.remove("tts.mp3")

    @discord.slash_command(
        name="horoscope",
        description="Get your daily horoscope",
    )
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def _horoscope(
        self,
        ctx: discord.ApplicationContext,
        sign=discord.Option(
            str,
            "Zodiac sign",
            required=True,
            choices=[
                discord.OptionChoice(name="Aries", value="aries"),
                discord.OptionChoice(name="Taurus", value="taurus"),
                discord.OptionChoice(name="Gemini", value="gemini"),
                discord.OptionChoice(name="Cancer", value="cancer"),
                discord.OptionChoice(name="Leo", value="leo"),
                discord.OptionChoice(name="Virgo", value="virgo"),
                discord.OptionChoice(name="Libra", value="libra"),
                discord.OptionChoice(name="Scorpio", value="scorpio"),
                discord.OptionChoice(name="Sagittarius", value="sagittarius"),
                discord.OptionChoice(name="Capricorn", value="capricorn"),
                discord.OptionChoice(name="Aquarius", value="aquarius"),
                discord.OptionChoice(name="Pisces", value="pisces"),
            ],
        ),
    ):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://newastro.vercel.app/{sign}") as response:
                data = await response.json()

        embed = discord.Embed(
            description=data["horoscope"], color=config["COLORS"]["SUCCESS"]
        )
        embed.set_thumbnail(url=data["icon"])
        await ctx.respond(embed=embed)

    @discord.slash_command(name="colorscheme", description="Generate a color scheme")
    async def _colorscheme(self, ctx: discord.ApplicationContext):
        await ctx.defer()

        url = "http://colormind.io/api/"
        payload = {"model": "default"}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    return await ctx.respond("Failed to fetch color scheme.")

                data = json.loads(await response.text())
                colors = data.get("result", [])
        if not colors:
            return await ctx.respond("No colors received from the service.")

        try:
            image = Image.new("RGB", (100 * len(colors), 100))
            draw = ImageDraw.Draw(image)
            for i, color in enumerate(colors):
                draw.rectangle([(i * 100, 0), ((i + 1) * 100, 100)], fill=tuple(color))

            filename = "colors.png"
            image.save(filename)
            await ctx.respond(file=discord.File(filename))
        except Exception as e:
            await ctx.respond(f"Error creating the color image: {e}")
        finally:
            if os.path.exists(filename):
                os.remove(filename)

    @discord.slash_command(
        name="listeners",
        description="Shows the top listeners of your current Spotify song. (Must be listening to Spotify)",
    )
    async def get_listeners(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        spotify = None
        for activity in ctx.author.activities:
            if isinstance(activity, discord.Spotify):
                spotify = activity

        if not spotify:
            await ctx.respond(
                "You must be listening to Spotify to use this command.", ephemeral=True
            )

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://beta-api.stats.fm/api/v1/search/elastic",
                params={
                    "query": spotify.title,
                    "type": "track",
                    "limit": "50",
                },
                headers={
                    "accept": "application/json",
                    "User-Agent": "Mozilla/5.0 (U; Linux i654 ) Gecko/20130401 Firefox/46.2",
                },
            ) as response:
                data = await response.json()

                track_id = None

                if data.get("items") and data["items"].get("tracks"):
                    tracks = data["items"]["tracks"]
                    for track in tracks:
                        track_artists = [artist["name"] for artist in track["artists"]]
                        if spotify.artist in track_artists:
                            track_id = track["id"]
                            break

                if not track:
                    await ctx.respond(
                        f"Could not find any listeners for {spotify.title}"
                    )

                async with session.get(
                    f"https://beta-api.stats.fm/api/v1/tracks/{track_id}/top/listeners",
                    headers={
                        "accept": "application/json",
                        "User-Agent": "Mozilla/5.0 (U; Linux i654 ) Gecko/20130401 Firefox/46.2",
                        "Authorization": f"Bearer {config['STATS_FM_API_KEY']}",
                    },
                ) as response:
                    data = await response.json()
                    if not data.get("items"):
                        await ctx.respond(
                            f"Could not find any listeners for {spotify.title}"
                        )
                        return

                    listeners = data["items"]
                    view = ListenerPaginator(listeners, spotify)

                    first_listener = listeners[0]
                    embed = discord.Embed(
                        description=first_listener["user"]["profile"]["bio"]
                        or "No bio",
                        color=discord.Color.embed_background(),
                    )

                    embed.set_author(
                        name=f"{spotify.title} by {spotify.artist}",
                        url=spotify.track_url,
                        icon_url=spotify.album_cover_url,
                    )

                    if first_listener["user"]["image"]:
                        embed.set_thumbnail(url=first_listener["user"]["image"])

                    embed.add_field(
                        name="User",
                        value=f"{first_listener['user']['displayName']} ([Open in Spotify](https://open.spotify.com/user/{first_listener['user']['id']}))",
                    )
                    embed.add_field(
                        name="Streams",
                        value=f"{first_listener['streams']}x ({ms_to_hours(first_listener['playedMs'])})",
                    )

                    embed.set_footer(text=f"Page 1/{len(listeners)}")

                    await ctx.respond(embed=embed, view=view)


def setup(bot_: discord.Bot):
    bot_.add_cog(Misc(bot_))
