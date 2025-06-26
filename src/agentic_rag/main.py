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

def earnings_retriever_tool_func(query: str):
    """
    Specialized function to search earnings call transcripts and quarterly reports.
    """
    try:
        retriever = VectorRetriever(query=query)
        
        hits = retriever.retrieve_top_k(
            k=3,
            to_expand_to_n_queries=2,
            collection_type="earnings_call_transcripts",  # Specific collection
            additional_filters={}
        )
        
        context = []
        for hit in hits:
            if hasattr(hit, 'payload') and 'content' in hit.payload:
                context.append(hit.payload['content'])
        
        if not context:
            return {"context": ["No earnings call transcripts or quarterly reports found for your query."]}
        
        return {"context": context}
        
    except Exception as e:
        print(f"Error in earnings_retriever_tool_func: {str(e)}")
        return {"context": [f"Error retrieving earnings information: {str(e)}"]}

def sec_filings_retriever_tool_func(query: str):
    """
    Specialized function to search SEC filings and regulatory documents.
    """
    try:
        retriever = VectorRetriever(query=query)
        
        hits = retriever.retrieve_top_k(
            k=3,
            to_expand_to_n_queries=2,
            collection_type="edgar_fillings",  # Specific collection
            additional_filters={}
        )
        
        context = []
        for hit in hits:
            if hasattr(hit, 'payload') and 'content' in hit.payload:
                context.append(hit.payload['content'])
        
        if not context:
            return {"context": ["No SEC filings or regulatory documents found for your query."]}
        
        return {"context": context}
        
    except Exception as e:
        print(f"Error in sec_filings_retriever_tool_func: {str(e)}")
        return {"context": [f"Error retrieving SEC filings: {str(e)}"]}

def news_retriever_tool_func(query: str):
    """
    Specialized function to search financial news and market analysis.
    """
    try:
        retriever = VectorRetriever(query=query)
        
        hits = retriever.retrieve_top_k(
            k=3,
            to_expand_to_n_queries=2,
            collection_type="financial_news",  # Specific collection
            additional_filters={}
        )
        
        context = []
        for hit in hits:
            if hasattr(hit, 'payload') and 'content' in hit.payload:
                context.append(hit.payload['content'])
        
        if not context:
            return {"context": ["No financial news or market analysis found for your query."]}
        
        return {"context": context}
        
    except Exception as e:
        print(f"Error in news_retriever_tool_func: {str(e)}")
        return {"context": [f"Error retrieving financial news: {str(e)}"]}

def macro_retriever_tool_func(query: str):
    """
    Specialized function to search macroeconomic reports and economic data.
    """
    try:
        retriever = VectorRetriever(query=query)
        
        hits = retriever.retrieve_top_k(
            k=3,
            to_expand_to_n_queries=2,
            collection_type="macro_economic_reports",  # Specific collection
            additional_filters={}
        )
        
        context = []
        for hit in hits:
            if hasattr(hit, 'payload') and 'content' in hit.payload:
                context.append(hit.payload['content'])
        
        if not context:
            return {"context": ["No macroeconomic reports or economic data found for your query."]}
        
        return {"context": context}
        
    except Exception as e:
        print(f"Error in macro_retriever_tool_func: {str(e)}")
        return {"context": [f"Error retrieving macroeconomic data: {str(e)}"]}

def education_retriever_tool_func(query: str):
    """
    Specialized function to search educational content and financial concepts.
    """
    try:
        retriever = VectorRetriever(query=query)
        
        hits = retriever.retrieve_top_k(
            k=3,
            to_expand_to_n_queries=2,
            collection_type="investopedia",  # Specific collection
            additional_filters={}
        )
        
        context = []
        for hit in hits:
            if hasattr(hit, 'payload') and 'content' in hit.payload:
                context.append(hit.payload['content'])
        
        if not context:
            return {"context": ["No educational content or financial concepts found for your query."]}
        
        return {"context": context}
        
    except Exception as e:
        print(f"Error in education_retriever_tool_func: {str(e)}")
        return {"context": [f"Error retrieving educational content: {str(e)}"]}

