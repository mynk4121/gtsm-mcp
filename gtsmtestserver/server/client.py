import asyncio
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# =========================================================
# CONFIG
# =========================================================

CONFIG_PATH = r"C:\Users\mynka\Desktop\bedrock test\gtsmtestserver\server\config.json"


def load_config():
    return json.loads(Path(CONFIG_PATH).read_text())


# =========================================================
# SAFE TEXT EXTRACTION
# =========================================================

def extract_text(result):

    try:

        if hasattr(result, "content"):

            if isinstance(result.content, list):

                parts = []

                for item in result.content:

                    if hasattr(item, "text"):
                        parts.append(item.text)
                    else:
                        parts.append(str(item))

                return "\n".join(parts)

        return str(result)

    except Exception:
        return str(result)


# =========================================================
# TOOL FORMAT
# =========================================================

def convert_tool(tool):

    return {
        "name": tool.name,
        "description": tool.description or "",
        "parameters": tool.inputSchema
    }


# =========================================================
# USER RESOLVER
# =========================================================

async def resolve_user(api_session, name):

    try:

        result = await api_session.call_tool(
            "api_find_user_by_name",
            {"name": name}
        )

        text = extract_text(result)

        if not text or "|" not in text:
            return None

        lines = [
            x.strip()
            for x in text.strip().split("\n")
            if "|" in x
        ]

        users = []

        for line in lines:

            parts = line.split("|")

            if len(parts) < 4:
                continue

            users.append({
                "user_id": int(parts[0]),
                "name": parts[1],
                "email": parts[2],
                "department": parts[3]
            })

        return users

    except Exception as e:

        print("Resolver error:", e)
        return None


# =========================================================
# HELPERS
# =========================================================

def is_db_query(text):

    text = text.lower()

    return any(
        x in text
        for x in [
            "gtsm-db",
            "readonly",
            "read-only",
            "database",
            " db"
        ]
    )


def is_db_mutation(text):

    text = text.lower()

    mutation_words = [
        "update",
        "delete",
        "remove",
        "create",
        "add",
        "insert",
        "modify",
        "change"
    ]

    return is_db_query(text) and any(
        word in text
        for word in mutation_words
    )


def clean_response(text):

    if not text:
        return ""

    text = re.sub(
        r"\[\{.*?\}\]",
        "",
        str(text),
        flags=re.DOTALL
    )

    lines = []

    for line in text.splitlines():

        lower = line.lower().strip()

        if (
            "i understand" in lower
            or "i will follow" in lower
            or "strictly adhere" in lower
            or "let's" in lower
            or "tool:" in lower
            or "args:" in lower
        ):
            continue

        lines.append(line)

    return "\n".join(lines).strip()


# =========================================================
# MAIN
# =========================================================

