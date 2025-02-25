# Chatbot with Rasa & LlamaIndex - Dockerized

## Overview
This project is a containerized chatbot using **Rasa** and **LlamaIndex**, orchestrated with **Docker Compose**. The chatbot is designed to answer questions about **Tunisia**, its **culture**, **history**, **geography**, and other related topics.

## Prerequisites
Ensure you have the following installed:
- [Docker](https://www.docker.com/)


## Installation & Setup
### 1. Clone the repository
```sh
git clone https://github.com/Aniisss/Tunisia_chatbot.git
cd <your-project-directory>
```

### 2. Configure Environment Variables
Before running the services, create a `.env` file in the project root and add the necessary API key:
```sh
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Build and Start the Services
```sh
docker-compose up --build 
```
This will:
- Build the `rasa_base` image for both Rasa and custom actions.
- Start the Rasa server, Rasa actions, and LlamaIndex API.

### 4. Verify Running Containers
```sh
docker ps
```
You should see the following containers running:
- `rasa_server` (Rasa Core API on port `5005`)
- `rasa_actions` (Rasa actions server on port `5055`)
- `llama_index_api` (LlamaIndex API on port `8000`)

## Usage
### Send Messages to the Chatbot
To communicate with the chatbot, send a POST request to the Rasa server endpoint:

**Endpoint:** `http://0.0.0.0:5005/webhooks/rest/webhook`

**Request Body (JSON):**
```json
{
  "sender": "user1",
  "message": "Hello!"
}
```

**Example using `curl`:**
```sh
curl -X POST http://0.0.0.0:5005/webhooks/rest/webhook \
     -H "Content-Type: application/json" \
     -d '{"sender": "user1", "message": "Hello!"}'
```

### Restart Services
```sh
docker-compose restart
```

## Stopping and Cleaning Up
To stop the containers without removing them:
```sh
docker-compose down
```
To remove all containers, networks, and volumes:
```sh
docker-compose down -v
```

## Debugging
- To check logs for Rasa:
  ```sh
  docker-compose logs rasa
  ```
- To check logs for Actions:
  ```sh
  docker-compose logs actions
  ```
- To check logs for LlamaIndex API:
  ```sh
  docker-compose logs llama_index_api
  ```

---

