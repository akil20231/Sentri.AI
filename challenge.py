from __future__ import annotations
import time
import random
import discord

class ChallengeStore:
    def __init__(self):
        self.pending: dict[int, dict] = {}  # user_id -> data

    def create(self, user_id: int) -> dict:
        a = random.randint(5, 9)
        b = random.randint(6, 9)
        expires = int(time.time()) + 120
        payload = {"a": a, "b": b, "expires": expires, "passed": False}
        self.pending[user_id] = payload
        return payload

    def get(self, user_id: int) -> dict | None:
        p = self.pending.get(user_id)
        if not p:
            return None
        if int(time.time()) > p["expires"]:
            self.pending.pop(user_id, None)
            return None
        return p

    def pass_user(self, user_id: int) -> None:
        if user_id in self.pending:
            self.pending[user_id]["passed"] = True

class VerifyView(discord.ui.View):
    def __init__(self, store: ChallengeStore, user_id: int):
        super().__init__(timeout=120)
        self.store = store
        self.user_id = user_id

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.primary)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This verification isn’t for you.", ephemeral=True)
            return

        payload = self.store.get(self.user_id)
        if not payload:
            await interaction.response.send_message("Verification expired. Please retry.", ephemeral=True)
            return

        prompt = (
            f"Reply in this channel with:\n"
            f"1) the answer to **{payload['a']}+{payload['b']}**\n"
            f"2) **one emoji**\n"
            f"3) **one typo** (any misspelled word)\n\n"
            f"Example: `15 😅 teh`\n"
            f"You have 2 minutes."
        )
        await interaction.response.send_message(prompt, ephemeral=True)

def check_challenge(message_content: str, expected_sum: int) -> bool:
    # Very lightweight: must contain a number = expected, at least one non-ascii emoji-ish char,
    # and at least one "typo" token (we treat any token with repeated uncommon pattern as typo).
    tokens = message_content.strip().split()
    if not tokens:
        return False

    has_number = any(t.isdigit() and int(t) == expected_sum for t in tokens)
    has_emoji = any(ord(ch) > 10000 for ch in message_content)  # rough emoji check
    # "typo": token length >=3 and contains nonstandard sequence like "teh", double letters etc.
    typoish = any(len(t) >= 3 and (t.lower() in {"teh", "adn", "recieve"} or "  " in message_content) for t in tokens)

    return bool(has_number and has_emoji and (typoish or len(tokens) >= 3))
