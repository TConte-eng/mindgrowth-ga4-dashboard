import streamlit as st
import pandas as pd
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, Dimension, RunReportRequest
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
REDIRECT_URI = "http://localhost:8501"

st.set_page_config(page_title="Teste GA4 OAuth", page_icon="📊", layout="wide")
st.title("Teste de conexão com GA4 via OAuth")

try:
    client_id = st.secrets["google_oauth"]["client_id"]
    client_secret = st.secrets["google_oauth"]["client_secret"]
except Exception as e:
    st.error("Não encontrei [google_oauth] no secrets.toml.")
    st.exception(e)
    st.stop()

client_config = {
    "web": {
        "client_id": client_id,
        "client_secret": client_secret,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

if "credentials" not in st.session_state:
    st.session_state.credentials = None

flow = Flow.from_client_config(client_config, scopes=SCOPES)
flow.redirect_uri = REDIRECT_URI

query_params = st.query_params

if "code" not in query_params and st.session_state.credentials is None:
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    st.link_button("Fazer login com Google", auth_url)
    st.info("Depois do login, você voltará para esta página.")
    st.stop()

if "code" in query_params and st.session_state.credentials is None:
    try:
        authorization_response = f"{REDIRECT_URI}?code={query_params['code']}"
        if "state" in query_params:
            authorization_response += f"&state={query_params['state']}"
        flow.fetch_token(authorization_response=authorization_response)

        creds = flow.credentials
        st.session_state.credentials = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes,
        }
        st.success("Login realizado com sucesso.")
    except Exception as e:
        st.error("Erro ao concluir OAuth.")
        st.exception(e)
        st.stop()

if st.session_state.credentials is None:
    st.stop()

creds = Credentials(
    token=st.session_state.credentials["token"],
    refresh_token=st.session_state.credentials["refresh_token"],
    token_uri=st.session_state.credentials["token_uri"],
    client_id=st.session_state.credentials["client_id"],
    client_secret=st.session_state.credentials["client_secret"],
    scopes=st.session_state.credentials["scopes"],
)

property_id = st.text_input("ID da propriedade GA4", value="537595613")

if property_id:
    try:
        client = BetaAnalyticsDataClient(credentials=creds)

        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="date")],
            metrics=[Metric(name="sessions")],
            date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
        )

        response = client.run_report(request)

        rows = []
        for row in response.rows:
            rows.append({
                "date": row.dimension_values[0].value,
                "sessions": int(row.metric_values[0].value),
            })

        df = pd.DataFrame(rows)

        st.subheader("Dados retornados")
        st.dataframe(df, use_container_width=True)
        st.line_chart(df.set_index("date")["sessions"])

    except Exception as e:
        st.error("Erro ao chamar a API do GA4.")
        st.exception(e)

if st.button("Sair / limpar sessão"):
    st.session_state.credentials = None
    st.query_params.clear()
    st.rerun()
