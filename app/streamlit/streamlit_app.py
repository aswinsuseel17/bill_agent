import requests
import streamlit as st

st.set_page_config(page_title="Bill Analyzer", page_icon="📄")
st.title("Bill Analyzer UI")

api_base_url = st.text_input("FastAPI Base URL", value="http://localhost:8001")

st.subheader("Upload PDF Bills")
uploaded_files = st.file_uploader(
    "Upload one or more PDF bills",
    type=["pdf"],
    accept_multiple_files=True,
)

if st.button("Analyze Bills", type="primary"):
    if not uploaded_files:
        st.warning("Upload at least one PDF file.")
    else:
        files = [("files", (f.name, f.getvalue(), "application/pdf")) for f in uploaded_files]
        try:
            response = requests.post(f"{api_base_url}/bills/upload", files=files, timeout=60)
            if response.ok:
                st.success("Bills analyzed successfully")
                st.json(response.json())
            else:
                st.error(f"API error: {response.status_code}")
                st.json(response.json())
        except requests.RequestException as exc:
            st.error(f"Could not reach API: {exc}")

st.subheader("Get Bill by ID")
bill_id = st.text_input("Bill ID")
if st.button("Get Bill Data"):
    if not bill_id.strip():
        st.warning("Enter a bill ID.")
    else:
        try:
            response = requests.get(f"{api_base_url}/bills/{bill_id.strip()}", timeout=30)
            if response.ok:
                st.json(response.json())
            else:
                st.error(f"API error: {response.status_code}")
                st.json(response.json())
        except requests.RequestException as exc:
            st.error(f"Could not reach API: {exc}")
