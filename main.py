import asyncio
import datetime
import sqlite3

import discord
from discord.ext import commands, tasks

bot = commands.Bot(command_prefix="!!", intents=discord.Intents.all())
bot.load_extension("punishment")

conn = sqlite3.connect("main.db")
cur = conn.cursor()


@bot.event
async def on_ready():
    print(str(bot.user))
    check_mutes.start()


@bot.command(name="이벤트등록")
@commands.has_permissions(administrator=True)
async def add_event(ctx, *, title="이벤트"):
    await ctx.send("> 이벤트 기간을 1분 이내에 작성해주세요.")

    try:
        during = await bot.wait_for(
            "message", timeout=60, check=lambda m: m.author == ctx.author
        )
    except asyncio.TimeoutError:
        return await ctx.send("> 이벤트 등록이 취소되었습니다.")

    await ctx.send("> 이벤트 내용을 1분 이내에 작성해주세요.")

    try:
        msg = await bot.wait_for(
            "message", timeout=60, check=lambda m: m.author == ctx.author
        )
    except asyncio.TimeoutError:
        return await ctx.send("> 이벤트 등록이 취소되었습니다.")

    cur.execute(
        "INSERT INTO EVENT(title, content, during) VALUES (?, ?, ?)",
        (title, msg.content, during.content),
    )
    conn.commit()

    await ctx.send("> 이벤트 등록이 완료되었습니다.")


@bot.command(name="이벤트삭제")
@commands.has_permissions(administrator=True)
async def delete_event(ctx, title):
    try:
        cur.execute(f"DELETE FROM EVENT WHERE title= {title}")
        conn.commit()
    except Exception as e:
        print(e)
        return await ctx.send(f"> 일치하는 이벤트가 존재하지 않습니다. ( {title} )")

    await ctx.send(f"> {title} 이벤트가 삭제 되었습니다.")


@bot.command(name="유저메모")
@commands.has_permissions(administrator=True)
async def memo(ctx, member: discord.Member, *, content):
    cur.execute(f"SELECT * FROM memo WHERE user_id= {member.id}")
    check = cur.fetchone()

    if check is None:
        cur.execute(f"INSERT INTO memo VALUES (?, ?)", (member.id, content))
        conn.commit()
    else:
        cur.execute(f"UPDATE memo SET content = {content} WHERE user_id = {member.id}")
        conn.commit()

    await ctx.send("> 메모 등록이 완료되었습니다.")


@bot.command(name="메모삭제")
@commands.has_permissions(administrator=True)
async def delete_memo(ctx, member: discord.Member):
    cur.execute(f"DELETE FROM memo WHERE user_id= {member.id}")
    conn.commit()

    await ctx.send("> 메모가 삭제되었습니다.")


@bot.command(name="유저정보")
@commands.has_permissions(administrator=True)
async def user_info(ctx, member: discord.Member):
    cur.execute(f"SELECT * FROM WARNS WHERE user_id= {member.id}")
    warns = cur.fetchall()

    warn_count = 0
    reasons = list()
    for i in warns:
        warn_count += 1
        reasons.append(f"( ID : {i[0]} )경고 {bot.get_user(i[1])} {i[2]}")

    cur.execute(f"SELECT * FROM MUTES WHERE user_id= {member.id}")
    mutes = cur.fetchall()

    for i in mutes:
        reasons.append(f"채팅금지 {bot.get_user(i[0])} {i[1]} {i[2]}")

    reasons = "\n".join(reasons)

    memo = "등록된 메모가 없습니다."
    cur.execute(f"SELECT * FROM memo WHERE user_id= {member.id}")
    check_memo = cur.fetchone()

    if check_memo:
        memo = check_memo[1]

    cur.execute(f"SELECT * FROM ON_MUTED WHERE user_id= {member.id}")
    check_mute = cur.fetchone()

    try:
        check_mute = f"채팅금지 {check_mute[1]}"
    except IndexError:
        check_mute = "진행중인 처벌이 없습니다."

    embed = discord.Embed(title=f"{member.name} 님의 정보", colour=discord.Colour.blue())
    embed.add_field(name="현재 경고 횟수", value=f"{warn_count} / 3")
    embed.add_field(name="처벌 기록", value=f"```{reasons}```", inline=False)
    embed.add_field(name="받고있는 처벌", value=f"```{check_mute}```", inline=False)
    embed.add_field(name="메모", value=f"```{memo}```", inline=False)
    embed.set_footer(text=f"{member.name} | {member.id}", icon_url=member.avatar_url)

    await ctx.send(embed=embed)


@bot.command(name="이벤트")
async def check_event(ctx):
    cur.execute("SELECT * FROM EVENT")
    events = cur.fetchall()

    if events is None:
        return await ctx.send("> 등록된 이벤트가 없습니다.")

    for i in events:
        embed = discord.Embed(
            title=i[0], description=i[1], colour=discord.Colour.blue()
        )
        embed.set_footer(text=f"이벤트 기간 | {i[2]}")
        await ctx.send(embed=embed)


@tasks.loop(seconds=2)
async def check_mutes():
    cur.execute("SELECT * FROM ON_MUTED")
    mutes = cur.fetchall()

    for i in mutes:
        role = discord.utils.get(bot.get_guild(i[2]).roles, name="Muted")
        date = datetime.datetime.strptime(i[1], "%Y-%m-%d %H:%M:%S")

        if date < datetime.datetime.now():
            await bot.get_guild(i[2]).get_member(i[0]).remove_roles(role)
            cur.execute("DELETE FROM ON_MUTED WHERE user_id=" + str(i[0]))
            conn.commit()


bot.run("NzsdfWo")
