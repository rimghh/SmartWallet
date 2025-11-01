import os
from datetime import date
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# ==================== CONFIG ====================
st.set_page_config(
    page_title="💶 SmartWallet",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSV_PATH = "expenses.csv"
USERS_CSV = "users.csv"
REVENUS_CSV = "revenus.csv"

# ==================== INITIALISATION session_state ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_data" not in st.session_state:
    st.session_state.user_data = {}
if "revenus" not in st.session_state:
    st.session_state.revenus = pd.DataFrame(columns=["date", "type", "amount", "source", "owner_email"])
if "expenses" not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=["date", "category", "amount", "desc", "owner_email"])

# ==================== FONCTIONS ====================
@st.cache_data
def load_expenses():
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        if "owner_email" not in df.columns:
            df["owner_email"] = ""  # ajoute la colonne vide si absente
        return df
    return pd.DataFrame(columns=["date", "category", "amount", "desc", "owner_email"])


def save_expenses(df: pd.DataFrame):
    df.to_csv(CSV_PATH, index=False)

def register_user(email, pwd, name, phone):
    if not os.path.exists(USERS_CSV):
        pd.DataFrame(columns=["email", "pwd", "name", "phone"]).to_csv(USERS_CSV, index=False)
    users = pd.read_csv(USERS_CSV)
    if email in users["email"].values:
        return False
    new_user = pd.DataFrame([{"email": email, "pwd": pwd, "name": name, "phone": phone}])
    users = pd.concat([users, new_user], ignore_index=True)
    users.to_csv(USERS_CSV, index=False)
    return True

def authenticate(email, pwd):
    if not os.path.exists(USERS_CSV):
        return None
    users = pd.read_csv(USERS_CSV)
    user = users[(users["email"] == email) & (users["pwd"] == pwd)]
    return user.iloc[0].to_dict() if not user.empty else None

def load_revenus():
    if os.path.exists(REVENUS_CSV):
        df = pd.read_csv(REVENUS_CSV)
        if "owner_email" not in df.columns:
            df["owner_email"] = ""  # ajoute la colonne vide si absente
        return df
    return pd.DataFrame(columns=["date", "type", "amount", "source", "owner_email"])


def save_revenus(df):
    df.to_csv(REVENUS_CSV, index=False)

# ==================== CHARGEMENT INITIAL ====================
st.session_state.expenses = load_expenses() if st.session_state.expenses.empty else st.session_state.expenses
st.session_state.revenus = load_revenus() if st.session_state.revenus.empty else st.session_state.revenus

# ==================== TITRE PRINCIPAL ====================
st.markdown("<h1 style='color:green; text-align:center;'>💶 SmartWallet</h1>", unsafe_allow_html=True)

# ==================== NAVBAR ====================
tabs = ["⚙️ Compte", "Budget total", "💼 Revenus", "📋 Dépenses"]
selected_tab = st.radio("Navigation", tabs, horizontal=True, label_visibility="collapsed")
st.markdown(f"<div style='background-color:#a8e6cf; padding:10px; border-radius:10px; text-align:center; font-weight:600'>{selected_tab}</div>", unsafe_allow_html=True)

# ==================== COMPTE ====================
if selected_tab == "⚙️ Compte":
    st.title("⚙️ Mon compte")
    choice = st.selectbox("Connexion / Inscription", ["Se connecter", "S'enregistrer"])

    if choice == "S'enregistrer":
        new_email = st.text_input("Email", key="reg_email")
        new_pwd = st.text_input("Mot de passe", type="password", key="reg_pwd")
        new_name = st.text_input("Nom complet", key="reg_name")
        new_phone = st.text_input("Téléphone", key="reg_phone")
        if st.button("Créer un compte"):
            ok = register_user(new_email, new_pwd, new_name, new_phone)
            st.success("Compte créé ! Connectez-vous.") if ok else st.error("Email déjà utilisé.")
    else:
        email = st.text_input("Email", key="login_email")
        pwd = st.text_input("Mot de passe", type="password", key="login_pwd")
        if st.button("Se connecter"):
            user_data = authenticate(email, pwd)
            if user_data:
                st.session_state.logged_in = True
                st.session_state.user_data = user_data
                st.success(f"Connecté(e) : {email}")
            else:
                st.error("Email ou mot de passe incorrect.")

    if st.session_state.logged_in:
        st.subheader("📄 Mes données personnelles")
        user = st.session_state.user_data
        st.write(f"**Nom :** {user.get('name','')}")
        st.write(f"**Email :** {user.get('email','')}")
        st.write(f"**Téléphone :** {user.get('phone','')}")

