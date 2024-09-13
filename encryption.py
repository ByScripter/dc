from cryptography.fernet import Fernet
import json
import os

# Şifreleme anahtarını oluştur veya yükle
KEY_FILE = 'secret.key'
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, 'rb') as key_file:
        key = key_file.read()
else:
    key = Fernet.generate_key()
    with open(KEY_FILE, 'wb') as key_file:
        key_file.write(key)

cipher = Fernet(key)

# Şifrelemek istediğin token ve Discord ID'sini burada gir
TOKEN = ''
YOUR_DISCORD_ID = ''

# Verileri şifrele
encrypted_token = cipher.encrypt(TOKEN.encode()).decode()
encrypted_discord_id = cipher.encrypt(YOUR_DISCORD_ID.encode()).decode()

# Şifrelenmiş verileri JSON dosyasına kaydet
data = {
    "ENCRYPTED_TOKEN": encrypted_token,
    "ENCRYPTED_DISCORD_ID": encrypted_discord_id
}

with open('encrypted_data.json', 'w') as file:
    json.dump(data, file)

print("Veriler başarıyla şifrelendi ve encrypted_data.json dosyasına kaydedildi.")
