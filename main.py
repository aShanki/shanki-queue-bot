import nextcord, os, json, asyncio, random
from nextcord.ext import commands
from nextcord import SlashOption, Interaction
from discord_components import DiscordComponents, Button, ButtonStyle, Select, SelectOption

intents = nextcord.Intents.default(); intents.reactions = True; intents.members = True; intents.presences = True
client = commands.Bot(command_prefix = "-", strip_after_prefix = True, case_insensitive = True, intents=intents)

@client.event
async def on_ready():
  DiscordComponents(client)
  print(f'{client.user.name}#{client.user.discriminator} is now Online!')

@client.event
async def on_voice_state_update(member, before, after):
  if before.channel is None and after.channel is not None:
    w = open("config.json")
    config = json.load(w)
    if str(after.channel.id) in config["allowed_channels"]:
      if len(after.channel.members) > 7 and len(after.channel.members) < 9: # Change to your queue size
        users = ""
        list = []
        for x in after.channel.members:
          list.append(x)
        queue_channel = await client.fetch_channel(int(config["queue_channel"]))
        for x in after.channel.members:
          if list[len(after.channel.members) - 1] == x:
            users = users[:-2] + " and "
          users = users + x.mention + ", "
        msg = await queue_channel.send(f"**8 users** detected in {after.channel.mention}! Starting a game with users {users[:-2]} **in 15 seconds** if no one leaves.") # Change to your thing
        await asyncio.sleep(15)
        if len(after.channel.members) > 7 and len(after.channel.members) < 9:
          content = str(msg.content)
          await msg.edit(content = f"~~{content}~~ ✅ Done!")
        else:
          content = str(msg.content)
          await msg.edit(content = f"~~{content}~~ ❌ Cancelled!")
          return
        f = open("curr_game.json")
        data = json.load(f) 
        current_game_number = int(data["total_games"]) + 1
        data["total_games"] = str(current_game_number)
        vc1 = await after.channel.guild.create_voice_channel(f"Game#{current_game_number} - Team A", user_limit = 4)
        vc2 = await after.channel.guild.create_voice_channel(f"Game#{current_game_number} - Team B", user_limit = 4)
        totalplayers = []
        TeamB = []
        for x in after.channel.members:
          totalplayers.append(x)
        TeamA = random.sample(totalplayers, 4)
        for x in totalplayers:
          if x not in TeamA:
            TeamB.append(x)
        TeamAdesc = ""
        TeamBdesc = ""
        for x in TeamA:
          if x.nick != None:
            ign = str(x.nick)
          else:
            ign = "-"
          TeamAdesc = f"• {str(x.name)}#{str(x.discriminator)}" + " " + f"({ign})" + "\n" + TeamAdesc
        for x in TeamB:
          if x.nick != None:
            ign = str(x.nick)
          else:
            ign = "-"
          TeamBdesc = f"• {str(x.name)}#{str(x.discriminator)}"+ " " + f"({ign})" + "\n" + TeamBdesc
        textchannel = await after.channel.guild.create_text_channel(f"Game#{current_game_number}")
        embed = nextcord.Embed(title = f"Game#{current_game_number}", color = nextcord.Color.from_rgb(230, 230, 250))
        embed.add_field(name = "Team A:", value = f"```\n{TeamAdesc}\n```")
        embed.add_field(name = "Team B:", value = f"```\n{TeamBdesc}\n```")
        embed.set_footer(text = "Use /end to end the game")
        await textchannel.send(embed = embed)
        totalplayersids = []
        TeamAids = []
        TeamBids = []
        for x in totalplayers:
          totalplayersids.append(str(x.id))
        for x in TeamA:
          TeamAids.append(str(x.id))
        for x in TeamB:
          TeamBids.append(str(x.id))
        data[f"Game#{current_game_number}"] = {"status": "awaiting_submission", "submissions": [], "totalplayers": totalplayersids, "TeamA": TeamAids, "TeamB": TeamBids, "vc1": str(vc1.id), "vc2": str(vc2.id), "textchannel": str(textchannel.id)}
        adminrole = after.channel.guild.get_role(int(config["adminrole"]))
        for x in TeamA:
          member = await after.channel.guild.fetch_member(x.id)
          await textchannel.set_permissions(member, view_channel = True, send_messages = True)
          await textchannel.set_permissions(adminrole, view_channel = True, send_messages = True)
          await textchannel.set_permissions(after.channel.guild.default_role, view_channel = False, send_messages = False)
          await member.move_to(vc1)
        for x in TeamB:
          member = await after.channel.guild.fetch_member(x.id)
          await textchannel.set_permissions(member, view_channel = True, send_messages = True)
          await textchannel.set_permissions(adminrole, view_channel = True, send_messages = True)
          await textchannel.set_permissions(after.channel.guild.default_role, view_channel = False, send_messages = False)
          await member.move_to(vc2)
        json_object = json.dumps(data, indent = 4)
        with open("curr_game.json", "w") as outfile:
          outfile.write(json_object)
          

@client.slash_command(description = "Register yourself with your IGN.")
async def register(interaction: Interaction, ign: str = SlashOption(description = "Your IGN", required = True)):
  w = open("config.json")
  data = json.load(w)
  role = interaction.guild.get_role(int(data["verified_role"]))
  await interaction.user.add_roles(role)
  await interaction.user.edit(nick = ign)
  await interaction.response.send_message(f"✅ Successfully registered with ign", ephemeral = False)

@client.slash_command(description = "Ends your current game.")
async def end(interaction: Interaction):
  f = open("curr_game.json")
  data = json.load(f)
  status = ""
  for x in data:
    if x == "total_games":
      pass
    else:
      if str(interaction.user.id) in data[x]["totalplayers"]:
        textchannel = await client.fetch_channel(int(data[x]["textchannel"]))
        await textchannel.delete()
        vc1 = await client.fetch_channel(int(data[x]["vc1"]))
        await vc1.delete()
        vc2 = await client.fetch_channel(int(data[x]["vc2"]))
        await vc2.delete()
        data.pop(x)
        json_object = json.dumps(data, indent = 4)
        with open("curr_game.json", "w") as outfile:
          outfile.write(json_object)
        await interaction.response.send_message(f"✔️ **{x}** has been ended successfully!", ephemeral = True)
        status = 0
  if status != 0:
    await interaction.response.send_message("❌ It does not appear that you're participating in an ongoing game!", ephemeral = True)
  else:
    return


client.run('OTMwNjk2NzI0NDcxNzU4ODg4.Yd5o3g.AmWQu2ZAsyU1y9mvasnCBytmTUs')
