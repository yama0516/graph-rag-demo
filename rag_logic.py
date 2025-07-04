import os
from langchain_community.document_loaders import TextLoader
from langchain_anthropic import ChatAnthropic
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI
from langchain.chains import GraphCypherQAChain 
from openai import OpenAI
import json
from neo4j import GraphDatabase, basic_auth
import pandas as pd
from openai import AzureOpenAI
from tenacity import retry, wait_random_exponential, stop_after_attempt  
from azure.identity import DefaultAzureCredential
from azure.identity import get_bearer_token_provider
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters,
    SearchIndex
)
from openai import OpenAI
from azure.search.documents.models import (
    QueryAnswerType,
    QueryCaptionType,
    QueryCaptionResult,
    QueryAnswerResult,
    SemanticErrorMode,
    SemanticErrorReason,
    SemanticSearchResultsType,
    QueryType,
    VectorizedQuery,
    VectorQuery,
    VectorFilterMode,    
)

from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
from azure.search.documents import SearchClient, SearchIndexingBufferedSender  

load_dotenv()

index_name = "graphrag"
model = "text-embedding-3-large"

NEO4J_USERNAME = "neo4j"
NEO4J_DATABASE = "neo4j"

AZURE_AI_SEARCH_ENDPOINT = os.getenv('AZURE_AI_SEARCH_ENDPOINT')
AZURE_AI_SEARCH_API_KEY = os.getenv('AZURE_AI_SEARCH_API_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
CONNECTION_STRING = os.getenv('CONNECTION_STRING')
AZURE_AI_SERVICE_API_KEY = os.getenv('AZURE_AI_SERVICE_API_KEY')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Neo4jへの接続情報を設定してgraphインスタンスを作成
graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    database=NEO4J_DATABASE
)


# neo4j serverに接続するdriverの設定
driver = GraphDatabase.driver(NEO4J_URI, auth=('neo4j', NEO4J_PASSWORD))

credential = AzureKeyCredential(AZURE_AI_SEARCH_API_KEY)

client = OpenAI(api_key=OPENAI_API_KEY)

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
# タイトルフィールドとコンテンツフィールドのEmbeddingsを生成する関数。
def generate_embeddings(text, model=model):
    return client.embeddings.create(input = [text], model=model).data[0].embedding

