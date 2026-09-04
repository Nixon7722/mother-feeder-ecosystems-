import streamlit as st, requests, json

st.set_page_config(page_title="MOTHER V3.3 PAT", layout="wide")
st.title("🧠 MOTHER V3.3 - PAT READY")

st.write("This version supports NEW pat_ tokens")

if st.button("🔴 CONNECT TO REAL DERIV NOW", type="primary"):
    try:
        token = st.secrets["DERIV_TOKEN"]
        # NEW API - PAT tokens use api.derivws.com
        headers = {
            "Authorization": f"Bearer {token}",
            "Deriv-App-ID": "1089"
        }
        # Step 1: Get accounts
        r = requests.get("https://api.derivws.com/trading/v1/options/accounts", headers=headers, timeout=20)

        if r.status_code == 200:
            data = r.json()
            st.success("✅ REAL DERIV CONNECTED WITH NEW PAT TOKEN!")
            st.json(data)
            st.balloons()
            # Show accounts
            if "data" in data:
                st.write(f"Found {len(data['data'])} accounts:")
                for acc in data['data']:
                    st.write(f"- {acc.get('account_id')} | {acc.get('currency')} | {acc.get('is_demo')}")
        else:
            st.error(f"API Error {r.status_code}: {r.text}")
            st.info("Make sure token has Read + Trade scope and you copied it correctly.")

    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.write("Check Secrets -> DERIV_TOKEN exists")

st.divider()
st.write(f"Token exists: {'DERIV_TOKEN' in st.secrets}")
