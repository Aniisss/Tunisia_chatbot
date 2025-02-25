from rasa_sdk import Action 
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import UserUtteranceReverted
from dotenv import load_dotenv
import asyncio
import aiohttp
import requests
import os
import json
import time
import sys

import logging
from actions.context_history import get_openai_context

# Load the environment variables
load_dotenv(override=True)

# Create a logger instance for debugging 
logger = logging.getLogger(__name__)
stdoutHandler = logging.StreamHandler(stream=sys.stdout)
fileHandler = logging.FileHandler("logs.txt", mode="w")
logger.addHandler(stdoutHandler)
logger.addHandler(fileHandler)

# Definition of the system role to focus on Tunisia
system_role = (
    "You are an AI assistant for a website dedicated to Tunisia, covering its culture, traditions, and tourism. "
    "Your primary role is to generate responses using retrieved augmented generation (RAG) results and any available previous context. "
    "If the retrieved information is irrelevant or does not align with the user's intent, rely on your own knowledge "
    "to provide an informative and accurate response. Maintain an engaging and helpful tone. "
    "Do not mention when RAG results are missing or irrelevant, nor explain how you formulated your response; simply address the user's query naturally."
)


# setup the query engine for future querying
LLAMA_INDEX_API_URL = "http://llama_index_api:8000/query"

#Function to control the query in llamindex to prevent stacking
async def query_rag_with_timeout(user_query, timeout=10):
    start_time = time.time()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                LLAMA_INDEX_API_URL,
                json={"question": user_query},
                headers={"Content-Type": "application/json"},
                timeout=timeout,
            ) as response:
                response.raise_for_status()
                end_time = time.time()  # Record the end time
                elapsed_time = end_time - start_time
                logger.info(f"Time taken is {elapsed_time}")

                data = await response.json()
                return data.get("answer", "No relevant documents found.")
    except asyncio.TimeoutError:
        logger.warning("RAG query timed out.")
        return None
    except Exception as e:
        logger.error(f"RAG query failed: {str(e)}")
        return None

class ActionHandleQuery(Action):
    def name(self) -> str:
        return "action_handle_query"

    async def run(self, dispatcher: CollectingDispatcher, tracker, domain):
        user_query = tracker.latest_message["text"]  # Get the user's query
        try : 

            rag_response = await query_rag_with_timeout( user_query )
            rag_response = rag_response if rag_response else "No relevant documents found."
            logger.info(rag_response)


            # Step 2: get the conversation history
            context = get_openai_context(tracker)
            logger.info(context)

            # Step 4: Combine the RAG response, user query and context for refinement
            messages = [
                {"role": "system", "content": system_role},
                *context,
                {
                    "role": "user",
                    "content": f"User Query: {user_query}\n\nRAG Response: {rag_response}",
                },
            ]

            # Request refinement from OpenAI
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                  "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                  "Content-Type": "application/json",
                },
                data=json.dumps({
                  "model": "meta-llama/llama-3.3-70b-instruct:free", 
                  "messages": messages,
                  "top_p": 1,
                  "temperature": 1,
                  "frequency_penalty": 0,
                  "presence_penalty": 0,
                  "repetition_penalty": 1,
                  "top_k": 0,
                })
            )

            # Extract the refined response
            refined_response = response.json()["choices"][0].get("message").get("content")

            # Send the refined response back to the user
            dispatcher.utter_message(text=refined_response)
            return

        except Exception as e:
            # Handle errors gracefully
            logger.error(f"An error occurred: {str(e)}")
            dispatcher.utter_message(text=f"An error occurred: {str(e)}")