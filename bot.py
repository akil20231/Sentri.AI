from __future__ import annotations
import time
import discord
from discord.ext import commands

from config import get_settings
from db import init_db, insert_event, insert_decision
from features import UserState, update_state, extract_features, has_link
from scoring import agent_score, harm_score, final_risk
from moderation import CooldownManager, ensure_quarantine_role, apply_quarantine, build_reason_embed
from challenge import ChallengeStore, VerifyView, check_challenge

S = get_settings()
init_db()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

user_states: dict[int, UserState] = {}
cooldowns = CooldownManager()
challenges = ChallengeStore()

# trust window after passing verification
trust_until: dict[int, int] = {}

def get_state(user_id: int) -> UserState:
    if user_id not in user_states:
        user_states[user_id] = UserState()
    return user_states[user_id]

def in_trust_window(user_id: int) -> bool:
    return int(time.time()) < trust_until.get(user_id, 0)

@bot.event
async def on_ready():
    print(f"AgentGuard online as {bot.user} (guild={S.guild_id})")

@bot.command()
async def status(ctx: commands.Context):
    await ctx.send(f"✅ AgentGuard running. Tracking {len(user_states)} users. Monitored channels: {len(S.monitored_channels)}")

@bot.command()
@commands.has_permissions(manage_guild=True)
async def setchannels(ctx: commands.Context, *channel_ids: int):
    # runtime config convenience: doesn’t persist to env
    S.monitored_channels.clear()
    S.monitored_channels.update(channel_ids)
    await ctx.send(f"✅ Monitored channels updated: {', '.join(str(x) for x in S.monitored_channels)}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def unquarantine(ctx: commands.Context, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name=S.quarantine_role_name)
    if role and role in member.roles:
        await member.remove_roles(role, reason="AgentGuard unquarantine")
        await ctx.send(f"✅ Removed quarantine from {member.mention}")
    else:
        await ctx.send("User is not quarantined (or role missing).")

@bot.command()
async def appeal(ctx: commands.Context):
    await ctx.send("If you think you were flagged incorrectly, a moderator can review logs in #mod-logs. (Hackathon MVP: no full appeal flow.)")

async def log_to_mod_channel(guild: discord.Guild, embed: discord.Embed):
    ch = guild.get_channel(S.mod_log_channel_id)
    if ch:
        await ch.send(embed=embed)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    await bot.process_commands(message)

    if message.guild is None or message.guild.id != S.guild_id:
        return

    if S.monitored_channels and message.channel.id not in S.monitored_channels:
        return

    user_id = message.author.id
    now_ts = int(time.time())

    # If throttled, ignore (but still log event)
    mentions_count = len(message.mentions)
    insert_event(
        ts=now_ts,
        guild_id=message.guild.id,
        channel_id=message.channel.id,
        user_id=user_id,
        message_id=message.id,
        content=message.content,
        has_link=has_link(message.content),
        mentions_count=mentions_count
    )

    # challenge check: if user has an active challenge, see if they passed
    pending = challenges.get(user_id)
    if pending and not pending.get("passed", False):
        expected = pending["a"] + pending["b"]
        if check_challenge(message.content, expected):
            challenges.pass_user(user_id)
            trust_until[user_id] = int(time.time()) + 300  # 5 min trust window
            await message.reply("✅ Verification passed. Thanks! (Reduced scrutiny for 5 minutes.)")
        # continue normal processing too

    if cooldowns.active(user_id):
        return

    # trust window reduces aggressive moderation
    trust = in_trust_window(user_id)

    state = get_state(user_id)
    update_state(state, now_ts, message.content, mentions_count)
    feats = extract_features(state, now_ts)

    a_score, a_reasons = agent_score(feats, message.content)
    h_score, h_reasons = harm_score(feats)
    risk = final_risk(a_score, h_score)

    # if trusted, dampen risk
    if trust:
        risk *= 0.6

    # Decide action
    action = "none"
    reasons = []
    reasons.extend(a_reasons[:3])
    reasons.extend(h_reasons[:3])

    if risk >= S.quarantine_threshold:
        action = "quarantine"
    elif risk >= S.throttle_threshold:
        action = "throttle"
    elif risk >= S.warn_threshold:
        action = "warn"

    # Mid-confidence: challenge
    should_challenge = (0.40 <= a_score <= 0.60) and (risk >= S.warn_threshold) and not trust

    if action == "none" and not should_challenge:
        return

    insert_decision(
        ts=now_ts,
        guild_id=message.guild.id,
        channel_id=message.channel.id,
        user_id=user_id,
        message_id=message.id,
        agent_score=float(a_score),
        harm_score=float(h_score),
        final_risk=float(risk),
        action=action if not should_challenge else "challenge",
        reasons=" | ".join(reasons[:8])
    )

    # Build embed for mod logs
    emb = build_reason_embed(
        title=f"AgentGuard decision: {action if not should_challenge else 'challenge'}",
        risk=risk, agent=a_score, harm=h_score, reasons=reasons
    )
    await log_to_mod_channel(message.guild, emb)

    # Apply actions
    if should_challenge:
        payload = challenges.create(user_id)
        view = VerifyView(challenges, user_id)
        await message.reply(
            "⚠️ Quick verification needed (automation suspected). Click **Verify** to get a short prompt.",
            view=view
        )
        return

    if action == "warn":
        await message.reply(embed=emb)
        return

    if action == "throttle":
        cooldowns.set(user_id, S.throttle_seconds)
        await message.reply(f"⏳ You’re temporarily rate-limited for {S.throttle_seconds}s.", embed=emb)
        return

    if action == "quarantine":
        role = await ensure_quarantine_role(message.guild, S.quarantine_role_name)
        member = message.guild.get_member(user_id)
        if isinstance(member, discord.Member):
            await apply_quarantine(member, role)
            await message.reply("🚧 You’ve been placed in quarantine pending review.", embed=emb)

bot.run(S.token)
