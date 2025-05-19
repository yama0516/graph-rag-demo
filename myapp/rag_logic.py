import os
from langchain_community.document_loaders import TextLoader
from langchain_anthropic import ChatAnthropic
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI
from langchain.chains import GraphCypherQAChain 
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
import json

from neo4j import GraphDatabase, basic_auth
import pandas as pd

NEO4J_USERNAME = "neo4j"
NEO4J_DATABASE = "neo4j"

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




llm = ChatOpenAI(  
    model="gpt-4.1",
    temperature=0

) 

 

client = GraphCypherQAChain.from_llm(graph=graph, llm=llm, verbose=True, allow_dangerous_requests=True) 

def run_graph_rag(question):

    try:
        answer = client.invoke({"query": question}) 
        return answer['result']
    
    except Exception as e:
        return f"[エラー発生]: {str(e)}"