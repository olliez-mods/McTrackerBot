import sqlite3
import discord
import uuid
from datetime import datetime, timedelta
from discord.ext import commands, tasks
from SQL_functions import *
import asyncio
import random

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

BOT_OWNER_ID = -1

SQL_connection: sqlite3.Connection = None
SQL_cursor: sqlite3.Cursor = None

def get_uuid() -> str:
    return str(uuid.uuid4()).replace("-", "")

def start_tracking_mc_server(uuid: str, ip: str, port: int):
    global SQL_connection, SQL_cursor
    SQL_cursor.execute("INSERT INTO mc_servers (server_ip, server_port, server_uuid) VALUES (?, ?, ?)", 
                       (ip, port, uuid))
    SQL_connection.commit()

# Make sure that the information about this server is up to date
def update_disc_server(ctx: commands.Context, ip: str, port: int):
    global SQL_connection, SQL_cursor

    # Get all mc_servers that match the given ip and port (it shouldn't be more then one)
    SQL_cursor.execute(f"""SELECT * FROM mc_servers
                       WHERE server_ip = '{ip}' AND server_port = '{port}'""")
    rows = SQL_cursor.fetchall()

    # If we are tracking that IP and port, we can leach off of it, otherwise generate a new uuid for the mc server
    if(len(rows) > 0):
        uuid: str = rows[0][2]
        if(len(uuid) != 32):
            print("Unexpected uuid length")
            raise ValueError(f"uuid \"{uuid}\" unexpected length")
    else:
        uuid = get_uuid()
        start_tracking_mc_server(uuid, ip, port)

    disc_server_id = ctx.guild.id
    disc_server_name = ctx.guild.name
    owner_id = ctx.guild.owner.id
    channel_id = ctx.channel.id

    SQL_cursor.execute("INSERT OR REPLACE INTO disc_servers (server_id, server_name, owner_id, channel_id, mc_server_uuid) VALUES (?, ?, ?, ?, ?)", 
                       (disc_server_id, disc_server_name, owner_id, channel_id, uuid))
    SQL_connection.commit()

def format_seconds(seconds: int):

    if(seconds < 0): seconds = 0

    # Compute the number of hours, minutes, and seconds
    hours = seconds // 3600
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    # Build the string
    if hours == 1:
        return f"{hours} hour {minutes} mins"
    elif(hours > 1):
        return f"{hours} hours {minutes} mins"
    else:
        return f"{minutes} mins {seconds} secs"

