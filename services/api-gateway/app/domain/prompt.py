from langchain_core.prompts import PromptTemplate

BASE_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        "You are a helpful assistant. Use the context to answer the question with citations.\n"
        "Context:\n{context}\n\nQuestion: {question}\n\n"
        "Respond with concise sentences and cite sources as [source:chunk_id]."
    ),
)
