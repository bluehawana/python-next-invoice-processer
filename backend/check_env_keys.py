from dotenv import load_dotenv, dotenv_values
import os

# Load explicitly from the .env file
env_vars = dotenv_values(".env")

print(f"--- Available ENV Keys ---")
for key in env_vars.keys():
    print(key)
