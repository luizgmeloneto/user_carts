# Análise de Carrinhos de Usuários e Categorias

Este projeto realiza a análise de dados de carrinhos de compras de usuários, integrando com uma API externa e armazenando os resultados no Google Cloud Storage. O sistema processa informações sobre produtos, categorias e comportamento de compra dos usuários.

## 🎯 Objetivo

O principal objetivo é identificar as categorias de produtos mais frequentes para cada usuário, junto com suas datas mais recentes de atividade, criando um perfil de preferências de compra.

## 🛠️ Funcionalidades Principais

### 1. Upload para Google Cloud Storage
```python A função upload_df_to_gcs gerencia o upload de DataFrames para o Google Cloud Storage:
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
```


### 2. Obtenção de Categorias
A função `get_categories` recupera informações sobre produtos e suas categorias:
```python
def get_categories():
    """
    Busca produtos da API e cria um DataFrame com o mapeamento de produtos e categorias.
    
    Returns:
        DataFrame com colunas: product_id, category
    """
    products_response = requests.get('https://fakestoreapi.com/products')
    if products_response.status_code == 200:
        products = products_response.json()

        # Criando DataFrame com produto e sua respectiva categoria
        categories_df = pd.DataFrame([
            {
                'product_id': product['id'],
                'category': product['category']
            }
            for product in products
        ])
        return categories_df
```


### 3. Análise de Carrinhos de Usuários
A função `get_user_carts` realiza a análise principal:
- Busca dados de carrinhos da API
- Processa produtos individuais
- Calcula categorias mais frequentes
- Identifica datas mais recentes de atividade

```python
def get_user_carts():
    # Fazendo a chamada à API de carrinhos dos usuários
    url = f'https://fakestoreapi.com/carts/'
    response = requests.get(url)
    
    if response.status_code == 200:
        # Convertendo a resposta JSON para um dataframe
        data = response.json()
        df = pd.DataFrame(data)
```


## 📊 Processamento de Dados

O pipeline de processamento inclui:

1. **Explosão de Dados de Carrinho**

```python
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
```


2. **Cálculo de Categorias Mais Frequentes**

```python
category_counts = (
    df_final
    .groupby(['user_id', 'category'])['quantity']
    .sum()
    .reset_index()
)
```


3. **Identificação de Datas Mais Recentes**
```python
latest_dates = (
    df_final
    .groupby('user_id')['date']
    .max()
    .reset_index()
)
```

## 🚀 Como Usar

1. Configure as credenciais do Google Cloud:
   - Coloque o arquivo `credenciais.json` no mesmo diretório do script

2. Execute o script:
```bash
python api.py
```


3. Os resultados serão:
   - Salvos localmente como 'users_data.csv'
   - Enviados para o Google Cloud Storage

## 📋 Requisitos

- Python 3.x
- Bibliotecas necessárias:
    - pandas
    - requests
    - google-cloud-storage
```bash
pip install pandas requests google-cloud-storage
```

## 🔐 Configuração de Credenciais

O projeto requer um arquivo de credenciais do Google Cloud Platform:
- Nome do arquivo: `credenciais.json`
- Localização: mesmo diretório do script
- Permissões necessárias: acesso ao Cloud Storage

## 📝 Notas

- A API utilizada é a FakeStoreAPI para demonstração
- Os dados são processados em memória, considere otimizações para grandes volumes
- O timestamp no nome do arquivo garante unicidade no armazenamento
