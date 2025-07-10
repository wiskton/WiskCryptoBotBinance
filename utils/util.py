from datetime import datetime


def log(msg):
    print(msg)
    with open("logs.txt", "a") as f:
        f.write(f"{datetime.now()} | {msg}\n")