# ==================== REVENUS ====================
elif selected_tab == "💼 Revenus" and st.session_state.logged_in:
    st.title("💼 Revenus")
    with st.form("ajout_revenu"):
        source = st.text_input("Source du revenu (ex: Salaire)")
        montant = st.number_input("Montant (€)", min_value=0.0, step=10.0)
        date_revenu = st.date_input("Date du revenu")
        type_revenu = st.selectbox("Type de revenu", ["Fixe", "Variable"])
        if st.form_submit_button("Ajouter"):
            if source and montant > 0:
                nouveau = {
                    "source": source,
                    "amount": montant,
                    "date": str(date_revenu),
                    "type": type_revenu,
                    "owner_email": st.session_state.user_data["email"]
                }
                st.session_state.revenus = pd.concat([st.session_state.revenus, pd.DataFrame([nouveau])], ignore_index=True)
                save_revenus(st.session_state.revenus)
                st.success("Revenu ajouté !")
            else:
                st.warning("Veuillez saisir une source et un montant valide.")

    user_revenus = st.session_state.revenus[st.session_state.revenus["owner_email"] == st.session_state.user_data["email"]]
    if not user_revenus.empty:
        st.subheader("Historique des revenus")
        st.dataframe(user_revenus)
    else:
        st.info("Aucun revenu enregistré.")

# ==================== DÉPENSES ====================
elif selected_tab == "📋 Dépenses" and st.session_state.logged_in:
    st.title("📋 Suivi des dépenses")
    c1, c2 = st.columns(2)
    with c1:
        d = st.date_input("Date", value=date.today())
        cat = st.selectbox("Catégorie", ["Alimentation","Transport","Logement","Shopping","Autres"])
    with c2:
        amount = st.number_input("Montant (€)", min_value=0.0, step=1.0)
        desc = st.text_input("Description (facultatif)")
    if st.button("➕ Ajouter la dépense"):
        if amount > 0:
            new_row = {
                "date": d.isoformat(),
                "category": cat,
                "amount": amount,
                "desc": desc,
                "owner_email": st.session_state.user_data["email"]
            }
            st.session_state.expenses = pd.concat([st.session_state.expenses, pd.DataFrame([new_row])], ignore_index=True)
            save_expenses(st.session_state.expenses)
            st.success("Dépense ajoutée !")
        else:
            st.warning("Montant doit être > 0")

    user_expenses = st.session_state.expenses[st.session_state.expenses["owner_email"] == st.session_state.user_data["email"]]
    st.subheader("Historique des dépenses")
    st.dataframe(user_expenses, use_container_width=True)
    total_dep = user_expenses["amount"].sum() if not user_expenses.empty else 0.0
    st.metric("💵 Total des dépenses", f"{total_dep:.2f} €")

# ==================== BUDGET ====================
elif selected_tab == "Budget total" and st.session_state.logged_in:
    st.header("💰 Gestion du Budget")
    user_email = st.session_state.user_data["email"]
    user_revenus = st.session_state.revenus[st.session_state.revenus["owner_email"] == user_email]
    user_expenses = st.session_state.expenses[st.session_state.expenses["owner_email"] == user_email]

    total_revenu = user_revenus["amount"].sum() if not user_revenus.empty else 0.0
    total_dep = user_expenses["amount"].sum() if not user_expenses.empty else 0.0
    budget_restant = total_revenu - total_dep

    if total_revenu == 0:
        st.info("Ajoutez des revenus pour voir le budget.")
    elif budget_restant < 0:
        st.warning("⚠️ Vos dépenses dépassent vos revenus !")
    else:
        st.subheader("Résumé du budget")
        st.write(f"**Revenus :** {total_revenu:.2f} €")
        st.write(f"**Dépenses :** {total_dep:.2f} €")
        st.write(f"**Budget restant :** {budget_restant:.2f} €")

        # Graphe circulaire
        labels = ["Dépenses", "Budget restant"]
        values = [total_dep, budget_restant]
        fig, ax = plt.subplots()
        ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
        ax.axis("equal")
        st.pyplot(fig)