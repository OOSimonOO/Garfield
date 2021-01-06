import time
import os
import threading
import random
from typing import Tuple

import discord
from gtts import gTTS
import googletrans

import MathBot
import Utils



class SoundPlayer:
    def __init__(self, guild : discord.Guild):
        self.guild = guild
        self.voice_client = None
        self.voice_channel = None
        self.queue = []
        self.skipping = False
        self.running = False
        self.thread = None
        self.now_playing = None
        
        
    @staticmethod
    def playthread(soundplayer):
        while soundplayer.running:
            if not soundplayer.skipping:
                if soundplayer.voice_client.is_paused():
                    time.sleep(1)
                    continue
                if soundplayer.voice_client.is_playing():
                    time.sleep(1)
                    continue
            else:
                soundplayer.skipping = False
                soundplayer.voice_client.stop()
            
            if len(soundplayer.queue) > 0:
                sound = soundplayer.queue.pop(0)
                soundplayer.now_playing = sound
                soundplayer.voice_client.play(sound[1])
            else:
                soundplayer.now_playing = None
            time.sleep(1)
        
    def is_connected(self) -> bool:
        return self.voice_channel != None
    
    async def connect(self, channel : discord.VoiceChannel) -> bool:
        if not self.is_connected():
            self.voice_channel = await channel.connect()
            self.voice_client = discord.utils.get(bot.voice_clients, guild = self.guild)
            self.running = True
            self.thread = threading.Thread(target=self.playthread, args=(self,))
            self.thread.start()
            return True
        else:
            return False
        
    async def disconnect(self) -> bool:
        if self.is_connected():
            self.voice_client.pause()
            self.running = False
            self.thread.join()
            self.voice_client = None
            await self.voice_channel.disconnect()
            self.voice_channel = None
            return True
        else:
            return False
            
    def pause(self) -> bool:
        if self.is_connected():
            self.voice_client.pause()
            return True
        else:
            return False
        
    def resume(self) -> bool:
        if self.is_connected():
            self.voice_client.resume()
            return True
        else:
            return False
        
    def add(self, name : str, audio : discord.FFmpegPCMAudio) -> None:
        self.queue.append((name, audio))
        
    def skip(self) -> None:
        self.skipping = True
    
    def clear(self) -> int:
        l = len(self.queue)
        self.queue = []
        return l
    
    
         
