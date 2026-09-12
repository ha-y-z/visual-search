from langchain.chat_models import BaseChatModel
from langchain.messages import HumanMessage


class QueryRewriter:
    def __init__(self, model: BaseChatModel):
        self.model = model

    def rewrite_query(self, query: str) -> str:
        messages = [
            HumanMessage(
                f"""
                You are a query rewriting fashion assistant that helps improve search queries. 
                Rewrite the user's query to be more effective for searching.
                - Use more general fashion terms.
                - Include relevant fashion item types.
                - ONLY include the rewritten query in your response.
                User's query: "{query}"
                """,
            ),
        ]
        rewritten_query = self.model.invoke(messages)
        return rewritten_query.text