async def run_chat():

    load_dotenv()

    cfg = load_config()

    # =====================================================
    # LLM
    # =====================================================

    llm = ChatBedrockConverse(
        model=os.environ["BEDROCK_MODEL_ID"],
        region_name=os.environ["AWS_REGION"],
        temperature=0
    )

    # =====================================================
    # MCP SERVERS
    # =====================================================

    db_cfg = cfg["mcpServers"]["gtsm-db"]
    api_cfg = cfg["mcpServers"]["gtsm-api"]

    db_server = StdioServerParameters(
        command=db_cfg["command"],
        args=db_cfg["args"]
    )

    api_server = StdioServerParameters(
        command=api_cfg["command"],
        args=api_cfg["args"]
    )

    # =====================================================
    # CONNECT
    # =====================================================

    async with stdio_client(db_server) as (db_r, db_w):

        async with stdio_client(api_server) as (api_r, api_w):

            async with ClientSession(db_r, db_w) as db_session:

                async with ClientSession(api_r, api_w) as api_session:

                    await db_session.initialize()
                    await api_session.initialize()

                    print("\nMCP AGENT READY")

                    # =================================================
                    # LOAD TOOLS
                    # =================================================

                    db_tools = await db_session.list_tools()
                    api_tools = await api_session.list_tools()

                    print("\nAVAILABLE TOOLS:\n")

                    for t in db_tools.tools:
                        print("DB :", t.name)

                    for t in api_tools.tools:
                        print("API:", t.name)

                    # =================================================
                    # TOOL MAP
                    # =================================================

                    tool_session_map = {}

                    for t in db_tools.tools:
                        tool_session_map[t.name] = db_session

                    for t in api_tools.tools:
                        tool_session_map[t.name] = api_session

                    # =================================================
                    # BIND TOOLS
                    # =================================================

                    all_tools = []

                    for t in db_tools.tools:
                        all_tools.append(convert_tool(t))

                    for t in api_tools.tools:
                        all_tools.append(convert_tool(t))

                    llm_with_tools = llm.bind_tools(all_tools)

                    # =================================================
                    # SYSTEM PROMPT
                    # =================================================

                    system_prompt = """
You are a strict MCP ITSM assistant.

=================================================
SYSTEMS
=================================================

1. gtsm-db
   - READ ONLY
   - NEVER changes
   - CRUD operations are NOT allowed
   - ONLY ALLOWED:
       db_list_users
       db_list_incidents
       db_search_incidents

2. gtsm-api
   - FULL CRUD system
   - create/update/delete allowed

=================================================
CRITICAL RULES
=================================================

1. ALWAYS execute tools for fresh data
2. NEVER hallucinate updates/deletes
3. NEVER invent tool results
4. NEVER expose raw tool JSON
5. NEVER expose tool calls
6. NEVER expose internal reasoning
7. NEVER reuse memory as database truth
8. ALWAYS trust latest tool output
9. ONLY answer using real tool output

=================================================
ROUTING
=================================================

If user says:
- gtsm-db
- readonly
- database
- db

ONLY use DB tools.

If user says:
- gtsm-api
- api

ONLY use API tools.

If user simply asks users/incidents:
default to API tools.

=================================================
VERY IMPORTANT
=================================================

If user tries to:
- update
- delete
- create
- add
- modify

inside gtsm-db / readonly db:

DO NOT call API tools.
DO NOT simulate update.
DO NOT pretend success.

Instead clearly say:

"gtsm-db is READ ONLY. Create/update/delete operations are not allowed."

=================================================
UPDATE / DELETE FLOW
=================================================

For update/delete by name:

1. api_find_user_by_name
2. extract user_id
3. api_update_user OR api_delete_user

Never stop after step 1.

=================================================
FINAL RESPONSE STYLE
=================================================

Only provide clean final answers.
Never provide tool JSON.
Never provide tool arrays.
"""

                    messages = [
                        SystemMessage(content=system_prompt)
                    ]

                    # =================================================
                    # CHAT LOOP
                    # =================================================

                    while True:

                        user_input = input("\nYou: ").strip()

                        if user_input.lower() in ["exit", "quit"]:
                            print("Goodbye!")
                            return

                        # =============================================
                        # BLOCK READONLY MUTATIONS
                        # =============================================

                        if is_db_mutation(user_input):

                            print(
                                "\nAssistant: gtsm-db is READ ONLY. "
                                "Create/update/delete operations are not allowed."
                            )

                            continue

                        messages.append(
                            HumanMessage(content=user_input)
                        )

                        # =============================================
                        # AGENT LOOP
                        # =============================================

                        while True:

                            response = await llm_with_tools.ainvoke(messages)

                            tool_calls = getattr(
                                response,
                                "tool_calls",
                                []
                            ) or []

                            # =========================================
                            # FINAL ANSWER
                            # =========================================

                            if not tool_calls:

                                final_text = clean_response(
                                    response.content
                                )

                                print("\nAssistant:", final_text)

                                messages.append(response)

                                break

                            # =========================================
                            # STORE AI RESPONSE
                            # =========================================

                            messages.append(response)

                            # =========================================
                            # EXECUTE TOOLS
                            # =========================================

                            for tc in tool_calls:

                                tool_name = tc["name"]

                                tool_args = tc.get("args", {})

                                # =====================================
                                # AUTO RESOLVE UPDATE USER
                                # =====================================

                                if tool_name == "api_update_user":

                                    if "user_id" not in tool_args:

                                        lookup_name = (
                                            tool_args.get("name")
                                            or tool_args.get("old_name")
                                            or tool_args.get("username")
                                        )

                                        if lookup_name:

                                            users = await resolve_user(
                                                api_session,
                                                lookup_name
                                            )

                                            if users:

                                                # multiple matches
                                                if len(users) > 1:

                                                    msg = (
                                                        f'Multiple users found '
                                                        f'for "{lookup_name}":\n'
                                                    )

                                                    for u in users:

                                                        msg += (
                                                            f'- ID {u["user_id"]}: '
                                                            f'{u["name"]} '
                                                            f'({u["email"]}) - '
                                                            f'{u["department"]}\n'
                                                        )

                                                    msg += (
                                                        "\nPlease specify user_id."
                                                    )

                                                    print("\nAssistant:", msg)

                                                    messages.append(
                                                        ToolMessage(
                                                            content=msg,
                                                            tool_call_id=tc["id"]
                                                        )
                                                    )

                                                    continue

                                                tool_args["user_id"] = (
                                                    users[0]["user_id"]
                                                )

                                # =====================================
                                # AUTO RESOLVE DELETE USER
                                # =====================================

                                if tool_name == "api_delete_user":

                                    if "user_id" not in tool_args:

                                        lookup_name = (
                                            tool_args.get("name")
                                        )

                                        if lookup_name:

                                            users = await resolve_user(
                                                api_session,
                                                lookup_name
                                            )

                                            if users:

                                                # multiple matches
                                                if len(users) > 1:

                                                    msg = (
                                                        f'Multiple users found '
                                                        f'for "{lookup_name}":\n'
                                                    )

                                                    for u in users:

                                                        msg += (
                                                            f'- ID {u["user_id"]}: '
                                                            f'{u["name"]} '
                                                            f'({u["email"]}) - '
                                                            f'{u["department"]}\n'
                                                        )

                                                    msg += (
                                                        "\nPlease specify user_id."
                                                    )

                                                    print("\nAssistant:", msg)

                                                    messages.append(
                                                        ToolMessage(
                                                            content=msg,
                                                            tool_call_id=tc["id"]
                                                        )
                                                    )

                                                    continue

                                                tool_args["user_id"] = (
                                                    users[0]["user_id"]
                                                )

                                # =====================================
                                # EXECUTE TOOL
                                # =====================================

                                session = tool_session_map.get(tool_name)

                                if not session:

                                    result_text = (
                                        f"Tool not available: {tool_name}"
                                    )

                                else:

                                    print(f"\nTool: {tool_name}")
                                    print("Args:", tool_args)

                                    try:

                                        result = await session.call_tool(
                                            tool_name,
                                            tool_args
                                        )

                                        result_text = extract_text(result)

                                    except Exception as e:

                                        result_text = (
                                            f"Tool execution failed: {e}"
                                        )

                                print("\nTool Result:")
                                print(result_text)

                                # =====================================
                                # RETURN TOOL RESULT
                                # =====================================

                                messages.append(
                                    ToolMessage(
                                        content=result_text,
                                        tool_call_id=tc["id"]
                                    )
                                )


# =========================================================
# ENTRY
# =========================================================

if __name__ == "__main__":

    asyncio.run(run_chat())