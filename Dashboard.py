import streamlit as st
import pandas as pd
import requests
import json as j
import plotly.express as px
import locale

st.set_page_config(layout= 'wide')

with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html= True)

# Define o locale para formato monetário brasileiro
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

## Funções
# Função para obter os registros
def obter_registros(url, header):
    try:
        resposta = requests.get(url, headers = header)
        resposta.raise_for_status()
        return resposta.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao acessar a API: {e}")
    except ValueError as e:
        st.error(f"Erro ao carregar os dados: {e}")

# Função para obter o token
def obter_token():
    return st.query_params["token"]

# Função para obter a URL do servidor
def obter_url_servidor():
    return st.query_params["url"]

# Função para obter a URL das safras
def obter_url_safras(url_base):
    return f"http://{url_base}/api/safras"

# Função para obter a URL das safras
def obter_url_atividades(url_base):
    return f"http://{url_base}/api/itesafra"

# Função para obter a URL dos indicadores
def obter_url_indicadores(url_base):
    return f"http://{url_base}/api/indicadores/graficos"

# Obtém o token
token = obter_token()

# Obtém a url do servidor
url_servidor = obter_url_servidor()

### Criação do Sidebar e dos Filtros
st.sidebar.title('Filtros')

## Criação da lista do Filtro de Safras
url_safras = obter_url_safras(url_servidor)
param_token = {
    "x-access-token": token
}
safras = obter_registros(url_safras, param_token)

df_safras = pd.DataFrame(safras, columns = ["safra"])

# Adicionando uma nova coluna formatada
df_safras['safra_formatada'] = df_safras['safra'].astype(str).str[:2] + '/' + df_safras['safra'].astype(str).str[2:]

with st.sidebar.expander('Safras'):
    filtro_safras = st.selectbox('Selecione', options = df_safras["safra_formatada"], placeholder = 'Opções')
    safra_selecionada = filtro_safras.replace("/", "")

if filtro_safras:
    safra_selecionada = filtro_safras.replace("/", "")

## Criação da lista do Filtro de Atividades
url_atividades = obter_url_atividades(url_servidor)
param_safra = {
  "safra": safra_selecionada
}

header_atividades = {
    "x-access-token": token,
    "params": j.dumps(param_safra)
}

atividades = obter_registros(url_atividades, header_atividades)

df_atividades = pd.DataFrame(atividades["atividades"], columns = ["codAtividade", "atividade"])

with st.sidebar.expander('Atividade'):
    filtro_atividade = st.selectbox('Selecione', options = df_atividades["atividade"], placeholder = 'Opções')
st.dataframe(df_atividades)
