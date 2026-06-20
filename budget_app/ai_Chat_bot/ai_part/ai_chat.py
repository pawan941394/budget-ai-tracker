import json
import os
import sys
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from dotenv import load_dotenv
from .db_utils import init_db, save_history, load_history, create_session, list_user_sessions

load_dotenv()


def build_agent(api_key: str | None = None, transactions: list[dict] | None = None, phone_number: str | None = None) -> Agent:
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key

    transactions = transactions or []

    agent = Agent(
        "google:gemini-flash-lite-latest",
        system_prompt=(
            "You are a highly capable budget assistant for the user. "
            "Use the user's transaction JSON and chat history as the primary source of truth. "
            "The user's phone number is the session identifier. "
            "If the user asks for recent transactions, summarize the latest items from the current user's transaction JSON directly. "
            "You have a tool `grep_transaction_data` to search the current user's transaction JSON. "
            "You have a tool `get_recent_transactions` to return the latest transactions. "
            "You also have a tool `generate_data_schema_diagram` to show the Mermaid diagram of the data structure. "
            "And you have a tool `generate_spending_histogram` to create a visual spending chart using Mermaid xychart-beta. "
            "If a user asks about their spending, recent transactions, or a specific merchant, "
            "your FIRST action should always be to use `get_recent_transactions` or `grep_transaction_data`. "
            "Whenever a user asks for a histogram, chart, or visual representation of spending, use `generate_spending_histogram`."
            "Always summarize the findings clearly for the user."
        ),
    )

    @agent.tool_plain
    def generate_spending_histogram() -> str:
        """
        Generate a Mermaid histogram chart of spending based on the current user's transactions.
        Use this when the user asks for a histogram, chart, or analysis of their expenses.
        Returns Mermaid code block.
        """
        amounts = []
        try:
            for item in transactions:
                if item.get("amount") is not None:
                    amounts.append(float(item["amount"]))
        except Exception as e:
            return f"Error reading transactions: {str(e)}"

        if not amounts:
            return "No transaction amounts found to plot."

        try:
            max_amount = max(amounts)
            num_bins = 5 if max_amount <= 500 else 10
            bin_width = (max_amount / num_bins) if max_amount > 0 else 100

            bins = [0] * num_bins
            labels = []
            for i in range(num_bins):
                start = i * bin_width
                end = (i + 1) * bin_width
                labels.append(f"{int(start)}-{int(end)}")

                for amt in amounts:
                    if start <= amt < end or (i == num_bins - 1 and amt >= start):
                        bins[i] += 1

            mermaid_code = "xychart-beta\n"
            mermaid_code += "    title \"Spending Distribution\"\n"
            mermaid_code += f"    x-axis [{', '.join(labels)}]\n"
            mermaid_code += "    y-axis \"Frequency\"\n"
            mermaid_code += f"    bar [{', '.join(map(str, bins))}]"

            return f"Here is the histogram of your spending:\n\n```mermaid\n{mermaid_code}\n```"
        except Exception as e:
            return f"Error creating Mermaid histogram: {str(e)}"

    @agent.tool_plain
    def generate_data_schema_diagram() -> str:
        """
        Generate a Mermaid class diagram showing the structure of the Transaction model.
        Use this when the user asks about how data is stored or asks for a schema diagram.
        """
        mermaid_code = """
classDiagram
    class TransactionData {
        +String status
        +Float amount
        +String sender_name
        +String sender_upi
        +String receiver_name
        +String receiver_upi
        +String bank
        +String timestamp
        +String reference_id
        +String payment_type
        +String utr_id
    }
    """
        return f"Here is the Mermaid diagram for the transaction data schema:\n\n```mermaid{mermaid_code}```"

    @agent.tool_plain
    def current_date_and_time() -> str:
        """
        Return the current date and time. Use this when the you required it for any reason, such as when the user asks for recent transactions or wants to know the current date.
        """
        from datetime import datetime
        now = datetime.now()
        return f"The current date and time is: {now.strftime('%Y-%m-%d %H:%M:%S')}"

    @agent.tool_plain
    def grep_transaction_data(query: str) -> str:
        """
        Search the current user's transaction JSON based on a query.
        """
        matches = []
        try:
            for item in transactions:
                item_text = json.dumps(item, ensure_ascii=True)
                if query.lower() in item_text.lower():
                    matches.append(item_text)
        except Exception as e:
            return f"Error reading transactions: {str(e)}"

        if not matches:
            scope = f" for phone number {phone_number}" if phone_number else ""
            return f"No transactions found matching '{query}'{scope}. Try a shorter or different keyword."

        return "\n---\n".join(matches)

    @agent.tool_plain
    def get_recent_transactions(limit: int = 5) -> str:
        recent_items = transactions[-limit:]
        if not recent_items:
            return "No transactions found for this user."
        return json.dumps(recent_items, ensure_ascii=True, indent=2)

    return agent


def chat(username, session_id):
    init_db()
    create_session(session_id, username)
    
    print(f"--- Welcome {username} ---")
    print(f"Chat Session: {session_id}")
    print("Type 'exit' or 'quit' to stop.")
    
    # Load history from DB
    messages = load_history(session_id)
    if messages:
        print(f"--- Resumed {len(messages)} messages from history ---")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            break

        agent = build_agent(os.getenv("GOOGLE_API_KEY"))
        result = agent.run_sync(user_input, message_history=messages)
        messages.extend(result.new_messages())
        
        # Save updated history to DB
        save_history(session_id, messages)
        
        print(f"AI: {result.output}")

if __name__ == "__main__":
    user = "pawan1"
    sess = "session_001"
    chat(user, sess)
