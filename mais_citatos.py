import matplotlib.pyplot as plt
import pandas as pd
from pymongo import MongoClient
import numpy as np
import json

# Função para quebrar o título em múltiplas linhas se exceder o limite de caracteres
def wrap_text(text, max_width):
    words = text.split()
    wrapped_text = ''
    current_line = ''
    
    for word in words:
        if len(current_line) + len(word) + 1 <= max_width:
            current_line += word + ' '
        else:
            wrapped_text += current_line.strip() + '\n'
            current_line = word + ' '
    
    wrapped_text += current_line.strip()  # Adiciona a última linha
    return wrapped_text

# Conectar ao MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['gyn-sefin']
colecao = db['bibliometria']

# Coletar os dados e ordenar pela contagem de citações
df = pd.DataFrame(list(colecao.find().sort('cited_by_count', -1).limit(10)))
df = df[['title', 'cited_by_count']].sort_values(by='cited_by_count', ascending=False)

# Gerar cores diferentes para cada barra
colors = plt.cm.Blues(np.linspace(1, 0, len(df)))

# Criar o gráfico de barras
plt.figure(figsize=(14, 8))  # Aumentar o tamanho da figura
bars = plt.barh(range(len(df)), df['cited_by_count'], color=colors)
plt.xlabel('Número de Citações')
plt.ylabel('Artigos')
plt.title('Top 10 Artigos Mais Citados')

# Inverter o eixo Y para manter a ordem correta
plt.gca().invert_yaxis()

# Adicionar números no eixo Y em vez dos títulos
plt.yticks(range(len(df)), range(1, len(df) + 1))

# Adicionar os valores ao lado das barras
for i, bar in enumerate(bars):
    plt.text(bar.get_width(), bar.get_y() + bar.get_height()/2, f'{df["cited_by_count"].iloc[i]:.0f}', va='center')

# Ajustar a largura máxima de caracteres para os títulos (exemplo: 100px ~= 40 caracteres)
max_characters = 40
legend_labels = [f'{i+1} - {wrap_text(df["title"].iloc[i], max_characters)}' for i in range(len(df))]

# Criar legenda numerada com as cores correspondentes e quebrar linhas quando necessário
plt.legend(bars, legend_labels, title="Artigos", loc='best', bbox_to_anchor=(1.15, 1), fontsize=10)

# Ajustar layout para evitar corte de texto
plt.tight_layout()

# Salvar o gráfico com a legenda
plt.savefig('./top_10_artigos_mais_citados_com_legenda_nova.png')

# Exportar o JSON com os dados
dados_json = df.to_dict(orient='records')
with open('./top_10_artigos_mais_citados01.json', 'w', encoding='utf-8') as f:
    json.dump(dados_json, f, ensure_ascii=False, indent=4)

# Exibir o gráfico
plt.show()