def news_and_macro_retriever_tool_func(query: str):
    """
    Specialized function to search both financial news and macroeconomic reports.
    """
    try:
        retriever = VectorRetriever(query=query)
        
        # Search financial news
        news_hits = retriever.retrieve_top_k(
            k=2,
            to_expand_to_n_queries=1,
            collection_type="financial_news",  # Specific collection
            additional_filters={}
        )
        
        # Search macro economic reports
        macro_hits = retriever.retrieve_top_k(
            k=2,
            to_expand_to_n_queries=1,
            collection_type="macro_economic_reports",  # Specific collection
            additional_filters={}
        )
        
        context = []
        
        # Add news content
        for hit in news_hits:
            if hasattr(hit, 'payload') and 'content' in hit.payload:
                context.append(f"[Financial News] {hit.payload['content']}")
        
        # Add macro content
        for hit in macro_hits:
            if hasattr(hit, 'payload') and 'content' in hit.payload:
                context.append(f"[Economic Report] {hit.payload['content']}")
        
        if not context:
            return {"context": ["No financial news or economic reports found for your query."]}
        
        return {"context": context}
        
    except Exception as e:
        print(f"Error in news_and_macro_retriever_tool_func: {str(e)}")
        return {"context": [f"Error retrieving news and economic data: {str(e)}"]}

# Create specialized retriever tools
retriever_tool = Tool.from_function(
    name="financial_knowledge_base",
    description="Search for financial information including earnings calls, SEC filings, financial news, and educational content. Use this tool when you need to find specific financial data, company information, market analysis, or educational content about financial concepts.",
    func=retriever_tool_func
)

earnings_tool = Tool.from_function(
    name="earnings_calls_search",
    description="Search for earnings call transcripts and quarterly reports. Use this when you need information about company earnings, financial performance, management commentary, revenue growth, profit margins, or quarterly results. Perfect for questions about how a company is performing financially.",
    func=earnings_retriever_tool_func
)

sec_filings_tool = Tool.from_function(
    name="sec_filings_search",
    description="Search for SEC filings, annual reports, and regulatory documents. Use this when you need official financial statements, risk factors, regulatory information, company disclosures, or legal compliance details. Great for understanding a company's official financial position and legal obligations.",
    func=sec_filings_retriever_tool_func
)

news_tool = Tool.from_function(
    name="financial_news_search",
    description="Search for financial news, market analysis, and current events. Use this when you need recent market information, analyst opinions, breaking financial news, stock price movements, or market trends. Ideal for staying updated on current financial events and market sentiment.",
    func=news_retriever_tool_func
)

macro_tool = Tool.from_function(
    name="macroeconomic_reports_search",
    description="Search for macroeconomic reports and economic data. Use this when you need information about inflation, interest rates, GDP growth, economic policies, Federal Reserve decisions, or broader economic trends that affect financial markets. Perfect for understanding the big picture economic environment.",
    func=macro_retriever_tool_func
)

education_tool = Tool.from_function(
    name="financial_education_search",
    description="Search for educational content and financial concepts. Use this when you need to explain financial terms, investment strategies, tax concepts, or basic financial literacy topics. Great for helping users understand financial jargon or learn about new financial concepts.",
    func=education_retriever_tool_func
)

news_and_macro_tool = Tool.from_function(
    name="market_environment_search",
    description="Search for both financial news and macroeconomic reports to understand the current market environment. Use this when you need a comprehensive view of both current market events and broader economic trends. Perfect for questions about how economic conditions are affecting markets or specific investments.",
    func=news_and_macro_retriever_tool_func
)

# Initialize the LLM
llm = init_chat_model("gpt-4o", temperature=0)

# Create the prompt template
GENERATE_PROMPT = (
    "You're FinBud - a friendly and supportive financial buddy for Gen Z. "
    "You're here to help users figure out their money stuff with clear, real, and chill advice.\n\n"
    
    "Detect the user's emotion and respond appropriately — be warm, validating, and casual like a trusted friend.\n\n"

    "Use the following information to answer their question. "
    "If the context isn't enough, it's okay to say 'I'm not totally sure, but here's something that might help!'\n\n"
    
    "💬 User question: {question}\n"
    "📚 Retrieved context: {context}\n\n"
    
    "📢 Now give your response in **3 helpful sentences max**, using simple language and friendly Gen Z tone. "
    "You can include emojis if it fits naturally. Keep it real and relatable."
)



# Create the agent executor
llm_with_tools = llm.bind_tools([
    retriever_tool,
    earnings_tool,
    sec_filings_tool,
    news_tool,
    macro_tool,
    education_tool,
    news_and_macro_tool
])

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
    workflow.add_node("retrieve", ToolNode([
        retriever_tool,
        earnings_tool,
        sec_filings_tool,
        news_tool,
        macro_tool,
        education_tool,
        news_and_macro_tool
    ]))
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
                    "content": "Give some details on aapl",
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