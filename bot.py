import discord
from discord.ext import commands
import os
import sys
import json
from cryptography.fernet import Fernet

# Şifreleme anahtarını yükle
with open('secret.key', 'rb') as key_file:
    key = key_file.read()

cipher = Fernet(key)

# Şifrelenmiş verileri JSON dosyasından oku
with open('encrypted_data.json', 'r') as file:
    data = json.load(file)
    encrypted_token = data['ENCRYPTED_TOKEN']
    encrypted_discord_id = data['ENCRYPTED_DISCORD_ID']

# Şifreli verileri çöz
TOKEN = cipher.decrypt(encrypted_token.encode()).decode()
YOUR_DISCORD_ID = int(cipher.decrypt(encrypted_discord_id.encode()).decode())

# Botu başlat
intents = discord.Intents.default()
intents.members = True  # Üyeleri yönetebilmek için gerekli
intents.message_content = True  # Mesaj içeriklerine erişim izni

bot = commands.Bot(command_prefix='!', intents=intents)

# Kayıtlı kullanıcılar listesini tutacak bir dosya adı
REGISTERED_USERS_FILE = 'registered_users.txt'

# Roller için bir dosya adı
ROLES_FILE = 'roles.json'

# Kayıtlı rolünü ve kayıtcı rolünü saklamak için bir değişken
registered_role_id = None
kayitci_role_id = None

def load_roles():
    global registered_role_id, kayitci_role_id
    if os.path.exists(ROLES_FILE):
        with open(ROLES_FILE, 'r') as file:
            roles = json.load(file)
            registered_role_id = roles.get('registered_role_id')
            kayitci_role_id = roles.get('kayitci_role_id')

def save_roles():
    roles = {
        'registered_role_id': registered_role_id,
        'kayitci_role_id': kayitci_role_id
    }
    with open(ROLES_FILE, 'w') as file:
        json.dump(roles, file)

@bot.event
async def on_ready():
    await bot.tree.sync()
    load_roles()
    print(f'Bot {bot.user.name} olarak giriş yaptı ve komutlar senkronize edildi!')

@bot.tree.command(name="kayıtlırol", description="Kayıtlı kullanıcılar için rol belirle (Sadece sunucu sahibi kullanabilir).")
async def kayıtlırol(interaction: discord.Interaction, role: discord.Role):
    global registered_role_id
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("Bu komutu sadece sunucu sahibi kullanabilir.", ephemeral=True)
        return
    
    registered_role_id = role.id
    save_roles()
    await interaction.response.send_message(f'Kayıtlı rol {role.name} olarak ayarlandı!')

@bot.tree.command(name="kayıtcırol", description="Kayıtcı rolü belirle (Sadece sunucu sahibi kullanabilir).")
async def kayitcirol(interaction: discord.Interaction, role: discord.Role):
    global kayitci_role_id
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("Bu komutu sadece sunucu sahibi kullanabilir.", ephemeral=True)
        return
    
    kayitci_role_id = role.id
    save_roles()
    await interaction.response.send_message(f'Kayıtcı rol {role.name} olarak ayarlandı!')

@bot.tree.command(name="kayıtcı", description="Etiketlenen kullanıcıya Kayıtcı rolünü ver.")
async def kayitci(interaction: discord.Interaction, member: discord.Member):
    if kayitci_role_id is None:
        await interaction.response.send_message("Henüz bir Kayıtcı rolü belirlenmedi.", ephemeral=True)
        return

    kayitci_role = interaction.guild.get_role(kayitci_role_id)
    
    if kayitci_role:
        await member.add_roles(kayitci_role)
        await interaction.response.send_message(f'{member.mention} başarıyla {kayitci_role.name} rolü verildi!')
    else:
        await interaction.response.send_message("Belirtilen rol bulunamadı.", ephemeral=True)

@bot.tree.command(name="kayıt", description="Etiketlenen kullanıcıyı kaydet ve rol ver (Sadece Kayıtcı rolü olanlar kullanabilir).")
async def kayıt(interaction: discord.Interaction, member: discord.Member, isim: str, yaş: int):
    if registered_role_id is None:
        await interaction.response.send_message("Henüz bir kayıtlı rolü belirlenmedi.", ephemeral=True)
        return

    kayitci_role = interaction.guild.get_role(kayitci_role_id)
    if kayitci_role_id is None or kayitci_role not in interaction.user.roles:
        await interaction.response.send_message("Bu komutu sadece Kayıtcı rolü olanlar kullanabilir.", ephemeral=True)
        return

    registered_role = interaction.guild.get_role(registered_role_id)
    
    if registered_role:
        if registered_role in member.roles:
            await interaction.response.send_message(f'{member.mention} zaten kayıtlı.', ephemeral=True)
        else:
            await member.add_roles(registered_role)
            with open(REGISTERED_USERS_FILE, 'a') as file:
                file.write(f'{isim} | {yaş} ({member.id})\n')
            
            await interaction.response.send_message(f'{member.mention} başarıyla kaydedildi ve {registered_role.name} rolü verildi!')
    else:
        await interaction.response.send_message("Belirtilen rol bulunamadı.", ephemeral=True)

@bot.tree.command(name="ban", description="Bir kullanıcıyı banla (Sadece yöneticiler kullanabilir).")
async def ban(interaction: discord.Interaction, user: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Bu komutu sadece yöneticiler kullanabilir.", ephemeral=True)
        return
    
    await user.ban(reason=f"{interaction.user.name} tarafından banlandı.")
    await interaction.response.send_message(f'{user.name} başarıyla banlandı!')

@bot.tree.command(name="unban", description="Bir kullanıcının banını kaldır (Sadece yöneticiler kullanabilir).")
async def unban(interaction: discord.Interaction, user_id: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Bu komutu sadece yöneticiler kullanabilir.", ephemeral=True)
        return

    try:
        user = await interaction.guild.fetch_ban(user_id)
        await interaction.guild.unban(user.user)
        await interaction.response.send_message(f'{user.user.name} başarıyla unbanlandı!')
    except discord.NotFound:
        await interaction.response.send_message("Bu kullanıcı banlı değil veya bulunamadı.", ephemeral=True)

@bot.tree.command(name="restart", description="Botu yeniden başlat.")
async def restart(interaction: discord.Interaction):
    if interaction.user.id != YOUR_DISCORD_ID:
        await interaction.response.send_message("Bu komutu sadece bot sahibi kullanabilir.", ephemeral=True)
        return
    
    await interaction.response.send_message("Bot yeniden başlatılıyor...")
    
    # Botu kapatıp yeniden başlatmak için mevcut Python işlemini yeniden başlatır
    os.execv(sys.executable, ['python'] + sys.argv)

# Botu çalıştır
bot.run(TOKEN)

