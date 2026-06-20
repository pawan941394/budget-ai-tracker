# Budget App Architecture

## Goal

Build a budget app where users can upload payment images or fill a form manually, extract expense data into JSON, save the expense, and chat with an assistant that always uses the latest database state.

## Core product flow

1. User uploads an image or enters expense details manually.
2. System extracts or normalizes data into a structured JSON payload.
3. User reviews the extracted data before saving.
4. Expense is written to the database.
5. Chatbot answers questions using the latest stored expense data.
6. If the user edits the expense later, the chatbot reflects the updated record.

## Stack split

- **Django**: auth, users, database models, admin, and standard CRUD.
- **FastAPI**: lookup and retrieval service for AI/chat requests.

This split keeps Django as the source of truth while letting FastAPI handle retrieval-heavy endpoints cleanly.

## Data model

### Core entities

- User
- Ledger
- Expense
- Category
- Merchant
- RecurringExpense
- ChatSession
- ChatMessage

### Suggested expense fields

- merchant
- amount
- currency
- date
- category
- payment_method
- notes
- source_type
- confidence
- raw_text
- user_id
- session_id

These fields should stay stable in v1. Future fields can be added later if required.

## Retrieval design

The assistant should not query the database directly. Instead, the backend should:

1. Query the latest structured expense records.
2. Pull relevant recent edits and recurring items.
3. Use `grep`-style search only as a fallback for raw OCR text, prompts, or notes.
4. Pass only the relevant slice of context to the LLM.

## Search strategy

### Main path

Use structured database filtering for:

- merchant
- amount
- date
- category
- ledger
- user ownership

### Fallback path

Use `grep`-style text lookup for:

- OCR text
- receipt notes
- user prompts
- exact or near-exact text matches

### Matching behavior

- Exact matching first.
- Fuzzy matching second.
- Keep both for better recall on text-heavy queries.

## Graph-style relationships

The app can keep a small graph-like relation layer for better retrieval without using vector search.

Useful edges:

- user belongs to ledger
- expense belongs to user
- expense belongs to category
- expense paid at merchant
- expense updated by chat session
- recurring expense generates expense

This gives the chatbot stronger context than raw text search alone.

## Non-goals for v1

- No RAG pipeline
- No vector search
- No semantic embedding store
- No direct database access from the LLM

## Chat editing behavior

- The chatbot can help the user edit expenses.
- Edits update the DB directly.
- Old chat messages remain as history.
- New chat replies always use the latest DB state.

## Recurring expenses

Support recurring expenses in v1 with a simple rule such as monthly by default. This improves budget summaries and future projections without adding unnecessary complexity.

## Budget summaries

Start with:

- total income
- total spent
- remaining balance
- category-wise spend
- overspend warnings

Add forecasting and advanced insights later.

## Future growth

If the app grows, it can later add:

- richer graph queries
- more advanced fuzzy lookup
- budget goals
- trend analysis
- forecasting
