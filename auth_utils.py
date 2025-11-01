import os
import pandas as pd
import hashlib

USERS_CSV = "users.csv"

# --- Crée le fichier users.csv si absent ---
def ensure_users_csv():
    if not os.path.exists(USERS_CSV):
        pd.DataFrame(columns=["email", "password_hash"]).to_csv(USERS_CSV, index=False)

# --- Fonction pour hasher le mot de passe ---
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

# --- Fonction pour enregistrer un utilisateur ---
def register_user(email: str, password: str) -> bool:
    ensure_users_csv()
    users = pd.read_csv(USERS_CSV)
    if email in users["email"].values:
        return False  # email déjà existant
    pwd_hash = hash_password(password)
    users = pd.concat([users, pd.DataFrame([{"email": email, "password_hash": pwd_hash}])], ignore_index=True)
    users.to_csv(USERS_CSV, index=False)
    return True

# --- Fonction pour authentifier un utilisateur ---
def authenticate(email: str, password: str) -> bool:
    ensure_users_csv()
    users = pd.read_csv(USERS_CSV)
    pwd_hash = hash_password(password)
    matched = users[(users["email"] == email) & (users["password_hash"] == pwd_hash)]
    return not matched.empty
