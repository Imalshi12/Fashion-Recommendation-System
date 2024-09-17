import secrets

# Generate a strong secret key
secret_key = secrets.token_hex(32)  # Generates a 64-character hex string
print(secret_key)