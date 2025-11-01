import os
from datetime import date
import pandas as pd
import streamlit as st

# ==================== CONFIG ====================
st.set_page_config(
    page_title="💰 Money Tracker",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSV_PATH = "expenses.csv"
USERS_CSV = "users.csv"

# ==================== FONCTIONS ====================
@st.cache_data
def load_expenses():
    if os.path.exists(CSV_PATH):
        # on force les types pour éviter les surprises
        return pd.read_csv(CSV_PATH, dtype={"date": "string", "category": "string", "amount": "float64", "desc": "string"})
    # DataFrame vide typé
    return pd.DataFrame({
        "date": pd.Series(dtype="string"),
        "category": pd.Series(dtype="string"),
        "amount": pd.Series(dtype="float"),
        "desc": pd.Series(dtype="string"),
    })

def save_expenses(df: pd.DataFrame):
    df.to_csv(CSV_PATH, index=False)

def register_user(email, pwd, name, phone):
    # version pédagogique (mot de passe en clair) — OK pour projet débutant
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
    if not user.empty:
        return user.iloc[0].to_dict()
    return None

# ==================== DONNÉES ====================
expenses_df = load_expenses()

# ==================== NAVBAR (simple CSS facultatif) ====================
st.markdown("""
<style>
.nav { background-color:#a8e6cf; padding:10px; border-radius:10px; display:flex; justify-content:space-around; align-items:center; font-weight:600; }
</style>
""", unsafe_allow_html=True)

tabs = ["⚙️ Compte", "💼 Revenus", "📋 Suivi des dépenses"]
selected_tab = st.radio("Navigation", tabs, horizontal=True, label_visibility="collapsed", key="menu")
st.markdown(f"<div class='nav'><b>{selected_tab}</b></div>", unsafe_allow_html=True)

# ==================== COMPTE ====================
if selected_tab == "⚙️ Compte":
    st.title("⚙️ Mon compte")
    choice = st.selectbox("Connexion / Inscription", ["Se connecter", "S'enregistrer"])

    if choice == "S'enregistrer":
        st.subheader("Créer un nouveau compte")
        new_email = st.text_input("Email", key="reg_email")
        new_pwd = st.text_input("Mot de passe", type="password", key="reg_pwd")
        new_name = st.text_input("Nom complet", key="reg_name")
        new_phone = st.text_input("Téléphone", key="reg_phone")

        if st.button("Créer un compte", key="btn_register"):
            ok = register_user(new_email, new_pwd, new_name, new_phone)
            st.success("Compte créé. Connectez-vous ci-dessous.") if ok else st.error("Cet email est déjà utilisé.")

    else:
        st.subheader("Se connecter")
        email = st.text_input("Email", key="login_email")
        pwd = st.text_input("Mot de passe", type="password", key="login_pwd")

        if st.button("Se connecter", key="btn_login"):
            user_data = authenticate(email, pwd)
            if user_data:
                st.session_state.logged_in = True
                st.session_state.user_data = user_data
                st.success(f"Connecté(e) : {email}")
            else:
                st.error("Email ou mot de passe incorrect.")

    if st.session_state.get("logged_in", False):
        st.subheader("📄 Mes données personnelles")
        user = st.session_state.get("user_data", {})
        st.write(f"**Nom :** {user.get('name','')}")
        st.write(f"**Email :** {user.get('email','')}")
        st.write(f"**Téléphone :** {user.get('phone','')}")

# ==================== REVENUS ====================
elif selected_tab == "💼 Revenus":
    st.title("💰 Gestion des revenus")

    # Stockage simple en session (pas de CSV pour rester léger)
    if "revenus" not in st.session_state:
        st.session_state["revenus"] = pd.DataFrame(columns=["date", "type", "amount", "desc"])
    rev_df = st.session_state["revenus"]

    st.subheader("➕ Ajouter un revenu")
    c1, c2 = st.columns(2)
    with c1:
        date_rev = st.date_input("Date", value=date.today())
        type_rev = st.selectbox("Type de revenu", ["Salaire", "Prime", "Cadeau", "Vente", "Autre"])
    with c2:
        montant_rev = st.number_input("Montant (€)", min_value=0.0, step=10.0)
        desc_rev = st.text_input("Description (facultatif)")

    if st.button("Ajouter le revenu"):
        if montant_rev > 0:
            new_rev = pd.DataFrame([{
                "date": date_rev.isoformat(),
                "type": type_rev,
                "amount": float(montant_rev),
                "desc": desc_rev
            }])
            st.session_state["revenus"] = pd.concat([rev_df, new_rev], ignore_index=True)
            st.success("✅ Revenu ajouté avec succès !")
        else:
            st.warning("⚠️ Entrez un montant > 0 €")

    st.markdown("---")
    st.subheader("📋 Historique des revenus")
    rev_df = st.session_state["revenus"]
    if rev_df.empty:
        st.info("Aucun revenu enregistré pour le moment.")
    else:
        st.dataframe(rev_df, use_container_width=True)
        total_rev = float(rev_df["amount"].sum())
        st.metric("💵 Total des revenus enregistrés", f"{total_rev:,.2f} €".replace(",", " "))

        # Graphique simple par type (clair et suffisant)
        st.subheader("📊 Revenus par type")
        t = rev_df.groupby("type", as_index=False)["amount"].sum()
        st.bar_chart(t, x="type", y="amount", use_container_width=True)

        # (Optionnel) Camembert Revenus vs Dépenses — activable
        show_pie = st.checkbox("Afficher la répartition Revenus vs Dépenses (camembert)")
        if show_pie:
            try:
                dep_df = load_expenses()
                total_dep = float(dep_df["amount"].sum()) if not dep_df.empty else 0.0
            except Exception:
                total_dep = 0.0

            data = pd.DataFrame({
                "Catégorie": ["Revenus", "Dépenses"],
                "Montant (€)": [total_rev, total_dep]
            })

            import altair as alt
            chart = alt.Chart(data).mark_arc().encode(
                theta="Montant (€)",
                color="Catégorie",
                tooltip=["Catégorie", "Montant (€)"]
            )
            st.altair_chart(chart, use_container_width=True)

# ==================== SUIVI DES DÉPENSES ====================
elif selected_tab == "📋 Suivi des dépenses":
    st.title("💰 Money Tracker — Suivi de vos dépenses")

    c1, c2 = st.columns(2)
    with c1:
        d = st.date_input("Date", value=date.today(), key="dep_date")
        cat = st.selectbox("Catégorie", ["Alimentation", "Transport", "Logement", "Shopping", "Autres"], key="dep_cat")
    with c2:
        amount = st.number_input("Montant (€)", min_value=0.0, step=1.0, key="dep_amount")
        desc = st.text_input("Description (facultatif)", key="dep_desc")

    if st.button("➕ Ajouter la dépense"):
        if amount > 0:
            new_row = {"date": d.isoformat(), "category": cat, "amount": float(amount), "desc": desc}
            updated = pd.concat([expenses_df, pd.DataFrame([new_row])], ignore_index=True)
            save_expenses(updated)
            st.cache_data.clear()  # pour recharger les données fraîches
            st.success("✅ Dépense enregistrée !")
            expenses_df = load_expenses()
        else:
            st.warning("⚠️ Entrez un montant > 0")

    st.markdown("---")
    st.subheader("📋 Mes dépenses")
    expenses_df = load_expenses()
    st.dataframe(expenses_df, use_container_width=True)
    total_depenses = float(expenses_df["amount"].sum()) if not expenses_df.empty else 0.0
    st.metric("💵 Total des dépenses", f"{total_depenses:,.2f} €".replace(",", " "))

    st.subheader("📈 Dépenses par mois")
    if not expenses_df.empty:
        tmp = expenses_df.copy()
        tmp["date"] = pd.to_datetime(tmp["date"], errors="coerce")
        monthly = (tmp.set_index("date")
                      .groupby(pd.Grouper(freq="M"))["amount"]
                      .sum()
                      .reset_index())
        monthly.rename(columns={"date": "Mois", "amount": "Montant (€)"}, inplace=True)
        st.bar_chart(monthly, x="Mois", y="Montant (€)", use_container_width=True)
    else:
        st.info("Aucune donnée pour le moment.")
