from letta_client import Letta

client = Letta(base_url="http://localhost:8283")
# client = Letta(token="LETTA_API_KEY")  # if using Letta Cloud

def print_message(message):
    if message.message_type == "reasoning_message":
        print("🧠 Reasoning: " + message.reasoning)
    elif message.message_type == "assistant_message":
        print("🤖 Agent: " + message.content)
    elif message.message_type == "tool_call_message":
        print("🔧 Tool Call: " + message.tool_call.name + "\n" + message.tool_call.arguments)
    elif message.message_type == "tool_return_message":
        print("🔧 Tool Return: " + message.tool_return)
    elif message.message_type == "user_message":
        print("👤 User Message: " + message.content)


# # creation of agent with memory on the local server (in my case)
agent_state = client.agents.create(
    name="simple_agent",
    memory_blocks=[
        {
          "label": "human",
          "value": "My name is Charles",
          "limit": 10000 # character limit -> by default it is 5000
        },
        {
          "label": "persona",
          "value": "You are a helpful assistant and you always use emojis"
        }
    ],
    model="openai/gpt-4o-mini-2024-07-18",
    embedding="openai/text-embedding-3-small"
)


# send a message to the agent
response = client.agents.messages.create(
    agent_id=agent_state.id,
    messages=[
        {
            "role": "user",
            "content": "hows it going????"
        }
    ]
)

# if we want to print the messages
for message in response.messages:
    print_message(message)

# if we want to print the usage stats like token count etc
print(response.usage.completion_tokens)
print(response.usage.prompt_tokens)
print(response.usage.step_count)

# what is the agent state -> system prompt of the agent
print(agent_state.system)

print([t.name for t in agent_state.tools]) # list of tools that are present in the agent
# note we can customize the tools in the agent creation according to our needs

print(agent_state.memory)

# print all the archival memory blocks -> archival_memory this the updated name
passages = client.agents.archival_memory.list(
    agent_id=agent_state.id,
)
print(passages)


# send a message to the agent
response = client.agents.messages.create(
    agent_id=agent_state.id,
    messages=[
        {
            "role": "user",
            "content": "my name actually Sarah."
        }
    ]
)

# # if we want to print the messages
for message in response.messages:
    print_message(message)


print(response.usage.completion_tokens)
print(response.usage.prompt_tokens)
print(response.usage.step_count)

client.agents.blocks.retrieve(
    agent_id=agent_state.id,
    block_label="human"
).value

response = client.agents.messages.create(
    agent_id=agent_state.id,
    messages=[
        {
            "role": "user",
            "content": "Save the information that 'bob loves cats' to archival"
        }
    ]
)

passages = client.agents.archival_memory.list(
    agent_id=agent_state.id,
)

print([passage.text for passage in passages])

# send a message to the agent
response = client.agents.messages.create(
    agent_id=agent_state.id,
    messages=[
        {
            "role": "user",
            "content": "What animals do I like? Search archival."
        }
    ]
)

for message in response.messages:
    print_message(message)