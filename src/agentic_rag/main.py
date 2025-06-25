import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from langchain_core.tools import Tool
from langchain_core.messages import HumanMessage, AIMessage
from core.rag.retriever import VectorRetriever
from core.config import settings
from langchain.chat_models import init_chat_model
from langgraph.graph import MessagesState
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition

def retriever_tool_func(query: str):
    """
    Function that uses VectorRetriever to search for financial information.
    Returns a dictionary with context from retrieved documents.
    """
    try:
        # Create a new retriever instance for this query
        retriever = VectorRetriever(query=query)
        
        # Retrieve documents using the retriever
        hits = retriever.retrieve_top_k(
            k=5,  # Retrieve 5 documents
            to_expand_to_n_queries=2,  # Expand to 2 queries
            collection_type=None,  # Search all collections
            additional_filters={}  # No additional filters
        )
        
        # Extract content from the hits
        context = []
        for hit in hits:
            if hasattr(hit, 'payload') and 'content' in hit.payload:
                context.append(hit.payload['content'])
        
        # If no content found, return empty context
        if not context:
            return {"context": ["No relevant financial information found for your query."]}
        
        return {"context": context}
        
    except Exception as e:
        print(f"Error in retriever_tool_func: {str(e)}")
        return {"context": [f"Error retrieving information: {str(e)}"]}

# Create a retriever tool
retriever_tool = Tool.from_function(
    name="financial_knowledge_base",
    description="Search for financial information including earnings calls, SEC filings, financial news, and educational content. Use this tool when you need to find specific financial data, company information, market analysis, or educational content about financial concepts.",
    func=retriever_tool_func
)

# Initialize the LLM
llm = init_chat_model("gpt-4o", temperature=0)

# Create the prompt template
GENERATE_PROMPT = (
    "You're FinBud – a friendly and supportive financial buddy for Gen Z. "
    "You're here to help users figure out their money stuff with clear, real, and chill advice.\n\n"
    
    "Detect the user's emotion and respond appropriately — be warm, validating, and casual like a trusted friend.\n\n"

    "Use the following information to answer their question. "
    "If the context isn't enough, it's okay to say 'I'm not totally sure, but here's something that might help!'\n\n"
    
    "💬 User question: {question}\n"
    "📚 Retrieved context: {context}\n\n"
    
    "📢 Now give your response in **3 short, helpful sentences max**, using simple language and friendly Gen Z tone. "
    "You can include emojis if it fits naturally. Keep it real and relatable."
)



# Create the agent executor
llm_with_tools = llm.bind_tools([retriever_tool])

def generate_query_or_respond(state: MessagesState):
    """Generate a response using the LLM with tools."""
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

def generate_answer(state: MessagesState):
    """Generate an answer."""
    # Get the original question from the first message
    question = state["messages"][0].content
    
    # Find the tool response (should be the last message with tool results)
    context = ""
    for msg in reversed(state["messages"]):
        if hasattr(msg, 'content') and isinstance(msg.content, str) and "context" in msg.content:
            # Extract context from the tool response
            try:
                import json
                # The tool response might be in JSON format
                if msg.content.startswith('{'):
                    data = json.loads(msg.content)
                    if 'context' in data:
                        context = '\n'.join(data['context'])
                        break
                else:
                    context = msg.content
                    break
            except:
                context = msg.content
                break
    
    # Format the prompt
    prompt = GENERATE_PROMPT.format(question=question, context=context)
    response = llm.invoke([{"role": "user", "content": prompt}])
    return {"messages": [response]}

def build_graph():
    workflow = StateGraph(MessagesState)

    # Define the nodes we will cycle between
    workflow.add_node("generate_query_or_respond", generate_query_or_respond)
    workflow.add_node("retrieve", ToolNode([retriever_tool]))
    workflow.add_node("generate_answer", generate_answer)

    workflow.add_edge(START, "generate_query_or_respond")

    # Decide whether to retrieve
    workflow.add_conditional_edges(
        "generate_query_or_respond",
        # Assess LLM decision (call `retriever_tool` tool or respond to the user)
        tools_condition,
        {
            # Translate the condition outputs to nodes in our graph
            "tools": "retrieve",
            END: END,
        },
    )

    # Edges taken after the `retrieve` node is called.
    workflow.add_conditional_edges(
        "retrieve",
        # Route to generate_answer after retrieval
        lambda state: "generate_answer",
        {
            "generate_answer": "generate_answer",
        }
    )
    
    workflow.add_edge("generate_answer", END)

    # Compile
    return workflow.compile()

def main():
    """
    Example usage of the Agentic RAG system.
    """
    print("Building and running Financial RAG Graph...")
    
    # Build the graph
    graph = build_graph()
    
    # Run the graph
    for chunk in graph.stream(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "I'm worried. This is my first time doing tax. What should I do first to file tax?",
                }
            ]
        }
    ):
        for node, update in chunk.items():
            print("Update from node", node)
            update["messages"][-1].pretty_print()
            print("\n\n")
    

if __name__ == "__main__":
    main()