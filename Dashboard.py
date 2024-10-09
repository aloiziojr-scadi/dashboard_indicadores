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

# if filtro_safras:
#     safra_selecionada = filtro_safras.replace("/", "")

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

dado_atividades = atividades["atividades"]

lista_atividades = []
for dado in dado_atividades:
    atividade = {
        "cod_atividade": dado["codAtividade"],
        "atividade": dado["atividade"],
        "area_total": dado["resumoPorArea"]["areaTotal"],
        "unidade_area": dado["resumoPorArea"]["unidadeArea"],
        "desc_unidade_area": dado["resumoPorArea"]["descUnidadeArea"],
        "despesa_area": dado["resumoPorArea"]["despesa"],
        "produtividade": dado["resumoPorUnidade"]["produtividade"],
        "unidade": dado["resumoPorUnidade"]["unidade"],
        "desc_unidade": dado["resumoPorUnidade"]["descUnidade"],
        "despesa_unidade": dado["resumoPorUnidade"]["despesa"]
    }
    lista_atividades.append(atividade)

df_atividades = pd.DataFrame(lista_atividades)


with st.sidebar.expander('Atividade'):
    filtro_atividade = st.selectbox('Selecione', options = df_atividades["atividade"], placeholder = 'Opções')

df_atividades = df_atividades[df_atividades['atividade'] == filtro_atividade]


with st.spinner("Carregando dados... "):
    ### Exibindo o título
    st.title("Indicadores")

    ### Exibindo Subtítulo
    colunasubtitulo1, colunasubtitulo2 = st.columns(2)
    with colunasubtitulo1:
        st.subheader(filtro_atividade)
    with colunasubtitulo2:
        st.subheader(f"Safra: {filtro_safras}")

    codigo_atividade = df_atividades.loc[0, 'cod_atividade']

    #{  "safra": "2223",  "codAtividade": "01",  "nroMaximoSecoes": 7}
    param_indicadores = {
        "safra": safra_selecionada,  
        "codAtividade": codigo_atividade,  
        "nroMaximoSecoes": 7
    }

    header_indicadores = {
        "x-access-token": token,
        "params": j.dumps(param_indicadores)
    }

    url_indicadores = obter_url_indicadores(url_servidor)
    indicadores = obter_registros(url_indicadores, header_indicadores)

    contas_principais = indicadores['contas']
    lista_contas_principais = []
    lista_itens = []
    for dado in contas_principais:
        conta = {
            "codigo_conta": dado['codigo'],
            "descricao_conta": dado['descricao'],
            "moeda": dado['moeda'],
            "percentual_grupo": dado['percentualGrupo'],
            "valor": dado['valor']
        }
        lista_contas_principais.append(conta)

        for dado_sub in dado['itens']['contas']:
            item = {
                "codigo_conta": dado['codigo'],
                "descricao_conta": dado['descricao'],
                "codigo_item": dado_sub['codigo'],
                "descricao_item": dado_sub['descricao'],
                "moeda": dado_sub['moeda'],
                "percentual_grupo": dado_sub['percentualGrupo'],
                "valor": dado_sub['valor'],
                "tipo_conta": "CONTA"
            }
            lista_itens.append(item)
        for dado_sub in dado['itens']['outros']["contas"]:
            item = {
                "codigo_conta": dado['codigo'],
                "descricao_conta": dado['descricao'],
                "codigo_item": dado_sub['codigo'],
                "descricao_item": dado_sub['descricao'],
                "moeda": dado_sub['moeda'],
                "percentual_grupo": dado_sub['percentualGrupo'],
                "valor": dado_sub['valor'],
                "tipo_conta": "OUTROS"
            }
            lista_itens.append(item)

    conta_principal_outros = indicadores['outros']
    conta_outros = {
        "codigo_conta": "00",
        "descricao_conta": conta_principal_outros['descricao'],
        "moeda": conta_principal_outros['moeda'],
        "percentual_grupo": conta_principal_outros['percentualGrupo'],
        "valor": conta_principal_outros['valor']
    }
    lista_contas_principais.append(conta_outros)

    for dado_outros in conta_principal_outros['contas']:
        for dado_sub in dado_outros['itens']['contas']:
            item = {
                "codigo_conta": dado_outros['codigo'],
                "descricao_conta": dado_outros['descricao'],
                "codigo_item": dado_sub['codigo'],
                "descricao_item": dado_sub['descricao'],
                "moeda": dado_sub['moeda'],
                "percentual_grupo": dado_sub['percentualGrupo'],
                "valor": dado_sub['valor'],
                "tipo_conta": "CONTA"
            }
            lista_itens.append(item)
        for dado_sub in dado_outros['itens']['outros']["contas"]:
            item = {
                "codigo_conta": dado_outros['codigo'],
                "descricao_conta": dado_outros['descricao'],
                "codigo_item": dado_sub['codigo'],
                "descricao_item": dado_sub['descricao'],
                "moeda": dado_sub['moeda'],
                "percentual_grupo": dado_sub['percentualGrupo'],
                "valor": dado_sub['valor'],
                "tipo_conta": "OUTROS"
            }
            lista_itens.append(item)


    # st.write(lista_contas_principais)
    # st.write(indicadores)


