import sqlite3
import discord
import uuid
from datetime import datetime, timedelta
from discord.ext import commands, tasks
from SQL_functions import *

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

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

    print(rows)

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


def get_embed(mc_server_uuid: str) -> discord.Embed:
    global SQL_connection, SQL_cursor

    # The time 16 hours ago
    t_16_hours_ago = datetime.now() - timedelta(hours=1)

    SQL_cursor.execute(f"SELECT * FROM LOGS_{mc_server_uuid} WHERE timestamp >= ?", (t_16_hours_ago,))
    rows = SQL_cursor.fetchall()

    if(len(rows) == 0):
        embed = discord.Embed(title="MC SERVER", color=0x00ff00)
        print("NO DATA YET")
        embed.add_field(value="NO DATA YET")
        return embed

    # Get the online collumn
    is_online = (rows[-1][3] == 1)
    player_count = rows[-1][4]
    player_list = rows[-1][5].split(",") if player_count > 0 else []

    if(is_online): status_str = "Online"
    else: status_str = "Offline"

    embed = discord.Embed(title="MC SERVER: " + status_str, color=0x00ff00)

    if(is_online):
        if(player_count <= 0):
            embed.add_field(name="Players", value="Such Empty", inline=False)
        else:
            players_str = "\n".join(player_list)
            embed.add_field(name="Players", value=players_str, inline=False)

    return embed


@tasks.loop(seconds=5)
async def update_pinned_messages():
    global SQL_connection, SQL_cursor
    SQL_cursor.execute(f"SELECT * FROM disc_servers")

    disc_servers = SQL_cursor.fetchall()

    for disc in disc_servers:

        try:
            guild = bot.get_guild(disc[0])
            channel = guild.get_channel(disc[3])
            message = channel.get_partial_message(disc[4])
            mc_server_uuid = disc[5]

            # Try to do something with the message, if it thows a HTTPException we assume that it's been deleted and try to create a new one
            try:
                await message.clear_reactions()
            except discord.HTTPException:
                print("Message does not exist, creating it")
                message = await channel.send("This is a message, time is:" + str(datetime.now()))
                SQL_cursor.execute("UPDATE disc_servers SET pinned_id = ? WHERE server_id = ?", (message.id, disc[0]))
                SQL_connection.commit()

            n_embed = get_embed(mc_server_uuid)
            
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
async def set(ctx: commands.Context, ip: str, port:int):
    global SQL_cursor

    owner_id = ctx.guild.owner_id
    
    # If message isn't sent by the auther, react to the message with an "X" and then exit this function
    if(ctx.author.id != owner_id):
        await ctx.message.add_reaction('❌')
        return

    update_disc_server(ctx, ip, port)
    print(f"Now tracking {ip}:{port}")


    


def start(sql_database: str, token: str):
    global SQL_connection, SQL_cursor

    SQL_connection = sqlite3.connect(sql_database)
    SQL_cursor =SQL_connection.cursor()

    bot.run('MTIzNDk5NTMzMTM3MzA3NjYwNA.G5ONJ7.Sy4PMlFuDl75MkkdXADmWCVFW6Gkuwc6Txr7r8')