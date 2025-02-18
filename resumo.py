from pymongo import MongoClient
import json

# Conexão com o MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['gyn-sefin']
colecao = db['bibliometria']

# Consulta para buscar os 5.000 documentos mais citados
documentos = colecao.find().sort("cited_by_count", -1).limit(5000)

# Lista para armazenar os resultados
resultados = []

# Processa cada documento
for documento in documentos:
    resultado = {
        "titulo": documento.get("title"),
        "doi": documento.get("doi"),
        "resumo": " ".join([palavra for palavra in documento.get("abstract_inverted_index", {}).keys()]) if documento.get("abstract_inverted_index") else None,
        "citacoes": documento.get("cited_by_count")
    }
    resultados.append(resultado)

# Converte a lista de dicionários em JSON
resultados_json = json.dumps(resultados, indent=4)

# Salva o resultado em um arquivo JSON
with open('top_5000_artigos_mais_citados.json', 'w') as file:
    file.write(resultados_json)

print("JSON gerado e salvo em 'top_5000_artigos_mais_citados.json'")
