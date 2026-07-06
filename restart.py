# auto_restart_monitor.py
# Run this separately - it monitors your selfbot and restarts commands

import discord
from discord.ext import commands
import asyncio
import json
import os
import time
import random
import aiohttp
from datetime import datetime

# ========== CONFIGURATION ==========
TOKEN = os.getenv("TOKEN")
COMMAND_STATE_FILE = "command_state.json"

# ✅ Create the file if it doesn't exist
if not os.path.exists(COMMAND_STATE_FILE):
    with open(COMMAND_STATE_FILE, 'w') as f:
        json.dump({}, f)
    print("Created empty command_state.json")

# ========== COMMAND STATE MANAGEMENT ==========
def load_command_state():
    try:
        with open(COMMAND_STATE_FILE, 'r') as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def save_command_state(data):
    with open(COMMAND_STATE_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def remove_command_state(command_name):
    data = load_command_state()
    if command_name in data:
        del data[command_name]
        save_command_state(data)

def add_command_state(command_name, data):
    state = load_command_state()
    state[command_name] = data
    save_command_state(state)

# ========== LOAD HELPERS ==========
def load_lines(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip()]
    except:
        return []

# ========== BOT CLASS ==========
class AutoRestartBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", self_bot=True)
        self.restored_commands = False
        self.token = os.getenv("TOKEN")
        self.start_time = time.time()
        self.tasks = {}
        self.wordlists = {}
        self.token_pool = []
        self.BEEF_WORDS = []
        self.reaction_emojis = []
        self.autopaste_msgs = {}
        self.stam_msgs = {}
        self.count_tasks = {}
        self.stream_task = None
        self.gc_task = None
        self.aball_tasks = {}
        self.spamall_tasks = {}
        self.multireact_tasks = {}
        self.multistam_tasks = {}
        self.multicount_tasks = {}
        self.multistream_tasks = []
        
    async def setup_hook(self):
        await self._register_commands()
        
    def _register_commands(self):
        @self.command(name='savecommand')
        async def save_cmd(ctx, name: str, *, data: str):
            try:
                data_json = json.loads(data)
                add_command_state(name, data_json)
                await ctx.send(f"Saved command: {name}")
            except:
                await ctx.send("Invalid JSON format")

        @self.command(name='removecommand')
        async def remove_cmd(ctx, name: str):
            remove_command_state(name)
            await ctx.send(f"Removed command: {name}")

        @self.command(name='listcommands')
        async def list_cmds(ctx):
            state = load_command_state()
            if not state:
                await ctx.send("No saved commands")
                return
            msg = "Saved Commands:\n"
            for cmd, data in state.items():
                msg += f"{cmd}: {json.dumps(data)[:100]}\n"
            await ctx.send(msg[:1900])

    async def on_ready(self):
        print(f"Auto-Restart Monitor logged in as {self.user}")
        
        if not self.restored_commands:
            state = load_command_state()
            if state:
                print(f"Restoring {len(state)} command(s)...")
                await asyncio.sleep(3)
                for cmd_name, data in state.items():
                    try:
                        await self.restore_command(cmd_name, data)
                    except Exception as e:
                        print(f"Failed to restore {cmd_name}: {e}")
                self.restored_commands = True
            else:
                print("No saved commands to restore")

    async def restore_ab(self, data):
        channel_id = data['channel_id']
        wordlist = data['wordlist']
        delay = data.get('delay', 1.8)
        
        channel = self.get_channel(channel_id)
        if not channel:
            print(f"Channel {channel_id} not found")
            return
        
        if wordlist not in self.wordlists:
            try:
                with open(f"{wordlist}.txt", 'r') as f:
                    self.wordlists[wordlist] = [l.strip() for l in f.readlines() if l.strip()]
            except:
                print(f"Wordlist {wordlist} not found")
                return
        
        if channel_id in self.tasks:
            self.tasks[channel_id].cancel()
        
        async def sched():
            while True:
                lines = self.wordlists.get(wordlist, [])
                if not lines:
                    await asyncio.sleep(5)
                    continue
                random.shuffle(lines)
                for line in lines:
                    try:
                        await channel.send(line)
                        await asyncio.sleep(delay)
                    except:
                        await asyncio.sleep(5)
        self.tasks[channel_id] = asyncio.create_task(sched())
        print(f"Restored ab in {channel_id} using {wordlist}")

    async def restore_ablow(self, data):
        channel_id = data['channel_id']
        wordlist = data['wordlist']
        delay = data.get('delay', 1.8)
        
        channel = self.get_channel(channel_id)
        if not channel:
            return
        
        if wordlist not in self.wordlists:
            try:
                with open(f"{wordlist}.txt", 'r') as f:
                    self.wordlists[wordlist] = [l.strip() for l in f.readlines() if l.strip()]
            except:
                return
        
        if channel_id in self.tasks:
            self.tasks[channel_id].cancel()
        
        async def sched_lower():
            while True:
                lines = self.wordlists.get(wordlist, [])
                if not lines:
                    await asyncio.sleep(5)
                    continue
                random.shuffle(lines)
                for line in lines:
                    try:
                        await channel.send(line.lower())
                        await asyncio.sleep(delay)
                    except:
                        await asyncio.sleep(5)
        self.tasks[channel_id] = asyncio.create_task(sched_lower())
        print(f"Restored ablow in {channel_id}")

    async def restore_spam(self, data):
        channel = self.get_channel(data['channel_id'])
        if not channel:
            return
        message = data['message']
        delay = data.get('delay', 6)
        channel_id = data['channel_id']
        
        async def sp():
            while True:
                try:
                    await channel.send(message)
                except:
                    await asyncio.sleep(10)
                await asyncio.sleep(delay)
        
        if channel_id in self.tasks:
            self.tasks[channel_id].cancel()
        self.tasks[channel_id] = asyncio.create_task(sp())
        print(f"Restored spam in {channel_id}")

    async def restore_spamall(self, data):
        channel_id = data['channel_id']
        message = data['message']
        
        if not self.token_pool or not message:
            return
        
        for alias, task in list(self.spamall_tasks.items()):
            if not task.done():
                task.cancel()
        self.spamall_tasks.clear()
        
        async def spam_worker(token_info, channel_id, alias, msg):
            token = token_info["token"]
            headers = {"Authorization": token, "Content-Type": "application/json"}
            url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
            async with aiohttp.ClientSession() as session:
                try:
                    while True:
                        payload = {"content": msg}
                        async with session.post(url, json=payload, headers=headers) as resp:
                            if resp.status not in (200, 204):
                                print(f"[Spam] {alias} send failed: {resp.status}")
                        await asyncio.sleep(2)
                except asyncio.CancelledError:
                    return
        
        for token_info in self.token_pool:
            alias = token_info.get("alias", "unknown")
            task = asyncio.create_task(spam_worker(token_info, channel_id, alias, message))
            self.spamall_tasks[alias] = task
            await asyncio.sleep(1)
        print(f"Restored spamall in {channel_id}")

    async def restore_aball(self, data):
        channel_id = data['channel_id']
        wordlist = data.get('wordlist')
        
        if not self.token_pool:
            return
        
        if wordlist:
            if wordlist in self.wordlists:
                self.BEEF_WORDS = self.wordlists[wordlist]
            else:
                lines = load_lines(f"{wordlist}.txt")
                if lines:
                    self.wordlists[wordlist] = lines
                    self.BEEF_WORDS = lines
        
        if self.token_pool and self.BEEF_WORDS:
            for alias, task in list(self.aball_tasks.items()):
                if not task.done():
                    task.cancel()
            self.aball_tasks.clear()
            
            import aiohttp
            async def beef_worker(token_info, channel_id, alias):
                token = token_info["token"]
                headers = {"Authorization": token, "Content-Type": "application/json"}
                url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
                async with aiohttp.ClientSession() as session:
                    while True:
                        word = random.choice(self.BEEF_WORDS)
                        payload = {"content": word}
                        async with session.post(url, json=payload, headers=headers) as resp:
                            if resp.status not in (200, 204):
                                print(f"[Beef] {alias} send failed: {resp.status}")
                        await asyncio.sleep(2)
            
            for token_info in self.token_pool:
                alias = token_info.get("alias", "unknown")
                task = asyncio.create_task(beef_worker(token_info, channel_id, alias))
                self.aball_tasks[alias] = task
                await asyncio.sleep(1)
            print(f"Restored aball in {channel_id}")

    async def restore_autopaste(self, data):
        channel_id = data['channel_id']
        delay = data.get('delay', 1.0)
        messages = data.get('messages', [])
        
        if not messages:
            return
        
        channel = self.get_channel(channel_id)
        if not channel:
            return
        
        self.autopaste_msgs[channel_id] = [(delay, msg) for msg in messages]
        
        if channel_id not in self.tasks:
            async def auto_paste_loop():
                while True:
                    if channel_id not in self.autopaste_msgs or not self.autopaste_msgs[channel_id]:
                        await asyncio.sleep(5)
                        continue
                    for d, m in self.autopaste_msgs[channel_id]:
                        try:
                            ch = self.get_channel(channel_id)
                            if ch:
                                await ch.send(m)
                        except:
                            pass
                        await asyncio.sleep(d)
                    await asyncio.sleep(1)
            self.tasks[channel_id] = asyncio.create_task(auto_paste_loop())
        print(f"Restored autopaste in {channel_id}")

    async def restore_stam(self, data):
        channel_id = data['channel_id']
        delay = data.get('delay', 1.0)
        messages = data.get('messages', [])
        
        if not messages:
            return
        
        channel = self.get_channel(channel_id)
        if not channel:
            return
        
        self.stam_msgs[channel_id] = [(delay, msg) for msg in messages]
        
        if f"stam_{channel_id}" not in self.tasks:
            async def stam_loop():
                counters = [1 for _ in messages]
                while True:
                    if channel_id not in self.stam_msgs or not self.stam_msgs[channel_id]:
                        await asyncio.sleep(5)
                        continue
                    for i, (d, m) in enumerate(self.stam_msgs[channel_id]):
                        try:
                            ch = self.get_channel(channel_id)
                            if ch:
                                await ch.send(f"{m} ({counters[i]})")
                                counters[i] += 1
                        except:
                            pass
                        await asyncio.sleep(d)
                    await asyncio.sleep(1)
            self.tasks[f"stam_{channel_id}"] = asyncio.create_task(stam_loop())
        print(f"Restored stam in {channel_id}")

    async def restore_autocount(self, data):
        channel_id = data['channel_id']
        start = data.get('start', 1)
        end = data.get('end')
        
        channel = self.get_channel(channel_id)
        if not channel:
            return
        
        async def count_loop():
            i = start
            while True:
                try:
                    ch = self.get_channel(channel_id)
                    if ch:
                        await ch.send(str(i))
                    i += 1
                    if end and i > end:
                        break
                    await asyncio.sleep(1)
                except:
                    await asyncio.sleep(2)
        
        if channel_id in self.count_tasks:
            self.count_tasks[channel_id].cancel()
        self.count_tasks[channel_id] = asyncio.create_task(count_loop())
        print(f"Restored autocount in {channel_id}")

    async def restore_stream(self, data):
        texts = data.get('texts', [])
        if not texts:
            return
        
        async def stream_loop():
            index = 0
            while True:
                text = texts[index % len(texts)]
                try:
                    await self.change_presence(activity=discord.Streaming(name=text, url="https://twitch.tv/yourchannel"))
                except:
                    pass
                index += 1
                await asyncio.sleep(15)
        
        if self.stream_task:
            self.stream_task.cancel()
        self.stream_task = asyncio.create_task(stream_loop())
        print(f"Restored stream with {len(texts)} texts")

    async def restore_gcname(self, data):
        channel_id = data['channel_id']
        delay = data.get('delay', 5.0)
        name = data.get('name', 'GC')
        
        if self.gc_task:
            self.gc_task.cancel()
        
        async def gc_loop():
            counter = 1
            while True:
                try:
                    ch = self.get_channel(channel_id)
                    if ch and isinstance(ch, discord.GroupChannel):
                        await ch.edit(name=f"{name} {counter}")
                        counter += 1
                        await asyncio.sleep(delay)
                    else:
                        break
                except:
                    await asyncio.sleep(10)
        
        self.gc_task = asyncio.create_task(gc_loop())
        print(f"Restored gcname in {channel_id}")

    async def restore_multireact(self, data):
        channel_id = data['channel_id']
        emojis = data.get('emojis', [])
        
        if not self.token_pool or not emojis:
            return
        
        import aiohttp
        async def react_worker(token_info, channel_id, alias, emojis):
            token = token_info["token"]
            headers = {"Authorization": token, "Content-Type": "application/json"}
            url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
            async with aiohttp.ClientSession() as session:
                try:
                    msg_ids = []
                    async with session.get(url, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for msg in data:
                                msg_ids.append(msg['id'])
                    for msg_id in msg_ids[:10]:
                        for emoji in emojis:
                            react_url = f"https://discord.com/api/v9/channels/{channel_id}/messages/{msg_id}/reactions/{emoji}/@me"
                            async with session.put(react_url, headers=headers) as resp:
                                pass
                            await asyncio.sleep(0.3)
                        await asyncio.sleep(0.5)
                except asyncio.CancelledError:
                    return
        
        for token_info in self.token_pool:
            alias = token_info.get("alias", "unknown")
            task = asyncio.create_task(react_worker(token_info, channel_id, alias, emojis))
            self.multireact_tasks[alias] = task
            await asyncio.sleep(0.5)
        print(f"Restored multireact in {channel_id}")

    async def restore_multistream(self, data):
        statuses = data.get('statuses', [])
        if not statuses:
            return
        
        token = TOKEN
        if not token:
            print("No token available for multistream restore")
            return
        
        async def stream_worker(stream_name):
            try:
                bot = commands.Bot(command_prefix="!", self_bot=True)
                @bot.event
                async def on_ready():
                    await bot.change_presence(activity=discord.Streaming(name=stream_name, url="https://twitch.tv/yourchannel"))
                await bot.start(token)
            except Exception as e:
                print(f"MultiStream error: {e}")
        
        # Cancel existing tasks
        for task in self.multistream_tasks:
            if not task.done():
                task.cancel()
        self.multistream_tasks.clear()
        
        for name in statuses:
            task = asyncio.create_task(stream_worker(name))
            self.multistream_tasks.append(task)
            await asyncio.sleep(0.5)
        print(f"Restored multistream with {len(statuses)} streams")

    async def restore_multicount(self, data):
        channel_id = data['channel_id']
        start = data.get('start', 1)
        stop = data.get('stop', 100)
        
        if not self.token_pool:
            return
        
        import aiohttp
        async def count_worker(token_info, channel_id, alias, start_num, stop_num, token_index, total_tokens):
            token = token_info["token"]
            headers = {"Authorization": token, "Content-Type": "application/json"}
            url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
            async with aiohttp.ClientSession() as session:
                offset = token_index
                step = total_tokens
                current = start_num + offset
                while current <= stop_num:
                    payload = {"content": str(current)}
                    async with session.post(url, json=payload, headers=headers) as resp:
                        pass
                    current += step
                    await asyncio.sleep(0.8)
        
        total_tokens = len(self.token_pool)
        for i, token_info in enumerate(self.token_pool):
            alias = token_info.get("alias", "unknown")
            task = asyncio.create_task(count_worker(token_info, channel_id, alias, start, stop, i, total_tokens))
            self.multicount_tasks[alias] = task
            await asyncio.sleep(0.3)
        print(f"Restored multicount in {channel_id}")
        
    async def restore_multistam(self, data):
        channel_id = data['channel_id']
        delay = data.get('delay', 2.0)
        message = data.get('message', '')
        
        if not self.token_pool or not message:
            return
        
        import aiohttp
        async def stam_worker(token_info, channel_id, alias, msg, delay):
            token = token_info["token"]
            headers = {"Authorization": token, "Content-Type": "application/json"}
            url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
            async with aiohttp.ClientSession() as session:
                counter = 1
                while True:
                    msg_with_count = f"{msg} ({counter})"
                    payload = {"content": msg_with_count}
                    async with session.post(url, json=payload, headers=headers) as resp:
                        pass
                    counter += 1
                    await asyncio.sleep(delay)
        
        for token_info in self.token_pool:
            alias = token_info.get("alias", "unknown")
            task = asyncio.create_task(stam_worker(token_info, channel_id, alias, message, delay))
            self.multistam_tasks[alias] = task
            await asyncio.sleep(0.5)
        print(f"Restored multistam in {channel_id}")

    async def restore_react(self, data):
        self.reaction_emojis = data.get('emojis', [])
        print(f"Restored react with {len(self.reaction_emojis)} emojis")

    async def restore_command(self, command_name, data):
        restore_map = {
            "ab": self.restore_ab,
            "ablow": self.restore_ablow,
            "spam": self.restore_spam,
            "spamall": self.restore_spamall,
            "aball": self.restore_aball,
            "autopaste": self.restore_autopaste,
            "stam": self.restore_stam,
            "autocount": self.restore_autocount,
            "stream": self.restore_stream,
            "gcname": self.restore_gcname,
            "multireact": self.restore_multireact,
            "multistam": self.restore_multistam,
            "multicount": self.restore_multicount,
            "multistream": self.restore_multistream,
            "react": self.restore_react
        }
        
        if command_name in restore_map:
            try:
                await restore_map[command_name](data)
            except Exception as e:
                print(f"Error restoring {command_name}: {e}")
        else:
            print(f"Unknown command: {command_name}")
            

# ========== RUN ==========
if __name__ == "__main__":
    if not TOKEN:
        print("No token provided!")
        exit()
    
    bot = AutoRestartBot()
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"Error: {e}")