class DiscordBot(discord.Client):
    
    async def on_ready(self):
        tuple(map(lambda x: os.remove(f"temp\\{x}"), os.listdir("temp")))
        print("online")
        await self.change_presence(activity=discord.Activity(type =discord.ActivityType.playing , name="mit einer Python"))
        self.sound_players = {}
        self.mathbotout = "dec"
        self.ttsout = "de"
        self.muted_users = []
        

    async def on_message(self, message):
        if message.author == self.user:
            return
        
        print(message.content)
    
        if message.author.id in self.muted_users:
            await message.delete()
            return
        
        if message.content.startswith("!stop"):
            for key in self.sound_players:
                await self.sound_players[key].disconnect()
            await message.channel.send("bye 👋")
            await self.close()
            return
        
        
        
        #command
        if message.content.startswith("!"):
            msg, file = await self.perform_command(message.content.lower()[1:].split(), message.author, message.guild)
            if msg != "" or file != "":
                if msg == "":
                    await message.channel.send(file=file)
                elif file == "":
                    await message.channel.send(msg)
                else:
                    await message.channel.send(msg, file=file)
                
        #math
        elif message.content.startswith("."):
            msg = await self.perform_math_command(message.content.lower()[1:])
            if msg != "":
                await message.channel.send(msg) 
                
                    
        #normal message
        else:  
            if message.content.lower() in Utils.greeting:
                await message.channel.send(f"Hallo {message.author.mention}")
        
        
        
        
        
    def check_sound_player(self, guild : discord.Guild) -> None:
        if not guild.id in self.sound_players:
            self.sound_players[guild.id] = SoundPlayer(guild)
            
            
            
            
    async def perform_command(self, parts, user, guild) -> Tuple[str, str]:   
           
            if len(parts) == 0:
                return "Use: !command", ""
                  
            elif parts[0] == "ping":
                return f"Pong ({round(self.latency * 1000)} ms)", ""
            
            elif parts[0] == "mute":
                if user.id != 645665079076978688:
                    return "You have no rights to do so", ""
                
                if len(parts) < 2:
                    return "Use: !mute user", ""
                
                user_id = int(parts[1].replace("<","").replace(">","").replace("@","").replace("!",""))
                if user_id == 645665079076978688:
                    return "You can´t mute yourself", ""
                self.muted_users.append(user_id)
                return f"Muted {parts[1]}", ""
            
            elif parts[0] == "mutelist":
                if len(self.muted_users) == 0:
                    return "No users is muted", ""
                msg = "Muted users:"
                for user in self.muted_users:
                    msg += f"\n\t<@!{user}>"
                return msg, ""
            
            elif parts[0] == "unmute":
                if user.id != 645665079076978688:
                    return "You have no rights to do so", ""
                
                if len(parts) < 2:
                    return "Use: !unmute user", ""
                
                user_id = int(parts[1].replace("<","").replace(">","").replace("@","").replace("!",""))
                if not user_id in self.muted_users:
                    return f"{parts[1]} is not muted", ""
                
                self.muted_users.remove(user_id)
                return f"Unmuted {parts[1]}", ""
                    
                    
                
            elif parts[0] == "say":
                return " ".join(parts[1:]), ""
            
            elif parts[0] == "translate":
                if parts[1] == "languages":
                    msg = "```languages for translation:\n"
                    
                    for key, value in googletrans.LANGUAGES.items():
                        msg+=f"\t{key} : {value}\n"
                    return msg + "```", ""
                
                else:
                    if not len(parts) < 4:
                        if not parts[1] in googletrans.LANGUAGES:
                            return f"{parts[1]} is not a valid language", "" 
                        if not parts[2] in googletrans.LANGUAGES:
                            return f"{parts[2]} is not a valid language", ""
                        
                        text = " ".join(parts[3:])
                        trans_text = googletrans.Translator().translate(text, parts[2], parts[1]).text
                        return trans_text, ""
                    return "Use: !translate src des text to translate", ""       
            
            
            elif parts[0] == "selfie":
                image = random.choice(os.listdir("selfies"))
                return "", f"selfies\\{image}"
            
            elif parts[0] == "lasagne":
                return "", "images\\lasagne.png"
            
            elif parts[0] == "mandelbrot":
                return "", "images\\mandelbrot.jpg"
            
            elif parts[0] == "gewicht":
                return "Bot crashed. Integer overflow", ""
            
            
            elif parts[0] == "aufgabe": 
                return "Zurzeit gibt es keine Aufgabe", ""
        
            elif parts[0] == "connect":
                if user.voice == None:
                    return "You have to be in a voicechannel", ""
                
                self.check_sound_player(guild)     
                          
                success = await self.sound_players[guild.id].connect(user.voice.channel)
                if success:
                    return f"Connected to voice channel ```{str(user.voice.channel)}```", ""
                else:
                    return "Already connected to a voice channel", ""              
                  
            elif parts[0] == "disconnect":
                if not guild.id in self.sound_players:
                    return f"Bot isn´t in a voice channel", " "
                success = await self.sound_players[guild.id].disconnect()
                if success:
                    return f"Disconnected from voice channel {str(user.voice.channel)}", ""
                else:
                    return "Bot isn´t in a voice channel", ""
                
                
            elif parts[0] == "pause":
                self.check_sound_player(guild) 
                success = self.sound_players[guild.id].pause()
                if success:
                    return "Sound paused", ""
                else:
                    return "Bot isn´t in a voice channel", ""               
                    
                
            elif parts[0] == "resume":
                self.check_sound_player(guild) 
                success = self.sound_players[guild.id].resume()
                if success:
                    return "Sound resumed", ""
                else:
                    return "Bot isn´t in a voice channel", ""
            
            elif parts[0] == "clear":
                self.check_sound_player(guild) 
                amount = self.sound_players[guild.id].clear()
                return f"Cleared {amount} audios", ""
            
            elif parts[0] == "skip":
                self.check_sound_player(guild) 
                self.sound_players[guild.id].skip()
                return "Skipped", ""
            
                        
            elif parts[0] == "queue":
                self.check_sound_player(guild) 
                queue = self.sound_players[guild.id].queue
                if len(queue) == 0:
                    return "Queue is empty", ""
                else:
                    msg = "Queue:"
                    for name, sound in queue:
                        msg += f"\n\t{name}"
                    return f"```{msg}```", ""

            elif parts[0] == "nowplaying":
                self.check_sound_player(guild) 
                sound = self.sound_players[guild.id].now_playing
                if sound == None:
                    return "Currently now sound is playing", ""
                else:
                    return f"```{sound[0]}```", ""

            elif parts[0] == "sound":
                if len(parts) == 1:
                    return "Use: !sound file", ""
                path = f"sounds\\{parts[1]}.mp3"
                if os.path.exists(path):
                    self.check_sound_player(guild) 
                    self.sound_players[guild.id].add(parts[1], discord.FFmpegPCMAudio(executable=r"C:\ffmpeg-20200831-4a11a6f-win64-static\bin\ffmpeg.exe", source=path))
                    return "", ""
                else:
                    return f"There is no {parts[1]}.mp3", ""
                
            elif parts[0] == "playlist":
                if len(parts) == 1:
                    return "Use: !playlist name", ""
                path = f"playlists\\{parts[1]}"
                if os.path.isdir(path):
                    self.check_sound_player(guild)
                    
                    songs = os.listdir(path)
                    for song in songs:
                        song_path = f"{path}\\{song}"
                        name = song[:-4:]
                        self.sound_players[guild.id].add(name, discord.FFmpegPCMAudio(executable=r"C:\ffmpeg-20200831-4a11a6f-win64-static\bin\ffmpeg.exe", source=song_path))  
                    return f"Added {len(songs)} songs", ""
                else:
                    return f"There is no {parts[1]} playlist", ""               
            
            elif parts[0] == "tts":
                if parts[1].startswith("!") or parts[1].startswith("."):
                    self.check_sound_player(guild)
                    path = f"temp\\{random.random()}"
                    text = ""
                    if parts[1].startswith("!"):
                        parts_ = parts[1:]
                        parts_[0] = parts_[0][1:]
                        text, _ = await self.perform_command(parts_, user, guild)
                        
                    elif parts[1].startswith("."):
                        parts_ = parts[1:]
                        parts_[0] = parts_[0][1:]
                        text = await self.perform_math_command(" ".join(parts_))
                        
                    gTTS(text=text, lang=self.ttsout, slow=False).save(path)
                    name = ""
                    if len(text) > 15:
                        name = text[:15] + "..."
                    else:
                        name = text
                    self.sound_players[guild.id].add(name, discord.FFmpegPCMAudio(executable=r"C:\ffmpeg-20200831-4a11a6f-win64-static\bin\ffmpeg.exe", source=path))
                    return "", ""
                
                elif parts[1] == "languages":
                    msg = "```languages for tts:\n"
                    for key, value in Utils.gTTS_languages.items():
                        msg+=f"\t{key} : {value}\n"
                    return msg + "```", ""
                
                elif parts[1] == "set":
                    if len(parts) < 3:
                        return "Use !tts set language"
                    else:
                        if parts[2] in Utils.gTTS_languages:
                            if parts[2] in Utils.gTTS_lang_changed:
                                self.ttsout = Utils.gTTS_lang_changed[parts[2]]
                            else:
                                self.ttsout = parts[2]
                            return f"Languages for tts is now {Utils.gTTS_languages[parts[2]]}", ""
                        else:
                            return f"{parts[2]} is not a valid language", ""
                            
                    
                else:
                    return "Use: !tts !command\n!tts languages\n!tts set language", ""
               
            else:
                return f"Unrecognized command **{parts[0]}**", ""   
                          
    async def perform_math_command(self, msg) -> str:
        if "=" in msg:
            parts = msg.replace(" ", "").split("=")
            try:
                parts.remove("")
            except:
                pass
                
            #output
            if len(parts) == 1:
                result, success, msg = MathBot.calculate_string(parts[0])
                if success:
                    if self.mathbotout == "bin":
                        try:
                            result = f"{bin(result)}"
                        except:
                            result = f"Can´t converted to binary\nResult: {result}" 
                                
                    if self.mathbotout == "oct":
                        try:
                            result = f"{oct(result)}"
                        except:
                            result = f"Can´t converted to octal\nResult: {result}"  
                                        
                    elif self.mathbotout == "dec":
                        result =  f"{result}"
                        
                    elif self.mathbotout == "hex":
                        try:
                            result = hex(result).upper()
                            result = result.replace("X", "x")
                            result = f"{result}"
                        except:
                            result = f"Can´t converted to hexadecimal\nResult: {result}"                
                    return result
                else:
                    return f"{msg}"
                    
            #save in variable
            elif len(parts) == 2:
                result, success, msg = MathBot.calculate_string(parts[1])
                if success:
                    #variable in use
                    if parts[0] in MathBot.functions or  parts[0] in MathBot.std_variables:
                        return f"The name **{parts[0]}** is already defined"
                    #vaiable available
                    else:
                        MathBot.variables.update({parts[0] : result})
                        return f"The variable **{parts[0]}** is **{result}**"
                else:
                    return f"{msg}"
            else:
                return f"There are more than on \"**=**\""
        
        else:
            parts = msg.lower().split()
            if parts[0] == "reset":
                num = len(MathBot.variables)
                MathBot.variables = {}
                return f"Deleted {num} variables"
            
            elif parts[0] == "variables":
                msg = ""
                for name, value in MathBot.variables.items():
                    msg+=f"{name} = {value} \n"
                if msg == "":
                        return "No variables defined"                      
                else:
                    return f"```{msg}```"
            
            elif parts[0] == "functions":
                msg = "Available functions:\n"
                for name in MathBot.functions:
                    msg+=f"\t{name}\n"
                return f"```{msg}```"
            
            elif parts[0] == "bin":
                if len(parts) > 1:
                    result = ""
                    try:
                        num = int(parts[1], 2)
                        num_bin = bin(num).split("b")[1]   
                        num_oct = oct(num).split("o")[1]                                       
                        num_hex = hex(num).split("x")[1].upper()
                        return f"```Binary: {num_bin}\nOctal: {num_oct}\nDecimal: {num}\nHexadecimal: {num_hex}```"
                    except:
                        return f"Error in conversion"
                else:
                    self.mathbotout = "bin"
                    return f"Output is set to binary"                  
                
            elif parts[0] == "oct":
                if len(parts) > 1:
                    try:
                        num = int(parts[1], 8)
                        num_bin = bin(num).split("b")[1]
                        num_oct = oct(num).split("o")[1]      
                        num_hex = hex(num).split("x")[1].upper()
                        return f"```Binary: {num_bin}\nOctal: {num_oct}\nDecimal: {num}\nHexadecimal: {num_hex}```"
                    except:
                        return "Error in conversion"
                else:
                    self.mathbotout = "oct"
                    return "Output is set to octal"                  
            
            elif parts[0] == "dec":
                if len(parts) > 1:
                    try:
                        num = int(parts[1])
                        num_bin = bin(num).split("b")[1]   
                        num_oct = oct(num).split("o")[1]                                     
                        num_hex = hex(num).split("x")[1].upper()
                        return f"```Binary: {num_bin}\nOctal: {num_oct}\nDecimal: {num}\nHexadecimal: {num_hex}```"
                    except:
                        return f"Error in conversion"
                else:
                    self.mathbotout = "dec"
                    return f"Output is set to decimal"                 
            
            
            elif parts[0] == "hex":
                if len(parts) > 1:
                    try:
                        num = int(parts[1], 16)
                        num_bin = bin(num).split("b")[1]  
                        num_oct = oct(num).split("o")[1]                                        
                        num_hex = hex(num).split("x")[1].upper()
                        return f"```Binary: {num_bin}\nOctal: {num_oct}\nDecimal: {num}\nHexadecimal: {num_hex}```"
                    except:
                        return f"Error in conversion"
                else:
                    self.mathbotout = "hex"
                    return "Output is set to hexadecimal"                 
            
            elif parts[0] == "?":
                return "A bot for mathematical operations"
            
            else:
                return f"Unrecognized command **{parts[0]}**"    
            
            
            
bot = DiscordBot()
bot.run(TOKEN)
