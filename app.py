import streamlit as st
from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, Dimension, RunReportRequest

st.set_page_config(page_title="Teste GA4", page_icon="📊")

st.title("Teste de conexão com GA4")

# 1. Ler credenciais do secrets
try:
    service_account_info = st.secrets["ga4_service_account"]
except Exception as e:
    st.error("Não encontrei a seção [ga4_service_account] nos secrets.")
    st.exception(e)
    st.stop()

# 2. Criar credenciais
try:
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=["https://www.googleapis.com/auth/analytics.readonly"],
    )
except Exception as e:
    st.error("Erro ao criar as credenciais do GA4. Verifique o private_key.")
    st.exception(e)
    st.stop()

st.success("Credenciais carregadas com sucesso.")

# 3. Pedir o ID da propriedade GA4 (G- não serve, é o número, tipo 123456789)
property_id = st.text_input(
    "ID da propriedade GA4 (ex: 123456789)",
    placeholder="Cole aqui o ID numérico da propriedade",
)

if property_id:
    try:
        client = BetaAnalyticsDataClient(credentials=credentials)

        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="date")],
            metrics=[Metric(name="sessions")],
            date_ranges=[DateRange(start_date="7daysAgo", end_date="yesterday")],
        )

        response = client.run_report(request)

        # Transformar resposta em tabela simples
        rows = []
        for row in response.rows:
            rows.append(
                {
                    "date": row.dimension_values[0].value,
                    "sessions": int(row.metric_values[0].value or 0),
                }
            )

        if rows:
            import pandas as pd

            df = pd.DataFrame(rows)
            st.subheader("Sessões por dia (últimos 7 dias)")
            st.dataframe(df)
            st.line_chart(df.set_index("date")["sessions"])
        else:
            st.warning("A API respondeu, mas não retornou linhas de dados.")
    except Exception as e:
        st.error("Deu erro ao chamar a API do GA4. Veja os detalhes abaixo:")
        st.exception(e)
else:
    st.info("Cole o ID da propriedade GA4 acima para testar a conexão.")
