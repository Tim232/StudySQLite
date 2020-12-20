import datetime
import sqlite3

import discord
from discord.ext import commands

conn = sqlite3.connect("main.db")
cur = conn.cursor()


class Punishment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="경고")
    @commands.has_permissions(administrator=True)
    async def warn(self, ctx, member: discord.Member, *, reason="사유 미작성"):
        cur.execute(f"SELECT * FROM WARNS WHERE user_id={member.id}")
        warnings = cur.fetchall()
        check = 1 + len(warnings)

        cur.execute(f"INSERT INTO WARNS(user_id, reason) VALUES(?, ?)", (member.id, reason))
        conn.commit()

        cur.execute(f"SELECT id FROM WARNS WHERE user_id={member.id}")
        ID = cur.fetchall()[-1][0]

        embed = discord.Embed(title="관리 로그", colour=discord.Colour.red(), timestamp=datetime.datetime.now())
        embed.add_field(name="처벌 내용", value="경고", inline=False)
        embed.add_field(name="유저", value=member.mention)
        embed.add_field(name="관리자", value=ctx.author.mention)
        embed.add_field(name="사유", value=reason, inline=False)
        embed.set_footer(text=f"경고 ID | {ID}")

        await ctx.send(embed=embed)

        if check == 3:
            await member.ban(reason="경고 3회 누적")

            embed = discord.Embed(title="관리 로그", colour=discord.Colour.red(), timestamp=datetime.datetime.now())
            embed.add_field(name="처벌 내용", value="밴", inline=False)
            embed.add_field(name="유저", value=member.mention)
            embed.add_field(name="사유", value="경고 3회 누적", inline=False)

            await ctx.send(embed=embed)

    @commands.command(name="경고삭제")
    @commands.has_permissions(administrator=True)
    async def delete_warns(self, ctx, _id: int):
        cur.execute(f"DELETE FROM WARNS WHERE id= {_id}")
        conn.commit()

        await ctx.send(f"> ID : {_id} 에 해당하는 경고가 삭제되었습니다. ")

    @commands.command(name="경고초기화")
    @commands.has_permissions(administrator=True)
    async def reset_warns(self, ctx, member: discord.Member):
        cur.execute(f"DELETE FROM WARNS WHERE user_id= {member.id}")
        conn.commit()

        await ctx.send(f"> {member.mention} 의 경고를 초기화 하였습니다.")

    @commands.command(name="채금")
    @commands.has_permissions(administrator=True)
    async def mute(self, ctx, member: discord.Member, time: str, *, reason):
        role = discord.utils.get(ctx.guild.roles, name="Muted")

        if role is None:
            role = await ctx.guild.create_role(name="Muted")

            for channel in ctx.guild.channels:
                await channel.set_permissions(role, send_messages=False)

        hour = 0
        minute = 0
        second = 0

        if time == "영구":
            await member.add_role(role)

            cur.execute(f"INSERT INTO MUTES VALUES (?, ?, ?)", (member.id, "영구", reason))
            conn.commit()

            embed = discord.Embed(title="관리 로그", colour=discord.Colour.red(), timestamp=datetime.datetime.now())
            embed.add_field(name="처벌 내용", value="영구 채팅 금지", inline=False)
            embed.add_field(name="유저", value=member.mention)
            embed.add_field(name="관리자", value=ctx.author.mention)
            embed.add_field(name="사유", value=reason, inline=False)

            return await ctx.send(embed=embed)

        a = [time]
        if time.find("h") != -1:
            a = a[0].split("h")
            hour = a.pop(0).strip()

        if time.find("m") != -1:
            a = a[0].split("m")
            minute = a.pop(0).strip()

        if time.find("s") != -1:
            a = a[0].split("s")
            second = a.pop(0).strip()

        await member.add_roles(role)

        ending = datetime.datetime.now() + datetime.timedelta(hours=int(hour), minutes=int(minute), seconds=int(second))
        ending = ending.strftime('%Y-%m-%d %H:%M:%S')

        cur.execute(f"INSERT INTO ON_MUTED VALUES (?, ?, ?)", (member.id, ending, ctx.guild.id))
        conn.commit()
        cur.execute(f"INSERT INTO MUTES VALUES (?, ?, ?)", (member.id, time, reason))
        conn.commit()

        embed = discord.Embed(title="관리 로그", colour=discord.Colour.red(), timestamp=datetime.datetime.now())
        embed.add_field(name="처벌 내용", value=f"{time} 채팅 금지", inline=False)
        embed.add_field(name="유저", value=member.mention)
        embed.add_field(name="관리자", value=ctx.author.mention)
        embed.add_field(name="사유", value=reason, inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="채금종료")
    @commands.has_permissions(administrator=True)
    async def delete_mute(self, ctx, member: discord.member):
        cur.execute(f"DELETE FROM ON_MUTED WHERE user_id= {member.id}")
        conn.commit()

        role = discord.utils.get(ctx.guild.roles, name="Muted")

        await member.remove_roles(role)
        await ctx.send("> 채팅금지가 종료되었습니다.")


def setup(bot):
    bot.add_cog(Punishment(bot))
