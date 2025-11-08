import discord
from discord.ext import commands
import uuid
import os
import sys
import json

# File location for JSON
DATA_FILE = os.path.join(os.path.dirname(__file__), "pets.json")
pets = []

# ---------------------------
# JSON LOAD / SAVE FUNCTIONS
# ---------------------------

def load_pets():
    global pets
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                pets = json.load(f)
        except json.JSONDecodeError:
            pets = []
    else:
        pets = []


def save_pets():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(pets, f, indent=4, ensure_ascii=False)


# ---------------------------
# BOT SETUP
# ---------------------------

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    load_pets()

    dog_art = r"""
   /\ 
  /  \__
 (     @\___
 /          O
/    (_____/  I am online!
/\_____/   
"""
    print(dog_art)


# ---------------------------
# COMMAND: ADD PET
# ---------------------------

@bot.command(name="addpet")
async def add_pet(ctx, *, args: str):
    """
    Add a pet using comma-separated fields:
    !addpet name, breed, playroom, jack, jim, jerry
    """

    parts = [p.strip() for p in args.split(",")]

    if len(parts) < 4:
        await ctx.send("Use format: !addpet name, breed, playroom, sep1,sep2,sep3")
        return

    name = parts[0]
    breed = parts[1]
    playroom = parts[2]

    # FIX: All items after index 2 go into separations
    separations = [p.strip() for p in parts[3:] if p.strip()]

    pet_id = str(uuid.uuid4())[:8]

    pet = {
        "id": pet_id,
        "name": name,
        "Breed / Description": breed,
        "playroom": playroom,
        "Keep separate from": separations
    }

    pets.append(pet)
    save_pets()

    await ctx.send(f"Added pet {name} with ID {pet_id}.")





# Delete pet by ID
@bot.command(name="delpet")
async def delete_pet(ctx, pet_id: str):
    """Delete a pet from the database using its ID."""
    global pets

    for pet in pets:
        if pet.get("id") == pet_id:
            name = pet.get("name", "Unknown")
            pets.remove(pet)
            save_pets()
            await ctx.send(f"Deleted {name} (ID: {pet_id}) from the database.")
            return

    await ctx.send("Pet not found.")





# ---------------------------
# COMMAND: LIST PETS
# ---------------------------

@bot.command(name="listpets")
async def list_pets(ctx):
    if not pets:
        await ctx.send("No pets added yet.")
        return

    msg = "**Pet List:**\n"
    for pet in pets:
        sep_list = ", ".join(pet.get("Keep separate from", []))
        msg += (
            f"ID: {pet.get('id')} | "
            f"Name: {pet.get('name')} | "
            f"Breed: {pet.get('Breed / Description')} | "
            f"Playroom: {pet.get('playroom')} | "
            f"Keep separate from: {sep_list}\n"
        )

    await ctx.send(msg)

# Search by name 

@bot.command(name="search")
async def search_pets(ctx, *, search_name: str):
    """Search for pets by name (partial match, case-insensitive)."""
    search_name = search_name.lower()

    results = []
    for pet in pets:
        name = pet.get("name", "").lower()
        if search_name in name:  # partial match
            results.append(pet)

    if not results:
        await ctx.send(f"No pets found matching '{search_name}'.")
        return

    msg = f"**Search results for '{search_name}':**\n"

    for pet in results:
        sep_list = ", ".join(pet.get("Keep separate from", []))

        msg += (
            f"\nID: {pet.get('id')}\n"
            f"Name: {pet.get('name')}\n"
            f"Breed / Description: {pet.get('Breed / Description')}\n"
            f"Playroom: {pet.get('playroom')}\n"
            f"Keep separate from: {sep_list}\n"
            f"------------------------\n"
        )

    await ctx.send(msg)



# ---------------------------
# COMMAND: GET PET BY ID
# ---------------------------

@bot.command(name="getpet")
async def get_pet(ctx, pet_id: str):
    for pet in pets:
        if pet.get("id") == pet_id:
            sep_list = ", ".join(pet.get("Keep separate from", []))
            await ctx.send(
                f"ID: {pet.get('id')}\n"
                f"Name: {pet.get('name')}\n"
                f"Breed / Description: {pet.get('Breed / Description')}\n"
                f"Playroom: {pet.get('playroom')}\n"
                f"Keep separate from: {sep_list}"
            )
            return

    await ctx.send("Pet not found.")


# Edit the pet by id

