import matplotlib.pyplot as plt
import pandas as pd
from pymongo import MongoClient
from collections import Counter

# Conectar ao MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['gyn-sefin']
colecao = db['bibliometria']

# Coletar os anos de publicação
anos = [trabalho.get('publication_year') for trabalho in colecao.find() if trabalho.get('publication_year')]

# Contar as ocorrências de publicações por ano
contagem_por_ano = Counter(anos)

# Criar um DataFrame com a contagem
df = pd.DataFrame(contagem_por_ano.items(), columns=['Ano', 'Quantidade'])
df = df.sort_values(by='Ano', ascending=True)  # Ordenar por ano

# Função para salvar o DataFrame em CSV (opcional)
def salvar_para_csv(df, nome_arquivo):
    caminho = f"./{nome_arquivo}.csv"
    df.to_csv(caminho, index=False)
    print(f"Arquivo salvo em: {caminho}")

# Gerar gráfico de barras
plt.figure(figsize=(10, 6))  # Definir o tamanho da figura
plt.bar(df['Ano'], df['Quantidade'], color='skyblue')
plt.xlabel('Ano de Publicação')
plt.ylabel('Número de Publicações')
plt.title('Distribuição de Publicações por Ano')

# Adicionar rótulos nas barras
for index, value in enumerate(df['Quantidade']):
    plt.text(df['Ano'].iloc[index], value, str(value), ha='center', va='bottom')

# Ajustar layout
plt.tight_layout()

# Salvar o gráfico como uma imagem
plt.savefig('./distribuicao_publicacoes_por_ano_nova.png')

# Exibir o gráfico
plt.show()
