import discord
from discord.ext import commands 
import requests
import io
import aiohttp
import random
import traceback
import xml.etree.ElementTree as ET

class AnimeArtCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.danbooru_url = 'https://danbooru.donmai.us'
        self.safebooru_url = 'https://safebooru.org'
        self.danbooru_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36', 
                #'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                #'Accept-Encoding': 'gzip, deflate, br',
                'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Brave";v="108"',
                'if-none-match':'W/"37ca6f8b1f9c2e77419c12599351968c"'
            }

    @commands.command(name="search_tags", aliases=["autocomplete","tags"], help="Autocomplete tags for search in booru image boards")
    async def search_tags(self, ctx: commands.Context, *args):
        if len(args) < 1:
            return await ctx.send('It is required at least 1 tag.')
        tags = " ".join(args)
        try: 
            message = await ctx.send('Searching tags...')
            tags = await self.autocomplete(tags)
            tag_str = """Tags:"""
            for tag in tags:
                tag_str = tag_str+f'\n`{tag}`'
            #await ctx.send(tag_str)
            await message.edit(content=tag_str)
        except Exception as e: 
            print("Error",  e.__class__, e)
            print(traceback.format_exc())
            await ctx.send(f"Error {e.__class__} in searching tags: {e}")

    async def autocomplete(self, tags):
        async with aiohttp.ClientSession() as session:
                async with session.get(url=f'{self.danbooru_url}/autocomplete.json?search[query]={tags}&search[type]=tag_query&version=1&limit=10') as resp:
                    if resp.status != 200 and resp.status != 304:
                        raise ValueError(f'Response Status code: {resp.status}')
                    response_tags = await resp.json()
                    return [tag['value'] for tag in response_tags]


    @commands.command(name="danbooru", aliases=["danb","dbooru"], help="Search an image from Danbooru")
    async def danbooru(self, ctx: commands.Context, *args):
        if len(args) < 1:
            return await ctx.send('It is required at least 1 tag.')
        try: 
            message = await ctx.send('Searching tags...')
            tags = []
            for arg in args:
                tag_fixed = await self.autocomplete(arg)
                if len(tag_fixed) == 0:
                    return await message.edit(content= 'Tag not found.')
                tags.append(tag_fixed[0])
            await message.edit(content='Getting posts...')
            r = requests.get(url = f'{self.danbooru_url}/posts.json?tags={"+".join(tags)}', headers=self.danbooru_headers)
            #print(f'{self.danbooru_url}/posts.json?tags={"+".join(tags)}')
            if  r.status_code != 200 and r.status_code != 304:
                raise ValueError(f'Error getting posts. Status code: {r.status_code}')
            danb_data = r.json()

            selected_image = danb_data[random.randint(0,len(danb_data)-1)]
            while (not 'file_url' in selected_image):
                selected_image = danb_data[random.randint(0,len(danb_data)-1)]
            
            await message.edit(content='Downloading file...')
            async with aiohttp.ClientSession() as session:
                async with session.get(selected_image['file_url']) as resp:
                    if resp.status != 200:
                        return await ctx.send('Could not download file...')
                    data = io.BytesIO(await resp.read())
                    #await message.edit(content='File downloaded')
                    await message.edit(content=f'Tags: `{tags}`', attachments=[discord.File(data, filename=f'{selected_image["md5"]}.{selected_image["file_ext"]}')])
        except Exception as e: 
            print("Error",  e.__class__, e)
            print(traceback.format_exc())
            await ctx.send(f"Error {e.__class__}: {e}")

    @commands.command(name="random", aliases=["danrandom"], help="Search a random image from Danbooru")
    async def random(self, ctx: commands.Context, *args):
        try: 
            #print(f'URL: {self.danbooru_url}/posts/random.json')
            message = await ctx.send('Getting post...')
            r = requests.get(url = f'{self.danbooru_url}/posts/random.json', headers = self.danbooru_headers)
            if r.status_code != 200:
                raise ValueError(f'Response Status code: {r.status_code}')
            danb_data = r.json()
            await message.edit(content='Downloading file...')
            async with aiohttp.ClientSession() as session:
                if not 'file_url' in danb_data:
                    random(ctx, args)
                async with session.get(danb_data['file_url']) as resp:
                    if resp.status != 200:
                        return await ctx.send('Could not download file...')
                    data = io.BytesIO(await resp.read())
                    if danb_data['tag_string_character'] != '':
                        name = f'{danb_data["tag_string_character"]}'
                    else:
                        name = danb_data['tag_string_general'].rsplit(' ')
                    await message.edit(content=f'Tags: `{name}`', attachments=[discord.File(data, filename=f'{danb_data["md5"]}.{danb_data["file_ext"]}')])
        except Exception as e: 
            print("Error",  e.__class__, e)
            print(traceback.format_exc())
            await ctx.send(f"Error {e.__class__}: {e}")
    
    @commands.command(name="safebooru", aliases=["safe"], help="Search an image from Safebooru")
    async def safebooru(self, ctx: commands.Context, *args):
        message = await ctx.send('Searching tags...')
        tags = "+".join(args)
        params = {
            'page':'dapi',
            's':'post',
            'q':'index',
            'limit':20,
            'tags': tags
        }
        try: 
            await message.edit(content='Getting posts...')
            r = requests.get(url = f'{self.safebooru_url}/index.php', params = params)
            if r.status_code != 200:
                raise ValueError(f'Response Status code: {r.status_code}')
            safe_tree = ET.fromstring(r.content)
            #print(safe_tree[0].attrib)
            #await ctx.send(f"Status Code: {r.status_code}")
            #await ctx.send(f'Retrieved {len(safe_tree)} images')
            selected_image = safe_tree[random.randint(0,len(safe_tree))].attrib
            await message.edit(content='Downloading file...')
            async with aiohttp.ClientSession() as session:
                async with session.get(selected_image['file_url']) as resp:
                    if resp.status != 200:
                        return await ctx.send('Could not download file...')
                    data = io.BytesIO(await resp.read())
                    ext = selected_image["file_url"][selected_image["file_url"].rindex('.')+1:]
                    #await ctx.send(file=discord.File(data, filename=f'{selected_image["md5"]}.{ext}'))
                    await message.edit(content=f'Tags: `{tags}`', attachments=[discord.File(data, filename=f'{selected_image["md5"]}.{ext}')])
        except Exception as e: 
            print("Error",  e.__class__, e)
            print(traceback.format_exc())
            await ctx.send(f"Error requesting: {e}")