import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html
from pymongo import MongoClient
from collections import Counter
import numpy as np
from scipy.optimize import curve_fit
from scipy.optimize import OptimizeWarning
import warnings

# Ignorar os avisos de ajuste exponencial (caso o ajuste exponencial falhe)
warnings.filterwarnings("ignore", category=OptimizeWarning)

# Conectar ao MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['tvi-tcc']
colecao = db['bibliometria_tvi']

# Função para ajuste exponencial
def func_exp(x, a, b, c):
    return a * np.exp(b * x) + c

# Função para ajuste polinomial de grau 2
def func_poly(x, a, b, c):
    return a * x**2 + b * x + c

# Função para gerar o gráfico de barras com ajuste (exponencial ou polinomial)
def gerar_grafico_series_temporais(df):
    # Ordenar os dados por ano
    df = df.sort_values(by='Ano')

    # Verificar se há dados suficientes para o ajuste
    if len(df) < 2:
        return dcc.Graph(figure={"layout": {"title": "Dados insuficientes para ajuste"}})

    # Ajustar o modelo exponencial
    x_data = df['Ano'].values
    y_data = df['Quantidade'].values

    try:
        # Log-transformação dos dados de quantidade para o ajuste exponencial
        y_data_log = np.log(y_data)

        # Ajuste exponencial
        popt_exp, _ = curve_fit(func_exp, x_data, y_data_log, maxfev=10000)

        # Prever valores ajustados no domínio original (revertendo a transformação log)
        x_fit = np.linspace(min(x_data), max(x_data), 100)
        y_fit_exp = np.exp(func_exp(x_fit, *popt_exp))

        ajuste_feito = 'exponencial'
        y_fit = y_fit_exp

    except (RuntimeError, OptimizeWarning):
        # Caso o ajuste exponencial falhe, aplicar ajuste polinomial
        popt_poly, _ = curve_fit(func_poly, x_data, y_data, maxfev=10000)

        # Prever valores ajustados com o polinômio
        y_fit_poly = func_poly(x_fit, *popt_poly)

        ajuste_feito = 'polinomial'
        y_fit = y_fit_poly

    # Criar o gráfico
    fig = go.Figure()

    # Adicionar o gráfico de barras (número total de publicações por ano)
    fig.add_trace(go.Bar(x=x_data, y=y_data, name='Total de Publicações por Ano'))

    # Adicionar a linha de ajuste
    fig.add_trace(go.Scatter(
        x=x_fit, y=y_fit, mode='lines', name=f'Ajuste {ajuste_feito}',
        line=dict(color='red', dash='dash')))

    # Atualizar o layout
    fig.update_layout(
        title=f'Total de Publicações por Ano com Ajuste {ajuste_feito.capitalize()}',
        xaxis_title='Ano',
        yaxis_title='Quantidade de Publicações',
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        yaxis_type='linear'
    )

    return dcc.Graph(figure=fig)

# Função para calcular a distribuição de trabalhos por ano e gerar o gráfico
def distribuicao_por_ano_ajuste():
    anos = [trabalho.get('publication_year') for trabalho in colecao.find() if trabalho.get('publication_year')]
    contagem_por_ano = Counter(anos)
    df = pd.DataFrame(contagem_por_ano.items(), columns=['Ano', 'Quantidade'])
    return gerar_grafico_series_temporais(df)

# Inicializa o aplicativo Dash
app = Dash(__name__)

# Layout simples com apenas o gráfico
app.layout = html.Div([
    html.H1("Distribuição de Trabalhos por Ano com Ajuste"),
    distribuicao_por_ano_ajuste()
])

if __name__ == '__main__':
    app.run_server(debug=True)
