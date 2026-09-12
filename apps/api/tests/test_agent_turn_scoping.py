import uuid

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage

from app.ai.agent import Agent


class _FakeToolCallingModel(FakeMessagesListChatModel):
    """FakeMessagesListChatModel plays back canned AIMessages in order regardless
    of input, but doesn't implement bind_tools (create_agent calls it once at
    construction time) -- make it a no-op so the canned tool_calls still work."""

    def bind_tools(self, tools, **kwargs):
        return self


def _search_stub(query: str):
    """Stub tool function mirroring RAG.retrieve_images's shape.

    Args:
        query: Search query string.
    """
    return (
        [{"type": "text", "text": f"found items for {query}"}],
        {"uris": ["/data/products/high_images/images/1.jpg"]},
    )


def test_invoke_agent_msg_does_not_leak_prior_turn_uris():
    tool_call_id = str(uuid.uuid4())
    # create_agent invokes the model once per turn, plus once more per tool call
    # it decides to make. Turn 1 calls the tool then answers (2 model calls);
    # turn 2 answers directly with no tool call (1 model call).
    responses = [
        AIMessage(
            content="",
            tool_calls=[{"name": "retrieve_images", "args": {"query": "red shoes"}, "id": tool_call_id}],
        ),
        AIMessage(content="Here are some red shoes for you."),
        AIMessage(content="Sure, red goes with almost anything."),
    ]
    # SummarizationMiddleware's keep=("fraction", 0.3) needs model profile info to
    # compute a token budget; a fake model has none, so supply one directly.
    model = _FakeToolCallingModel(responses=responses, profile={"max_input_tokens": 100_000})
    rag = type("StubRag", (), {"retrieve_images": staticmethod(_search_stub)})()
    agent = Agent(assistant_model=model, summary_model=model, rag=rag)

    thread_id = "thread-1"
    turn1 = agent.invoke_agent_msg([HumanMessage(content="find me red shoes")], thread_id=thread_id)
    assert turn1["uris"] == ["/data/products/high_images/images/1.jpg"]

    turn2 = agent.invoke_agent_text("is red a good color for shoes?", thread_id=thread_id)
    assert turn2["uris"] == []