def generate_search_query(user_question: str) -> str:
    system_prompt = """
    
    以下のユーザーの質問を、ドキュメント検索に適したキーワードに変換してください。無駄な語句を除き、簡潔にしてください。
    
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_question}
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0,
    )

    return response.choices[0].message.content.strip()

# client = GraphCypherQAChain.from_llm(graph=graph, llm=llm, verbose=True, allow_dangerous_requests=True) 
def search_text(query,category):
  search_client = SearchClient(AZURE_AI_SEARCH_ENDPOINT, index_name, credential=credential)
  vector_query = VectorizedQuery(vector=generate_embeddings(query), k_nearest_neighbors=50, fields="text_vector")

  docs = search_client.search(
      search_text=generate_search_query(query),
      vector_queries= [vector_query],
      select=["title", "num", "category", "chunk"],
      filter=f"category eq '{category}'",
      query_type=QueryType.SEMANTIC, 
      semantic_configuration_name='default', 
      query_caption=QueryCaptionType.EXTRACTIVE, 
      query_answer=QueryAnswerType.EXTRACTIVE,
      top=5
  )


  doc_list = [i for i in docs]
  return doc_list


def run_graph_rag(query):

    try:
        # search_client = SearchClient(AZURE_AI_SEARCH_ENDPOINT, index_name, credential=credential)
        # vector_query = VectorizedQuery(vector=generate_embeddings(query), k_nearest_neighbors=50, fields="text_vector")

        # docs = search_client.search(
        # search_text=generate_search_query(query),
        # vector_queries= [vector_query],
        # select=["title", "num", "category", "chunk"],
        # query_type=QueryType.SEMANTIC, 
        # semantic_configuration_name='default', 
        # query_caption=QueryCaptionType.EXTRACTIVE, 
        # query_answer=QueryAnswerType.EXTRACTIVE,
        # top=3
        # )

        # doc_list = [i for i in docs]
        # num_list = [doc_list[i]['num'] for i in range(3)]
        # chunk_list = [(doc_list[i]['category'],doc_list[i]['title'],doc_list[i]['chunk'] ) for i in range(3)]

        doc_memo = search_text(query,"memo")
        doc_milestone = search_text(query,"マイルストーン")

        num_list = [doc_memo[i]['num'] for i in range(5)] + [doc_milestone[i]['num'] for i in range(5)]
        chunk_list = [("category : " + doc_memo[i]['category'],"name : " + doc_memo[i]['title'],doc_memo[i]['chunk'] ) for i in range(5)] +[("category : " + doc_milestone[i]['category'],"name : " + doc_milestone[i]['title'],doc_milestone[i]['chunk'] ) for i in range(5)]


        # -------------------- Cypher --------------------
        cypher = """
        MATCH (n)-[r]-(m)
        WHERE n.num IN $num
        RETURN n, r, m
        LIMIT 100
        """
        records = graph.query(cypher, params={"num": num_list})

        # -------------------- Python --------------------
        nodes = {}   # num をキーに一意化
        edges = []   # リレーションのみ

        for rec in records:
            src, dst, rel = rec["n"], rec["m"], rec["r"]

            # ------------- ノードを一意に格納 -------------
            for node in (src, dst):
                num = node["num"]
                if num not in nodes:                     # 初登場ノードだけ登録
                    nodes[num] = {
                        "num":         num,
                        "name":        node.get("name"),
                        "description": node.get("description")
                    }

            # ------------- リレーションを格納 -------------
            if isinstance(rel, tuple) and len(rel) == 3:
                # Neo4j の REST/API でごく稀に返るタプル形式への対処
                _, rel_type, _ = rel
            else:
                rel_type = rel.type                     # Relationship オブジェクト

            edges.append({
                "source": nodes[src["num"]]["num"],
                "target": nodes[dst["num"]]["num"],
                "type":   rel_type
            })

        # ---------- 最終出力（RAG 用シリアライズなど） ----------
        if records:

            graph_data = {
                "nodes": list(nodes.values()),   # dict → list
                "edges": edges
            }

        else:
            graph_data = chunk_list


        system_prompt = """
# 役割
あなたはPost Merger Integrationを専門とするコンサルタントです。

# 指示
ユーザーから質問に対して、与えられた{データソース}および一般的なベストプラクティスからステップバイステップで考えて回答してください。

# 制約条件
  * 参照元として、{データソース}と一般的なベストプラクティスのどちらを使用したか明示してください。
  * 両者の内容に矛盾がある場合は、{データソース}を優先してください。
  * {データソース}の{category}は以下を意味しています。
    - memo: 過去の案件のPMIの論点やナレッジが記載されたメモです。
    - マイルストーン: 一般的なPMIのマイルストーンが記載されています。過去案件のナレッジではありません。
  * 一般的なベストプラクティスとは、PMIに関する公開文献、専門家の知見、業界標準を指します。

# 出力形式
  * アドバイザリーのように可能な限り詳しく解説してください。
  * 番号（num）は回答に含めないでください。
  * 番号（num）だけの記載は避け、ユーザーが内容を理解できるタイトルを出力してください。
  * 必ず回答の一番最後に以下の形式で、参照したデータソースの「タイトル（name）」を必ず記載してください。
    
    【参照メモ】
        - {node['name']}
        - {node['name']}
        - {node['name']}
  * 回答はマークダウン形式で必要に応じて表などを仕様してわかりやすく回答してください。
"""

        messages = [{'role': 'system', 'content': system_prompt}]

        user_prompt = f"""
        【ユーザー質問】
        {query}

        【データソース】
        {graph_data}

        """

        messages.append({'role': 'user', 'content': user_prompt})

        client = OpenAI(api_key=OPENAI_API_KEY)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0,
            max_tokens=5000
        )
 
        return response.choices[0].message.content
    
    except Exception as e:
        return f"[エラー発生]: {str(e)}"