# ADD THIS FUNCTION
def close_contract(otp_url, contract_id):
    ws = websocket.create_connection(otp_url, timeout=15)
    ws.send(json.dumps({"sell": contract_id, "price": 0}))
    resp = json.loads(ws.recv())
    ws.close()
    return resp

# IN OPEN TAB, after dataframe, ADD:
if st.button("🔴 CLOSE ALL OPEN NOW"):
    for c in contracts:
        otp = get_otp(ACCOUNT_ID)
        r = close_contract(otp, c["contract_id"])
        st.write(f"Closed {c['contract_id']}: {r}")
    st.success("All closed! Check Profit Table again")
