import requests
import pandas as pd
from google.cloud import storage
import os
from datetime import datetime

# Função destinado ao envio de arquivos para o Google Cloud Storage
def upload_df_to_gcs(df, bucket_name='enjoei-bucket', folder_name='user_carts'):
    """
    Salva o DataFrame como CSV e faz upload para o Google Cloud Storage.
    
    Args:
        df: DataFrame a ser salvo
        bucket_name: Nome do bucket no GCS
        folder_name: Nome da pasta dentro do bucket
    """
    # Configurando credenciais
    credentials_path = os.path.join(os.path.dirname(__file__), 'credenciais.json')
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    
    try:
        # Criando nome do arquivo com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'user_categories_{timestamp}.csv'
        
        # Salvando DataFrame em CSV temporariamente
        temp_path = f'/tmp/{filename}'
        df.to_csv(temp_path, index=False)
        
        # Inicializando cliente do Cloud Storage
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        # Definindo caminho do blob
        blob_path = f'{folder_name}/{filename}'
        blob = bucket.blob(blob_path)
        
        # Fazendo upload do arquivo
        blob.upload_from_filename(temp_path)
        
        # Removendo arquivo temporário
        os.remove(temp_path)
        
        print(f'Arquivo {filename} enviado com sucesso para gs://{bucket_name}/{blob_path}')
        return True
        
    except Exception as e:
        print(f'Erro ao enviar arquivo: {str(e)}')
        return False

def get_categories():
    # Fazendo a chamada à API de categorias
    url = 'https://fakestoreapi.com/products/categories'
    response = requests.get(url)
    
    if response.status_code == 200:
        categories = response.json()
        # Como a API só retorna as categorias, vamos buscar todos os produtos para ter o mapeamento
        products_response = requests.get('https://fakestoreapi.com/products')
        if products_response.status_code == 200:
            products = products_response.json()
            # Criando DataFrame com produto e categoria
            categories_df = pd.DataFrame([
                {
                    'product_id': product['id'],
                    'category': product['category']
                }
                for product in products
            ])
            return categories_df
    return None

def get_user_carts():
    # Fazendo a chamada à API
    url = f'https://fakestoreapi.com/carts/'
    response = requests.get(url)
    
    if response.status_code == 200:
        # Convertendo a resposta JSON para um dataframe
        data = response.json()
        df = pd.DataFrame(data)
        
        # Criando uma linha para cada produto
        df_exploded = pd.DataFrame([
            {
                'cart_id': row['id'],
                'user_id': row['userId'],
                'date': row['date'],
                'product_id': product['productId'],
                'quantity': product['quantity']
            }
            for _, row in df.iterrows()
            for product in row['products']
        ])
        
        # Obtendo as categorias
        categories_df = get_categories()
        
        # Fazendo o merge com as categorias
        if categories_df is not None:
            df_final = df_exploded.merge(
                categories_df,
                on='product_id',
                how='left'
            )
            
            # Agrupando por usuário para obter as informações solicitadas
            user_summary = (
                df_final
                .groupby('user_id')
                .agg({
                    'date': 'max',  # Data mais recente
                    'category': lambda x: x.value_counts().index[0]  # Categoria mais frequente
                })
                .reset_index()
                .rename(columns={
                    'date': 'latest_date',
                    'category': 'most_frequent_category'
                })
            )
            
            return user_summary
        
        return df_exploded
    else:
        print(f"Erro na chamada da API: {response.status_code}")
        return None

if __name__ == "__main__":
    df = get_user_carts()
    print(df)
    if df is not None:
        df.to_csv('users_data.csv', index=False)
        # upload_df_to_gcs(df)
