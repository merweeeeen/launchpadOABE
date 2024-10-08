from uuid import uuid4

import httpx
from dotenv import load_dotenv
from fastapi import status

from app.common.schema import ConversationFull, Description, PromptPayload
from app.queries.main import send_prompt

load_dotenv()


async def start_conversation(payload):
    # tentatively 'name' of conversation would be the initial prompt
    name = payload.query
    conversation_id = uuid4()
    full_conversation = ConversationFull(
        id=conversation_id,
        name=name,
        tokens=0,
        params=Description(description=None),
        messages=[],
    )
    await full_conversation.insert()
    prompt = PromptPayload(role="user", content=payload.query, exist=False).model_dump()
    async with httpx.AsyncClient(follow_redirects=True) as client:
        await client.post(
            f"http://localhost:3000/queries/{full_conversation.id}",
            json=prompt,
            timeout=15.0,
        )

    final_output = await ConversationFull.find_one(
        ConversationFull.id == conversation_id
    )

    return final_output


async def existing_conversation(payload):
    prompt = PromptPayload(role="user", content=payload.query, exist=True).model_dump()

    async with httpx.AsyncClient() as client:
        await client.post(
            f"http://localhost:3000/queries/{payload.id}", json=prompt, timeout=15.0
        )

    final_output = await ConversationFull.find_one(ConversationFull.id == payload.id)
    return final_output


async def get_all_conversations():
    retrieved_conversations = []
    for conversation in await ConversationFull.find().to_list():
        conversation = conversation.model_dump()
        del conversation["messages"]
        retrieved_conversations.append(conversation)
    return retrieved_conversations


async def get_a_conversation(id):
    return await ConversationFull.find_one(ConversationFull.id == id)


async def update_a_conversation(id, payload):
    conversation = await ConversationFull.find_one(ConversationFull.id == id)
    if name := payload.name:
        await conversation.set({ConversationFull.name: name})
    if params := payload.params:
        await conversation.set({ConversationFull.params: params})
    return status.HTTP_204_NO_CONTENT


async def delete_a_conversation(id):
    conversation = await ConversationFull.find_one(ConversationFull.id == id)
    await conversation.delete()
