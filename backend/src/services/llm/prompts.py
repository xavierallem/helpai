"""Prompt templates for LLM-based query processing."""

from typing import List
from ...models.chunk import SearchResult


def build_rag_prompt(query: str, search_results: List[SearchResult]) -> str:
    """
    Build a RAG (Retrieval-Augmented Generation) prompt.


    """
    # Build context from search results
    context_parts = []
    for i, result in enumerate(search_results, 1):
        context_part = f"[Document {i}]\n{result.content}"
        if result.page_number:
            context_part += f"\n(Page {result.page_number})"
        context_parts.append(context_part)

    context = "\n\n".join(context_parts)

    # Build the full prompt
    prompt = f"""You are a legal document assistant. Your task is to answer questions based ONLY on the provided legal documents. Follow these guidelines:

1. Answer the question using ONLY information from the provided documents
2. If the answer is not in the documents, say "I don't have enough information in the provided documents to answer that question"
3. Cite specific documents when providing information (e.g., "According to Document 1...")
4. Be precise and accurate - legal information must be correct
5. If multiple documents contain relevant information, synthesize them in your answer
6. Keep your response clear and concise

Documents:
{context}

Question: {query}

Answer:"""

    return prompt


def build_contextual_prompt(
    query: str,
    search_results: List[SearchResult],
    conversation_context: List[dict]
) -> str:
    """
    Build a prompt with conversation context for multi-turn dialogue.

 
    """
    # Build context from search results
    context_parts = []
    for i, result in enumerate(search_results, 1):
        context_part = f"[Document {i}]\n{result.content}"
        if result.page_number:
            context_part += f"\n(Page {result.page_number})"
        context_parts.append(context_part)

    context = "\n\n".join(context_parts)

    # Build conversation summary if there's context
    conversation_summary = ""
    if conversation_context:
        # Get last few exchanges (excluding the current query)
        recent_messages = conversation_context[-4:]  # Last 2 exchanges
        if recent_messages:
            conversation_summary = "\n\nPrevious conversation:\n"
            for msg in recent_messages:
                role = msg['role'].capitalize()
                conversation_summary += f"{role}: {msg['content']}\n"

    # Build the full prompt
    prompt = f"""You are a legal document assistant helping with questions about legal documents. Follow these guidelines:

1. Answer using ONLY information from the provided documents
2. Consider the conversation history when answering
3. If the answer is not in the documents, say "I don't have enough information in the provided documents to answer that question"
4. Cite specific documents (e.g., "According to Document 1...")
5. Be precise and accurate
6. Keep responses clear and concise
{conversation_summary}

Relevant Documents:
{context}

Current Question: {query}

Answer:"""

    return prompt
