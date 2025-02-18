import os

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html
import dash_mantine_components as dmc
from dash.dependencies import Input, Output  # Importações necessárias
from pymongo import MongoClient
from collections import Counter

# Conectar ao MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['tvi-tcc']
colecao = db['bibliometria_tvi']

# Função para coletar os dados do MongoDB
def obter_dados_trabalhos():
    trabalhos = list(colecao.find())
    return pd.DataFrame(trabalhos)

# Função para converter os dados da MongoDB para tabelas e gráficos
def gerar_tabela_grafico(df, coluna_x, coluna_y, titulo, xlabel, ylabel):
    tabela = dmc.Table(
        [html.Thead(html.Tr([html.Th(col) for col in df.columns]))] +
        [html.Tr([html.Td(df.iloc[i][col]) for col in df.columns]) for i in range(min(len(df), 10))],  # Exibir as 10 primeiras linhas
        striped=True, highlightOnHover=True, withBorder=True, withColumnBorders=True
    )
    grafico = dcc.Graph(figure=gerar_grafico(df[coluna_x], df[coluna_y], titulo, xlabel, ylabel))
    return tabela, grafico


# Função para gerar um gráfico de barras dinâmico usando Plotly
def gerar_grafico(x, y, titulo, xlabel, ylabel):
    fig = go.Figure(data=[go.Bar(x=x, y=y)])
    fig.update_layout(
        title=titulo,
        xaxis_title=xlabel,
        yaxis_title=ylabel,
        xaxis_tickangle=-45,
        height=400,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

# Função para salvar o DataFrame como CSV
def salvar_para_csv(df, nome_arquivo):
    if not os.path.exists("exported_csv"):
        os.makedirs("exported_csv")
    caminho_arquivo = f"exported_csv/{nome_arquivo}.csv"
    df.to_csv(caminho_arquivo, index=False)
    return caminho_arquivo

# Modificação das funções para ordenar os DataFrames antes de exportar para CSV
def trabalhos_mais_relevantes():
    df = pd.DataFrame(list(colecao.find().sort('relevance_score', -1).limit(10)))
    df = df.sort_values(by='relevance_score', ascending=False)  # Ordenar pela relevância
    salvar_para_csv(df, "trabalhos_mais_relevantes")
    return gerar_tabela_grafico(df, 'title', 'relevance_score', 'Trabalhos Mais Relevantes', 'Título', 'Relevância')

def trabalhos_mais_citados():
    df = pd.DataFrame(list(colecao.find().sort('cited_by_count', -1).limit(10)))
    df = df.sort_values(by='cited_by_count', ascending=False)  # Ordenar pela contagem de citações
    salvar_para_csv(df, "trabalhos_mais_citados")
    return gerar_tabela_grafico(df, 'title', 'cited_by_count', 'Trabalhos Mais Citados', 'Título', 'Citações')

def distribuicao_por_ano():
    anos = [trabalho.get('publication_year') for trabalho in colecao.find() if trabalho.get('publication_year')]
    contagem_por_ano = Counter(anos)
    df = pd.DataFrame(contagem_por_ano.items(), columns=['Ano', 'Quantidade'])
    df = df.sort_values(by='Ano', ascending=True)  # Ordenar por ano
    salvar_para_csv(df, "distribuicao_por_ano")
    return gerar_tabela_grafico(df, 'Ano', 'Quantidade', 'Distribuição de Trabalhos por Ano', 'Ano', 'Quantidade')

def autores_mais_frequentes():
    autores = []
    for trabalho in colecao.find():
        for autoria in trabalho['authorships']:
            autores.append(autoria['author']['display_name'])
    contagem_autores = Counter(autores)
    df = pd.DataFrame(contagem_autores.most_common(10), columns=['Autor', 'Quantidade'])
    df = df.sort_values(by='Quantidade', ascending=False)  # Ordenar pela frequência de autores
    salvar_para_csv(df, "autores_mais_frequentes")
    return gerar_tabela_grafico(df, 'Autor', 'Quantidade', 'Autores Mais Frequentes', 'Autor', 'Quantidade')

def instituicoes_mais_frequentes():
    instituicoes = []
    for trabalho in colecao.find():
        for autoria in trabalho['authorships']:
            for instituicao in autoria['institutions']:
                instituicoes.append(instituicao['display_name'])
    contagem_instituicoes = Counter(instituicoes)
    df = pd.DataFrame(contagem_instituicoes.most_common(10), columns=['Instituição', 'Quantidade'])
    df = df.sort_values(by='Quantidade', ascending=False)  # Ordenar pela frequência de instituições
    salvar_para_csv(df, "instituicoes_mais_frequentes")
    return gerar_tabela_grafico(df, 'Instituição', 'Quantidade', 'Instituições Mais Frequentes', 'Instituição', 'Quantidade')

def palavras_chave_mais_frequentes():
    palavras_chave = []
    for trabalho in colecao.find():
        if 'keywords' in trabalho:
            for keyword in trabalho['keywords']:
                palavras_chave.append(keyword['display_name'])
    contagem_palavras_chave = Counter(palavras_chave)
    df = pd.DataFrame(contagem_palavras_chave.most_common(10), columns=['Palavra-chave', 'Quantidade'])
    df = df.sort_values(by='Quantidade', ascending=False)  # Ordenar pela frequência das palavras-chave
    salvar_para_csv(df, "palavras_chave_mais_frequentes")
    return gerar_tabela_grafico(df, 'Palavra-chave', 'Quantidade', 'Palavras-chave Mais Frequentes', 'Palavra-chave', 'Quantidade')

# Inicializa o aplicativo Dash
app = Dash(__name__)

# Layout moderno com Material Design
app.layout = dmc.MantineProvider(
    theme={"colorScheme": "light"},
    children=[
        dmc.Container([
            dmc.Title("Dashboard de Bibliometria", order=1, mt=20),  # Removido align
            dmc.SegmentedControl(
                data=[
                    {"label": "Trabalhos Mais Relevantes", "value": "tab1"},
                    {"label": "Trabalhos Mais Citados", "value": "tab2"},
                    {"label": "Distribuição por Ano", "value": "tab3"},
                    {"label": "Autores Mais Frequentes", "value": "tab4"},
                    {"label": "Instituições Mais Frequentes", "value": "tab5"},
                    {"label": "Palavras-chave Mais Frequentes", "value": "tab6"}
                ],
                value="tab1",
                id="tabs",
                fullWidth=True,
                size="lg",
                radius="md",
                mt=20,
            ),
            dmc.Space(h=20),
            dmc.Container(id="tabs-content", fluid=True),
        ], fluid=True)
    ]
)

# Callbacks para trocar de abas
@app.callback(
    Output("tabs-content", "children"),
    Input("tabs", "value")
)
def render_content(tab):
    if tab == "tab1":
        return dmc.Container([dmc.Title("Trabalhos Mais Relevantes", order=2), *trabalhos_mais_relevantes()])
    elif tab == "tab2":
        return dmc.Container([dmc.Title("Trabalhos Mais Citados", order=2), *trabalhos_mais_citados()])
    elif tab == "tab3":
        return dmc.Container([dmc.Title("Distribuição de Trabalhos por Ano", order=2), *distribuicao_por_ano()])
    elif tab == "tab4":
        return dmc.Container([dmc.Title("Autores Mais Frequentes", order=2), *autores_mais_frequentes()])
    elif tab == "tab5":
        return dmc.Container([dmc.Title("Instituições Mais Frequentes", order=2), *instituicoes_mais_frequentes()])
    elif tab == "tab6":
        return dmc.Container([dmc.Title("Palavras-chave Mais Frequentes", order=2), *palavras_chave_mais_frequentes()])

if __name__ == '__main__':
    app.run_server(debug=True)
