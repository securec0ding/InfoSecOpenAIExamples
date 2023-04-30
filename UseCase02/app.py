import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import openai
from dotenv import load_dotenv
import os

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app)

df = pd.read_parquet('url_contents_embedded.parquet')
# Read the data from your DataFrame
embeddings = np.stack(df["ada_v2_embedding"].to_numpy())

# Define the function to generate embeddings using the same model as the DataFrame
def generate_embeddings(text, model="text-embedding-ada-002"):
    return openai.Embedding.create(input=[text], model=model)['data'][0]['embedding']

def get_question_embedding(question):
    return generate_embeddings(question)

# Define a function to compute cosine similarity
def get_most_similar_area(embedding, embeddings):
    embedding_array = np.array(embedding).reshape(1, -1)
    similarities = cosine_similarity(embedding_array, embeddings)
    most_similar_index = np.argmax(similarities)
    return df.iloc[most_similar_index]

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/api/generate-text", methods=["POST"])
def generate_text():
    data = request.json
    prompt = data.get("prompt")
    question_embedding = get_question_embedding(prompt)

    # Find the closest area in the DataFrame
    closest_area = get_most_similar_area(question_embedding, embeddings)

    # Send the question and the closest area to the LLM to get an answer
    prompt = f"Answer the following question based on this area of knowledge: {closest_area}\nQuestion: {prompt}"

    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=1000,
        n=1,
        stop=None,
        temperature=0.7,
    )

    answer = response.choices[0].text.strip()
    result = f"Answer: {answer} Closest Area: {closest_area}"

    return jsonify({"response": result})

if __name__ == "__main__":
    app.run(debug=True)