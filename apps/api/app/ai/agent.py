import logging

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain.chat_models import BaseChatModel
from langchain_core.messages import AIMessageChunk, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import StructuredTool
from langgraph.checkpoint.memory import InMemorySaver

from app.timing import timed_stage

from .rag import RAG

logger = logging.getLogger(__name__)


class Agent:
    def __init__(
        self, assistant_model: BaseChatModel, summary_model: BaseChatModel, rag: RAG
    ):
        self.rag = rag
        retrieve_images_tool = StructuredTool.from_function(
            func=self.rag.retrieve_images,
            name="retrieve_images",
            description="Searches the product database for fashion items. ONLY use this when the user explicitly asks to find or search for specific products/items.",
            response_format="content_and_artifact",
            parse_docstring=True,
        )
        self.agent = create_agent(
            model=assistant_model,
            tools=[retrieve_images_tool],
            system_prompt="""
                You are a helpful fashion shopping assistant, who talks in the gen z language.
                Your task is to assist users in finding fashion items based on their queries.
                Always answer to fashion-related queries and provide relevant information.
                If the topic is not related to fashion, politely inform the user that you can only assist with fashion-related queries.
                
                TOOL USAGE RULES:
                - If the user is just asking for general fashion advice, trends, or styling tips, answer them directly using your knowledge. DO NOT use the retrieve_images tool.
                - If the user EXPLICITLY asks to search for, find, see, or buy fashion items, you MUST use the 'retrieve_images' tool to fetch relevant images based on their query.
                - QUERY REFORMULATION: When calling the 'retrieve_images' tool, synthesize the user's latest request with relevant past context to create one comprehensive search query. IGNORE the images BUT INCORPORATE text.
            """,
            checkpointer=InMemorySaver(),
            middleware=[
                SummarizationMiddleware(
                    model=summary_model,
                    trigger=("tokens", 50000),
                    keep=("fraction", 0.3),
                )
            ],
        )

    def invoke_agent_msg(self, messages, thread_id: str = "1"):
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        # InMemorySaver checkpoints across turns, so response["messages"] is the
        # entire thread history, not just this turn's -- scanning it unscoped would
        # resurface prior turns' retrieve_images artifacts alongside the current one.
        prior_state = self.agent.get_state(config)
        prior_message_count = len(prior_state.values.get("messages", [])) if prior_state.values else 0
        with timed_stage(logger, "LLM invoke"):
            response = self.agent.invoke({"messages": messages}, config)
        uris = []
        for msg in reversed(response["messages"][prior_message_count:]):
            if isinstance(msg, ToolMessage) and msg.name == "retrieve_images":
                uris.extend(msg.artifact.get("uris", []))
        return {"text": response["messages"][-1].text, "uris": uris}

    def invoke_agent_text(self, text: str, thread_id: str = "1"):
        message = HumanMessage(content=text)
        return self.invoke_agent_msg([message], thread_id=thread_id)

    def stream_agent_msg(self, messages, thread_id: str = "1"):
        with timed_stage(logger, "LLM stream"):
            for msg, metadata in self.agent.stream(
                {"messages": messages},
                {"configurable": {"thread_id": thread_id}},
                stream_mode="messages",
            ):
                if not ('lc_source' in metadata and metadata['lc_source'] == 'summarization'):  # type: ignore[index]
                    if isinstance(msg, AIMessageChunk) and msg.content:
                        yield msg.text

                    elif isinstance(msg, ToolMessage) and msg.name == "retrieve_images" and msg.artifact and "uris" in msg.artifact:
                        yield {"type": "images", "uris": msg.artifact["uris"]}
                else:
                    if isinstance(msg, HumanMessage) and msg.content:
                        logger.debug("Summarization middleware: %s", msg.content)

    def stream_agent_text(self, text: str, thread_id: str = "1"):
        message = HumanMessage(content=text)
        return self.stream_agent_msg([message], thread_id=thread_id)
