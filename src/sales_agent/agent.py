import os
from openai import OpenAI
from dotenv import load_dotenv
import json
from tools import query_sales, get_schema

load_dotenv()
client = OpenAI()

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_sales",
            "description": (
                "Run a read-only SQL query against the sales database (SQLite) and "
                "return the results as JSON with columns, rows, and a truncated flag. "
                "Only SELECT statements are allowed. Results are capped at 50 rows, "
                "so prefer aggregate queries (COUNT, SUM, AVG with GROUP BY) over "
                "selecting raw rows."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "A single SQLite SELECT statement.",
                    },
                },
                "required": ["sql"],
            },
        },
    },
     {
        "type": "function",
        "function": {
            "name": "get_schema",
            "description": (
                "Call it before writing SQL"
            ),
            "parameters": {
                "type": "object",
                "properties":{}
            }
        },
    },
]









def run_agent(question, messages):
    messages.append({"role": "user", "content": question})
    for number in range(5):
        response =  client.chat.completions.create(model=os.environ["MODEL"], messages=messages, tools=TOOLS)
        message = response.choices[0].message 
        messages.append(message)
        if(response.choices[0].finish_reason == 'stop'):
            # readable = [m if isinstance(m, dict) else m.model_dump(exclude_none=True) for m in messages]
            # print('out')
            # print(json.dumps(readable, indent=2))
            return message.content

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            print(f"-> {name} {args}")
            if name == "query_sales":
                result = query_sales(args["sql"])
            elif name == "get_schema":
                result = get_schema()
            else:
                result = f"Unknown tool: {name}"

            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result,})
    else:
        return "Gave up after 5 rounds"
    




if __name__ == "__main__":
    messages = []
    while True:
        question = input("You: ")
        if question == "quit":
            break
        print(run_agent(question, messages))
    # response = client.chat.completions.create(model=os.environ["MODEL"], messages=messages, tools=TOOLS)
    # print('finish_reason', response.choices[0].finish_reason)
    # print('message', response.choices[0].message)
    # print('toolcalls',response.choices[0].message.tool_calls)
    # print('toolcalls.function.name',response.choices[0].message.tool_calls[0].function.name)
    # print('toolcalls.function.arguments',response.choices[0].message.tool_calls[0].function.arguments)
    # print('type of arguments', type(response.choices[0].message.tool_calls[0].function.arguments))
    # sql = json.loads(response.choices[0].message.tool_calls[0].function.arguments)['sql']
    # print('sql', sql)
    # result = query_sales(sql)
    # print('result', result)


    # response = client.chat.completions.create(model=os.environ["MODEL"], messages=messages, tools=TOOLS)
    # sql = json.loads(response.choices[0].message.tool_calls[0].function.arguments)['sql']
    # result = query_sales(sql)
    # messages.append(response.choices[0].message)
    # messages.append({"role": "user", "tool_call_id": response.choices[0].message.tool_calls[0].id, "content": result })




   


    # response = client.chat.completions.create(model=os.environ["MODEL"], messages=messages, tools=TOOLS)
    # print('finish_reason2', response.choices[0].finish_reason)
    # print('message2', response.choices[0].message)
    