# Retyurns an embed that shows how long each player currently online has been online for
def get_embed(mc_server_uuid: str, mc_server_name: str = "MC Server") -> discord.Embed:
    global SQL_connection, SQL_cursor

    # The time 16 hours ago
    t_16_hours_ago = datetime.now() - timedelta(hours=1)

    # This will get every log within the last 16 hours
    SQL_cursor.execute(f"SELECT * FROM LOGS_{mc_server_uuid} WHERE timestamp >= ?", (t_16_hours_ago,))
    rows = SQL_cursor.fetchall()

    # Since a log is made when something changes, we may not have any changes in the past 16 hours
    # This could mean someone is online for 16 hours+ so we want to get the most recent log if it exists
    if(len(rows) == 0):
        SQL_cursor.execute(f"SELECT * FROM LOGS_{mc_server_uuid} ORDER BY timestamp DESC LIMIT 1")
        rows = SQL_cursor.fetchall()

    # If there are actualy zero logs at all, we will return an Embed that says NO DATA
    if(len(rows) == 0):
        embed = discord.Embed(title=f"{mc_server_name}", color=0x858585) # grey
        embed.add_field(name="", value="NO DATA")
        return embed

    # Get the online collumn
    is_online = (rows[-1][3] == 1)
    player_count = rows[-1][4]
    player_list = rows[-1][5].split(",") if player_count > 0 else []

    # This will hold each players online seconds
    player_times_online: dict[str, str] = {}

    # Is the server online or offline
    if(is_online): 
        status_str = "Online"
        s_color = 0x00ff00
    else: 
        status_str = "Offline"
        s_color = 0xFF1616

    # In the case where a mc server won't return players names (mc.hypixel.net as an example)
    if(player_list == ['']):
        embed = discord.Embed(title=f"{mc_server_name}: " + status_str, color=s_color)
        embed.add_field(name="", value=("Player count: " + str('{:,}'.format(player_count))))
        return embed

    # This tracks how many players we don't have a final time for yet
    players_left: list[str] = player_list.copy()

    last_stamp = datetime.now()
    # Loop through the logs backwards
    for i in range(len(rows) -1, -1, -1):
        # If we have no players left to track we can exit early
        if(len(players_left) == 0):
            break

        # Get the timestamp and player list for this log
        time = rows[i][0]
        log_player_list = rows[i][5].split(",") if player_count > 0 else []

        # new_p_list allows us to edit the list while looping through it
        new_list = players_left
        for player in players_left:
            # We reached the log directly before this player joined the server
            if(not (player in log_player_list)):
                # Remove the player from tracked players list, and calculate seconds using the timestamp from the previouse log
                new_list.remove(player)
                player_times_online[player] = (datetime.now() - datetime.strptime(last_stamp, "%Y-%m-%d %H:%M:%S.%f")).seconds
        players_left = new_list

        last_stamp = rows[i][0]

    # If there are any players left over that we didn'y find a log where they joined in the last 16 hours, cap the time at 16 hours
    for player in players_left:
        player_times_online[player] = 60*60*16

    embed = discord.Embed(title=f"{mc_server_name}: " + status_str, color=s_color)

    if(is_online):
        if(player_count <= 0):
            embed.add_field(name="Players", value="Such Empty", inline=False)
        else:
            # For each player, format the seconds to something readable
            players_str = ""
            r_spread = random.random() * 7
            r_spread = int(r_spread/2 - r_spread)

            for p in player_list:
                players_str += p + " -> " + format_seconds(player_times_online[p]+r_spread) + "\n"
            embed.add_field(name="Players", value=players_str, inline=False)

    return embed

#Clear all the pinned messages sent by this bot on the entire server
async def clear_pinned(disc_server_id:int, channel_id:int):
    global bot
    guild = bot.get_guild(int(disc_server_id))
    channel = guild.get_channel(int(channel_id))
    if(guild == None): return
    if(channel == None): return

    pinned_messages = await channel.pins()
    for message in pinned_messages:
        if(message.author.id == bot.user.id):
            await message.unpin()
    

@tasks.loop(seconds=30)
async def update_pinned_messages():
    global SQL_connection, SQL_cursor
    SQL_cursor.execute(f"SELECT * FROM disc_servers")

    disc_servers = SQL_cursor.fetchall()

    # loop over every discord server
    for disc in disc_servers:

        try:
            guild_id:int = disc[0]
            guild = bot.get_guild(guild_id)
            if(guild == None):
                print("Could not find the guild")
                continue
            channel_id: int = disc[3]
            channel = guild.get_channel(channel_id)
            message = channel.get_partial_message(disc[4])
            mc_server_disp_name = disc[5]
            if (mc_server_disp_name == None): mc_server_disp_name = "MC Server"
            mc_server_uuid = disc[6]

            # Try to do something with the message, if it thows a HTTPException we assume that it's been deleted and try to create a new one
            try:
                await message.clear_reactions()
            except discord.HTTPException as e:
                print("Error with a pinned message, generating a new one")
                message = await channel.send("Please wait for up to 15 seconds for this message to update and pin itself.\nAlso make sure to remove old pinned messages in other channels.")
                await clear_pinned(guild_id, channel_id)
                await message.pin()
                SQL_cursor.execute("UPDATE disc_servers SET pinned_id = ? WHERE server_id = ?", (message.id, disc[0]))
                SQL_connection.commit()

            n_embed = get_embed(mc_server_uuid, mc_server_disp_name)
            
            await message.edit(embed=n_embed, content="")

            
            
        # if the guild or channel has been deleted then these may throw
        except discord.NotFound:
            pass
        except discord.HTTPException:
            pass



