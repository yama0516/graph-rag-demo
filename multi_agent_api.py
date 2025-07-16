
import asyncio
import os
from typing import Callable, List, Tuple
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import SelectorGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
import openai
from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_type = "openai"
model = "gpt-4o"

app = FastAPI()
router = APIRouter(prefix="/rag", tags=["RAG"])

# Request/Response models
class RunRequest(BaseModel):
    task: str

class Message(BaseModel):
    sender: str
    content: str

class ChatRequest(BaseModel):
    user_input: str
    history: List[Tuple[str, str]]

class ChatResponse(BaseModel):
    answer: str

def run_sync(task: str, on_message: Callable[[str, str], None]) -> None:
    async def _run():
        client = OpenAIChatCompletionClient(model=model)

        facilitator = AssistantAgent(
            name="facilitator_agent",
            description="議論の司令塔。タスクを分割して割り振る。全員が発言した後、最後に要約して終了する。",
            model_client=client,
            system_message="""
あなたはプロジェクトマネージャーです。

エージェント同士の意見が出揃った後、次に必要なタスクがあれば <agent>: <task> の形式で指示を出し、全体の方向性を導いてください。
タスクは将来日付ではなく、必ずこの議論の中で完了できるものとしてください。
- strategist_agent: 戦略立案
- operations_agent: 現場担当。実務の視点で提案や改善案を検討
- risk_manager_agent: リスク・法務・倫理面の指摘と対策
- engineer_agent: システム実装・自動化アプローチ

他のエージェントの意見に対して、賛成/反対/補足を行ってください。
実際に人間が議論しているように会話してください。
受け身にならず、積極的に発言してください。

"""
        )

        strategist = AssistantAgent(
            name="strategist_agent",
            description="ビジネス戦略・全体方針の立案担当",
            model_client=client,
            system_message="""
あなたは戦略コンサルタントです。業務課題に対して企業全体の視点から方針や優先順位を提案してください。
他のエージェントの意見に対して、賛成/反対/補足を行ってください。
実際に人間が議論しているように会話してください。
受け身にならず、積極的に発言してください。
"""
        )

        operations = AssistantAgent(
            name="operations_agent",
            description="現場担当。実務の視点で提案や改善案を検討",
            model_client=client,
            system_message="""
あなたは業務現場の管理者です。現場の制約を踏まえて具体的な改善アイデアを提示してください。
他のエージェントの意見に対して、賛成/反対/補足を行ってください。
実際に人間が議論しているように会話してください。
受け身にならず、積極的に発言してください。
"""
        )

        risk_manager = AssistantAgent(
            name="risk_manager_agent",
            description="リスク管理・法務・ガバナンスを担当",
            model_client=client,
            system_message="""
あなたはリスクマネージャーです。提案された解決策のリスク評価と注意点を述べてください。
他のエージェントの意見に対して、賛成/反対/補足を行ってください。
実際に人間が議論しているように会話してください。
受け身にならず、積極的に発言してください。
"""
        )

        engineer = AssistantAgent(
            name="engineer_agent",
            description="AI・IT技術者として実装視点で検討",
            model_client=client,
            system_message="""
あなたはシステムエンジニアです。技術的実装案や自動化アプローチを提示してください。
他のエージェントの意見に対して、賛成/反対/補足を行ってください。
実際に人間が議論しているように会話してください。
受け身にならず、積極的に発言してください。
"""
        )

        termination = (
            TextMentionTermination("TERMINATE")
            | MaxMessageTermination(max_messages=10)
        )

        participants = [facilitator, strategist, operations, risk_manager, engineer]
        team = SelectorGroupChat(
            participants=participants,
            model_client=client,
            termination_condition=termination,
            allow_repeated_speaker=False,
        )

        agent_names = {p.name for p in participants}

        # ストリーム出力をコールバックで逐次表示
        async for msg in team.run_stream(task=task):
            sender = (
                getattr(msg, "sender_name", None)
                or getattr(msg, "source", None)
                or type(msg).__name__
            )
            if sender not in agent_names:
                continue

            content = (getattr(msg, "content", None) or "").strip()
            on_message(sender, content)

    asyncio.run(_run())

def chat_with_gpt(user_input: str, agent_input: list[tuple[str,str]]):
    """
    指定したプロンプトを渡して ChatCompletion を呼び出し、
    モデルからの応答を返す関数。
    """
    history_lines = [
        f"{sender}: {msg}"
        for sender, msg in agent_input
    ]
    system_prompt = """
    あなたはエージェントのsuprevisorです。エージェントの会話を踏まえてユーザーに対して最終的な回答を作成してください。
    ユーザーに対しては各エージェントの意見をまとめて報告する旨を伝えてください。
    エージェントの議論の流れを踏まえ、上司やお客さんに説明するように丁寧に回答してください。
"""
    prompt = f"""
    # ユーザーからのインプット
    {user_input}

    # エージェントの会話履歴
    {history_lines}
"""
    messages = [
            {"role": "system",   "content": system_prompt},
            {"role": "user",     "content": prompt},
        ]

    response = openai.chat.completions.create(
        model="o3",        
        messages=messages,
        # 以下オプション（必要に応じて調整）
        # max_tokens=5000,        # 出力トークン数の上限
        max_completion_tokens=5000
    )

    # 応答は choices[0].message.content に入っている
    return response.choices[0].message.content

@router.post("/run",response_model=List[Message])
def run_task(req: RunRequest):
    """エージェントチームを起動し、生成されたメッセージを一括返却します。"""
    messages: List[Message] = []
    def collector(sender: str, content: str):
        messages.append(Message(sender=sender, content=content))
    try:
        run_sync(req.task, collector)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return messages

@router.post("/chat", response_model=ChatResponse)
def supervise_chat(req: ChatRequest):
    """エージェントの議論結果を GPT でまとめて返却します。"""
    try:
        answer = chat_with_gpt(req.user_input, req.history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return ChatResponse(answer=answer)

# Include and run
app.include_router(router)
