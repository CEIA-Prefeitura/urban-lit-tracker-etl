import time
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from tqdm import tqdm
from PyLitSurvey.config import logger
from requests.exceptions import HTTPError
from pyalex import Works

# Número de documentos por página
ITER_PER_STEP = 20
QUERY = '"urban change detection" OR "Urban Sprawl"'
MONGO_URI = 'mongodb://localhost:27017/'
DEBUG=True
FILTER_LANG='en|pt'
CORES=28

# Realiza a busca com os parâmetros configurados
w = Works().search(QUERY).filter(language=FILTER_LANG, from_publication_date=f'2017-01-01', to_publication_date=f'2024-12-31')

# Obtém o total de documentos e calcula o número total de páginas
total_iterations = w.count()
total_pages = (total_iterations + ITER_PER_STEP - 1) // ITER_PER_STEP

logger.info(f'Total de documentos: {total_iterations}')
logger.info(f'Total de páginas: {total_pages}')

# Página inicial
START_PAGE = 0

# Configura a barra de progresso
with tqdm(total=total_iterations) as pbar:
    with MongoClient(MONGO_URI) as client:
        db = client[f'gyn-sefin']
        colecao = db['bibliometria']

        # Define o iterador para a paginação começando da página START_PAGE
        current_page = START_PAGE
        cursor = "*"
        processed_docs = 0

        while processed_docs < total_iterations:
            try:
                paginator = w.paginate(per_page=ITER_PER_STEP, cursor=cursor)
                for docs in paginator:
                    new_docs = []
                    for doc in docs:
                        _id = doc.pop('id')
                        doc['_id'] = _id
                        new_docs.append(doc)
                    try:
                        colecao.insert_many(new_docs)
                    except Exception as e:
                        for doc in new_docs:
                            try:
                                colecao.insert_one(doc)
                            except DuplicateKeyError:
                                continue
                            except Exception as e:
                                logger.exception(e)
                                continue

                    pbar.update(len(new_docs))
                    processed_docs += len(new_docs)
                    cursor = paginator.cursor  # Atualiza o cursor para a próxima iteração
                    current_page += 1

            except HTTPError as e:
                if e.response.status_code == 403:
                    logger.warning(f"Erro 403 na página {current_page}. Aguardando antes de tentar novamente.")
                    time.sleep(60)  # Espera 60 segundos antes de tentar novamente
                else:
                    logger.exception(e)
                    break
            except Exception as e:
                logger.exception(e)
                break
