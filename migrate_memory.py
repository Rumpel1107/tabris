import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import config
from core.db import init_db, create_user, find_user_by_name, save_fact

FACTS = [
    "Name: Rumpel",
    "Background: Scrum Master transitioning to Technical PM / FDE",
    "Based in Madrid-Colombia",
    "Technical level: beginner, learning by building",
    "Communication language: Spanish",
    "Prefers to make all code changes manually as part of the learning process",
    "Prefers explanations in conversation, not inside files",
    "Objective: Build Tabris as a personal/learning project to be finished at functional level, then frozen",
    "Primary goal: generate independent income from a sellable product (Colombian income-tax liquidator) before runway ends",
    "OS: Ubuntu 26.04 LTS",
    "Hardware: Ryzen 7 5700G, 32GB RAM, RTX 3070 8GB VRAM",
    "Editor: VS Code | Version control: Git",
    "Project path: ~/Projects/tabris",
]

if __name__ == "__main__":
    init_db(config.DB_PATH)
    user = find_user_by_name(config.DB_PATH, "Rumpel")
    if user:
        print(f"User already exists: id={user['id']}. Skipping migration.")
    else:
        user_id = create_user(config.DB_PATH, name="Rumpel", language="es")
        for fact in FACTS:
            save_fact(config.DB_PATH, user_id, fact)
        print(f"Migration complete. User id={user_id}, {len(FACTS)} facts saved to {config.DB_PATH}")