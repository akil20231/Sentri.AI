from __future__ import annotations
import time
import discord
from typing import Optional, List

class CooldownManager:
    def __init__(self):
        self.cooldowns: dict[int, int] = {}  # user_id -> unix ts

    def set(self, user_id: int, seconds: int) -> None:
        self.cooldowns[user_id] = int(time.time()) + seconds

    def active(self, user_id: int) -> bool:
        return int(time.time()) < self.cooldowns.get(user_id, 0)

async def ensure_quarantine_role(guild: discord.Guild, role_name: str) -> discord.Role:
    role = discord.utils.get(guild.roles, name=role_name)
    if role:
        return role
    role = await guild.create_role(name=role_name, reason="AgentGuard quarantine role")
    return role

async def apply_quarantine(
    member: discord.Member,
    role: discord.Role
) -> None:
    if role not in member.roles:
        await member.add_roles(role, reason="AgentGuard quarantine")

def build_reason_embed(title: str, risk: float, agent: float, harm: float, reasons: List[str]) -> discord.Embed:
    emb = discord.Embed(title=title, description=f"Risk: **{risk:.2f}** (agent {agent:.2f}, harm {harm:.2f})")
    emb.add_field(name="Why", value="\n".join(f"• {r}" for r in reasons[:6]), inline=False)
    emb.set_footer(text="AgentGuard: soft actions first. Use /appeal if this is wrong.")
    return emb
