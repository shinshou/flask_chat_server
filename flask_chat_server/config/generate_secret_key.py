import os

# 24バイトのランダムな秘密鍵を生成
secret_key = os.urandom(24).hex()
# 秘密鍵を表示
print(f"SECRET_KEY = '{secret_key}'")
