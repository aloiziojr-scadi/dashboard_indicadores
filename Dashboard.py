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
    ## Exibindo o título
    st.title("Indicadores")

    ## Exibindo Subtítulo
    coluna_subtitulo_1, coluna_subtitulo_2 = st.columns([3,1])
    with coluna_subtitulo_1:
        st.subheader(f"Safra: {filtro_safras}")
        
    with coluna_subtitulo_2:
        st.subheader(filtro_atividade)
        
    codigo_atividade = df_atividades.loc[0, 'cod_atividade']
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

    total_geral = locale.currency(indicadores['total'], grouping = True)
    
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
                "rotulo": dado['descricao'],
                "codigo_conta": dado['codigo'],
                "descricao_conta": dado['descricao'],
                "codigo_item": dado_sub['codigo'],
                "descricao_item": dado_sub['descricao'],
                "moeda": dado_sub['moeda'],
                "percentual_geral": dado_sub['percentualGeral'],
                "percentual_grupo": dado_sub['percentualGrupo'],
                "valor": dado_sub['valor'],
                "tipo_conta": "CONTA"
            }
            lista_itens.append(item)
        for dado_sub in dado['itens']['outros']["contas"]:
            item = {
                "rotulo": dado['descricao'],
                "codigo_conta": dado['codigo'],
                "descricao_conta": dado['descricao'],
                "codigo_item": dado_sub['codigo'],
                "descricao_item": dado_sub['descricao'],
                "moeda": dado_sub['moeda'],
                "percentual_geral": dado_sub['percentualGeral'],
                "percentual_grupo": dado_sub['percentualGrupo'],
                "valor": dado_sub['valor'],
                "tipo_conta": "OUTROS"
            }
            lista_itens.append(item)

    conta_principal_outros = indicadores['outros']
    conta_outros = {
        "codigo_conta": "00",
        "descricao_conta": conta_principal_outros['descricao'].upper(),
        "moeda": conta_principal_outros['moeda'],
        "percentual_grupo": conta_principal_outros['percentualGrupo'],
        "valor": conta_principal_outros['valor']
    }
    lista_contas_principais.append(conta_outros)

    for dado_outros in conta_principal_outros['contas']:
        for dado_sub in dado_outros['itens']['contas']:
            item = {
                "rotulo": "OUTROS",
                "codigo_conta": dado_outros['codigo'],
                "descricao_conta": dado_outros['descricao'],
                "codigo_item": dado_sub['codigo'],
                "descricao_item": dado_sub['descricao'],
                "moeda": dado_sub['moeda'],
                "percentual_geral": dado_sub['percentualGeral'],
                "percentual_grupo": dado_sub['percentualGrupo'],
                "valor": dado_sub['valor'],
                "tipo_conta": "OUTROS CONTA"
            }
            lista_itens.append(item)
        for dado_sub in dado_outros['itens']['outros']["contas"]:
            item = {
                "rotulo": "OUTROS",
                "codigo_conta": dado_outros['codigo'],
                "descricao_conta": dado_outros['descricao'],
                "codigo_item": dado_sub['codigo'],
                "descricao_item": dado_sub['descricao'],
                "moeda": dado_sub['moeda'],
                "percentual_geral": dado_sub['percentualGeral'],
                "percentual_grupo": dado_sub['percentualGrupo'],
                "valor": dado_sub['valor'],
                "tipo_conta": "OUTROS OUTROS"
            }
            lista_itens.append(item)

    df_contas_principais = pd.DataFrame(lista_contas_principais)

    df_contas_principais['valor_formatado'] = df_contas_principais.apply(lambda x: f"{x['moeda']} {locale.currency(x['valor'], symbol = False, grouping=True)}", axis = 1)
    df_contas_principais['texto_completo'] = df_contas_principais.apply(lambda x: f"{x['descricao_conta'].upper()}<br>{x['percentual_grupo']:.2f}%<br>{x['valor_formatado']}", axis=1)
    fig_contas_principais = px.pie(df_contas_principais, values = 'valor', names = 'texto_completo', hole = .5)
    fig_contas_principais.update_traces(textinfo='none', customdata = df_contas_principais["texto_completo"], hovertemplate = "%{customdata}")
    fig_contas_principais.update_layout(title='Despesas Gerais', showlegend=True, legend=dict(x=1, y=0.5, traceorder='normal', font=dict(size=12)), margin=dict(l=0, r=150, t=40, b=0))

    # Adicionar o total no meio
    fig_contas_principais.add_annotation(text=total_geral, showarrow=False, font=dict(size=20), x=0.5, y=0.5, xref="paper", yref="paper")
    
    with st.container():
        coluna_principal_1, coluna_principal_2 = st.columns([3,1])
        with coluna_principal_1:
            st.plotly_chart(fig_contas_principais)
        with coluna_principal_2:
            texto_area = f"Por {df_atividades.loc[0, 'desc_unidade_area']} | Área {locale.currency(df_atividades.loc[0, 'area_total'], symbol = False, grouping = True)} {df_atividades.loc[0, 'unidade_area']}"
            valor_area = locale.currency(df_atividades.loc[0, 'despesa_area'], grouping = True)
            st.text(texto_area)
            st.metric('Despesas', value = valor_area)
            st.divider()
            texto_unidade = f"Por {df_atividades.loc[0, 'desc_unidade']} | Prod. {locale.currency(df_atividades.loc[0, 'produtividade'], symbol = False, grouping = True)} {df_atividades.loc[0, 'unidade']}"
            valor_unidade = locale.currency(df_atividades.loc[0, 'despesa_unidade'], grouping = True)
            st.text(texto_unidade)
            st.metric('Despesas', value = valor_unidade)

    with st.container():
        with st.expander('Dados'):
            df_itens = pd.DataFrame(lista_itens)
            filtro_itens = st.selectbox('Filtro', options = ['TODOS'] + list(df_itens['rotulo'].unique()), placeholder = 'Opções')
            if filtro_itens != 'TODOS':
                df_itens = df_itens[df_itens['rotulo'] == filtro_itens]
                atividade_selecionada = df_contas_principais[df_contas_principais['descricao_conta'] == filtro_itens].copy().reset_index()
                st.text(atividade_selecionada.loc[0, 'valor_formatado'])
                st.text(locale.currency(atividade_selecionada.loc[0, 'percentual_grupo'], grouping = True, symbol = False) + "%")

            df_itens['texto_completo'] = df_itens.apply(
                lambda x: f"{x['rotulo']} - {x['descricao_conta']} - {x['descricao_item']}" 
                if x['rotulo'] == 'OUTROS' 
                else f"{x['descricao_conta']} - {x['descricao_item']}", axis=1
            )
            df_itens['valor_formatado'] = df_itens.apply(lambda x: f"{x['moeda']} {locale.currency(x['valor'], symbol = False, grouping=True)}", axis = 1)
            df_itens['percentual_grupo_formatado'] = df_itens.apply(lambda x: f"{locale.currency(x['percentual_grupo'], symbol = False, grouping=True)}%", axis = 1)
            df_itens['percentual_geral_formatado'] = df_itens.apply(lambda x: f"{locale.currency(x['percentual_geral'], symbol = False, grouping=True)}%", axis = 1)
            
            tabela_itens = df_itens[['texto_completo', 'percentual_grupo_formatado', 'percentual_geral_formatado', 'valor_formatado']].copy()
            tabela_itens.rename(
                columns = {
                    "texto_completo": "Descrição", 
                    "valor_formatado": "Valor", 
                    "percentual_grupo_formatado": "Percentual do Grupo", 
                    "percentual_geral_formatado": "Percentual Geral"
                }, inplace = True
            )
            
            st.dataframe(tabela_itens, hide_index = True, use_container_width = True)
    