@bot.event
async def on_ready():
    print("Discord Bot connected to Discord!")
    update_pinned_messages.start()

@bot.event
async def on_command_error(ctx, error):
    if(isinstance(error, commands.UserInputError)):
        return
    raise error

@bot.command()
async def set(ctx: commands.Context, ip: str, port:int = 25565):
    owner_id = ctx.guild.owner_id
    
    # If message isn't sent by the auther, react to the message with an "X" and then exit this function
    if(ctx.author.id != owner_id and ctx.author.id != BOT_OWNER_ID):
        await ctx.message.add_reaction('❌')
        return

    await ctx.reply("Proccessing...\nPlease wait for a pinned message to be generated\n.")

    update_disc_server(ctx, ip, port)
    print(f"Now tracking {ip}:{port}")

@bot.command()
async def help(ctx: commands.Context):

    owner_id = ctx.guild.owner_id

    # If message isn't sent by the auther, react to the message with an "X" and then exit this function
    if(ctx.author.id != owner_id and ctx.author.id != BOT_OWNER_ID):
        await ctx.message.add_reaction('❌')
        return

    string = """Function:
    - !help   Brings up this page.\n
    - !set <ip> <port>   Starts tracking the given minecraft server, also creates the pinned message.\n
    - !name \"<name>\"   Sets the display name of the Minecraft server, use quotes (\") around the name for spaces.\n
    - !stop   Stops tracking the minecraft server."""
    await ctx.reply(string)


@bot.command()
async def taco(ctx: commands.Context):
    await ctx.message.delete()
    ctx.send(':taco:')

@bot.command()
async def stop(ctx: commands.Context):

    owner_id = ctx.guild.owner_id
    
    # If message isn't sent by the auther, react to the message with an "X" and then exit this function
    if(ctx.author.id != owner_id and ctx.author.id != BOT_OWNER_ID):
        await ctx.message.add_reaction('❌')
        return

    await ctx.reply("This feature is coming soon")


@bot.command()
async def name(ctx: commands.Context, name:str):
    global SQL_connection, SQL_cursor

    owner_id = ctx.guild.owner_id
    server_id = ctx.guild.id

    # If message isn't sent by the auther, react to the message with an "X" and then exit this function
    if(ctx.author.id != owner_id and ctx.author.id != BOT_OWNER_ID):
        await ctx.message.add_reaction('❌')
        return
    
    SQL_cursor.execute(f'SELECT * FROM disc_servers WHERE server_id = "{server_id}" LIMIT 1')
    rows = SQL_cursor.fetchall()

    if(len(rows) == 0):
        await ctx.reply("Please start tracking a minecraft server with \"!set\" before setting its name")
        return

    SQL_cursor.execute("UPDATE disc_servers SET mc_server_disp_name = ? WHERE server_id = ?", (name, server_id))
    SQL_connection.commit()

@bot.event
async def on_message(message: discord.Message):

    await bot.process_commands(message)

    # Check if the message is a system message indicating a message has been pinned
    if message.type == discord.MessageType.pins_add:
        # Check if the pinned message belongs to your bot
        if message.author == bot.user:
            # Delete the notification message
            await message.delete()
    

    
TIMEOUT = 10
async def set_timeout():
    global TIMEOUT
    update_pinned_messages.stop()
    update_pinned_messages.change_interval(seconds=TIMEOUT)
    update_pinned_messages.start()

def start(sql_database: str, token: str, owner_id:int, pinned_timeout):
    global SQL_connection, SQL_cursor, TIMEOUT, BOT_OWNER_ID

    BOT_OWNER_ID = owner_id

    SQL_connection = sqlite3.connect(sql_database)
    SQL_cursor =SQL_connection.cursor()

    TIMEOUT = pinned_timeout
    asyncio.run(set_timeout())

    bot.run(token)