@bot.command(name="editpet")
async def edit_pet(ctx, pet_id: str, field: str, *, new_value: str):
    """
    Edit a pet's fields.
    Usage:
      !editpet <id> name NewName
      !editpet <id> breed NewBreed
      !editpet <id> playroom NewRoom
      !editpet <id> sep add NameToAdd
      !editpet <id> sep remove NameToRemove
    """

    field = field.lower()

    # Find the pet first
    for pet in pets:
        if pet.get("id") == pet_id:

            # -------------------------
            # Edit the NAME
            # -------------------------
            if field == "name":
                old = pet["name"]
                pet["name"] = new_value
                save_pets()
                await ctx.send(f"Name updated from '{old}' to '{new_value}'.")
                return

            # -------------------------
            # Edit the BREED / DESCRIPTION
            # -------------------------
            elif field in ("breed", "description", "breed/description"):
                old = pet["Breed / Description"]
                pet["Breed / Description"] = new_value
                save_pets()
                await ctx.send(f"Breed/Description updated from '{old}' to '{new_value}'.")
                return

            # -------------------------
            # Edit PLAYROOM
            # -------------------------
            elif field == "playroom":
                old = pet["playroom"]
                pet["playroom"] = new_value
                save_pets()
                await ctx.send(f"Playroom updated from '{old}' to '{new_value}'.")
                return

            # -------------------------
            # EDIT SEPARATIONS (add/remove)
            # -------------------------
            elif field == "sep":
                parts = new_value.split(" ", 1)

                if len(parts) < 2:
                    await ctx.send("Format: sep add/remove Value")
                    return

                action = parts[0].lower()
                value = parts[1].strip()

                sep_list = pet.setdefault("Keep separate from", [])

                # Add to list
                if action == "add":
                    if value in sep_list:
                        await ctx.send(f"'{value}' is already in the separation list.")
                        return

                    sep_list.append(value)
                    save_pets()
                    await ctx.send(f"Added '{value}' to the separation list.")
                    return

                # Remove from list
                elif action == "remove":
                    if value not in sep_list:
                        await ctx.send(f"'{value}' is not in the separation list.")
                        return

                    sep_list.remove(value)
                    save_pets()
                    await ctx.send(f"Removed '{value}' from the separation list.")
                    return

                else:
                    await ctx.send("Use: sep add <name> OR sep remove <name>")
                    return

            else:
                await ctx.send("Unknown field. Valid fields: name, breed, playroom, sep")
                return

    await ctx.send("Pet not found.")





# ---------------------------
# COMMAND: ADD TO SEPARATION LIST
# ---------------------------

@bot.command(name="addsep")
async def add_separation(ctx, pet_id: str, *, name_to_add: str):
    for pet in pets:
        if pet.get("id") == pet_id:

            sep_list = pet.setdefault("Keep separate from", [])

            if name_to_add in sep_list:
                await ctx.send(f"{name_to_add} is already in the separation list.")
                return

            sep_list.append(name_to_add)
            save_pets()
            await ctx.send(f"Added {name_to_add} to {pet['name']}'s separation list.")
            return

    await ctx.send("Pet not found.")


# ---------------------------
# COMMAND: REMOVE FROM SEPARATION LIST
# ---------------------------

@bot.command(name="removesep")
async def remove_separation(ctx, pet_id: str, *, name_to_remove: str):
    for pet in pets:
        if pet.get("id") == pet_id:

            sep_list = pet.get("Keep separate from", [])

            if name_to_remove not in sep_list:
                await ctx.send(f"{name_to_remove} is not in the separation list.")
                return

            sep_list.remove(name_to_remove)
            save_pets()
            await ctx.send(f"Removed {name_to_remove} from {pet['name']}'s separation list.")
            return

    await ctx.send("Pet not found.")





# ---------------------------
# SHUTDOWN 
# ---------------------------

@bot.command(name="shutdown")
@commands.has_permissions(administrator=True)
async def shutdown(ctx):
    await ctx.send("Shutting down...")
    await bot.close()

# ---------------------------
# Restart bot
# ---------------------------

@bot.command(name="restart")
@commands.has_permissions(administrator=True)
async def restart(ctx):
    await ctx.send("Restarting bot...")
    await bot.close()
    os.execv(sys.executable, ["python"] + sys.argv)

# ---------------------------
# Help Command
# ---------------------------

@bot.command(name="helpme")
async def help_command(ctx):
    msg = (
        "**BadDog List Bot Commands**\n"
        "-----------------------------------\n"
        "**!addpet name, breed, playroom, sep1, sep2, sep3**\n"
        "Add a new pet. Example:\n"
        "  !addpet Toby, Shih Poo, Toy, Jack, Jim, Jerry\n\n"

        "**!listpets**\n"
        "Show all pets and their information.\n\n"

        "**!search name**\n"
        "Search for pets by name (partial match).\n"
        "Example:\n"
        "  !search Toby\n\n"

        "**!getpet <id>**\n"
        "View detailed information about a pet.\n"
        "Example:\n"
        "  !getpet abc12345\n\n"

        "**!addsep <id> <name>**\n"
        "Add a name to a pet's separation list.\n"
        "Example:\n"
        "  !addsep abc12345 Jack\n\n"

        "**!removesep <id> <name>**\n"
        "Remove a name from a pet's separation list.\n"
        "Example:\n"
        "  !removesep abc12345 Jack\n\n"

        "**!editpet <id> field value**\n"
        "Edit a pet's properties.\n"
        "Fields:\n"
        "  name <new name>\n"
        "  breed <new breed>\n"
        "  playroom <new room>\n"
        "  sep add <name>\n"
        "  sep remove <name>\n"
        "Examples:\n"
        "  !editpet abc12345 name Luna\n"
        "  !editpet abc12345 breed Husky Mix\n"
        "  !editpet abc12345 sep add Toby\n\n"

        "**!delpet <id>**\n"
        "Delete a pet by ID.\n"
        "Example:\n"
        "  !delpet abc12345\n\n"

        "**!shutdown** (owner only)\n"
        "Turn the bot off.\n\n"

        "**!restart** (owner only)\n"
        "Restart the bot.\n"
    )

    await ctx.send(msg)





# ---------------------------
# RUN BOT
# ---------------------------

bot.run("TOKEN GOES HERE")
