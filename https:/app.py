import streamlit as st, requests

st.set_page_config(page_title="MOTHER V3.4", layout="wide")
st.title("🧠 MOTHER V3.4 - PAT READY")

app_id = st.secrets.get("DERIV_APP_ID", "1089")
token = st.secrets.get("DERIV_TOKEN", "")

st.write(f"Using App ID: {app_id}")

if st.button("🔴 CONNECT TO REAL DERIV NOW", type="primary"):
    headers = {
        "Authorization": f"Bearer {token}",
        "Deriv-App-ID": str(app_id)
    }
    try:
        r = requests.get("https://api.derivws.com/trading/v1/options/accounts", headers=headers, timeout=20)
        if r.status_code == 200:
            st.success("✅ REAL DERIV CONNECTED!")
            data = r.json()
            st.json(data)
            st.balloons()
        else:
            st.error(f"API Error {r.status_code}: {r.text}")
            if "Invalid application" in r.text:
                st.warning("App ID wrong. Go to developers.deriv.com -> My Apps -> copy App ID.")
    except Exception as e:
        st.error(str(e))
