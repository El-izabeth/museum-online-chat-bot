import google.generativeai as genai
from pymongo import MongoClient
from fuzzywuzzy import process
from langchain.vectorstores import Pinecone as LangChainPinecone
from langchain.embeddings import SentenceTransformerEmbeddings
import pinecone
from sentence_transformers import SentenceTransformer

genai.configure(api_key="")
model = genai.GenerativeModel('gemini-1.5-flash')

def get_database():
    CONNECTION_STRING = ""
    client = MongoClient(CONNECTION_STRING)
    return client['museum']

db = get_database()
collection = db['museums']

def init_pinecone():
    PINECONE_API_KEY = "" 
    PINECONE_ENVIRONMENT = "us-east-1-aws"  
    pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
    index_name = "museum-index"
    if index_name not in pinecone.list_indexes():
        pinecone.create_index(index_name, dimension=384)
    return index_name

def create_pinecone_index(documents, index_name):
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = [
        f"{doc['name']} located in {doc['city']} with time slots: {', '.join(doc['time_slots'])}" 
        for doc in documents
    ]
    LangChainPinecone.from_texts(
        texts=texts,
        embedding=SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2"),
        index_name=index_name
    )

def fetch_all_museum_data():
    return list(collection.find())

def classify_intent(user_input):
    prompt = f". Remember that you have to give answer only in one word. It should only be either 'enquiry' or  'payment' . Classify the following user input as either 'enquiry' or 'payment': {user_input}"
    response = model.generate_content(prompt)
    intent = response.text.strip().lower()
    return intent

def extract_details(user_input, detail_type):
    prompt = f"""
    Extract the {detail_type} from the following input: {user_input}.
    For {detail_type}, return only proper names. If the detail type is 'museum name', do not return any general phrases like 'museums in city_name' or 'museum'. 
    If a specific name like 'XYZ Museum' cannot be found, return an empty response.
    For example, if you have a phrase like 'museums in Delhi', the response should be empty.
    """
    response = model.generate_content(prompt)
    extracted_detail = response.text.strip()
    print(extracted_detail)
    if "empty" in extracted_detail: return ""
    return extracted_detail if extracted_detail.lower() != "museum" else ""

def handle_enquiry(user_input):
    index_name = init_pinecone()
    documents = fetch_all_museum_data()
    create_pinecone_index(documents, index_name)

    vectorstore = LangChainPinecone(index_name=index_name, embedding_function=None)
    
    retrieved_docs = vectorstore.similarity_search(user_input, k=5)
    if not retrieved_docs:
        return "Sorry, I couldn't find any relevant information for your query."

    context = "\n".join([doc["text"] for doc in retrieved_docs])

    prompt = f"""
    You are an intelligent chatbot. Based on the context provided, answer the user's question accurately and naturally.
    Context:
    {context}
    
    Question:
    {user_input}
    """
    response = model.generate_content(prompt)
    print(response.text.strip())
    return response.text.strip()

def handle_payment(user_input):
    museum = extract_details(user_input, "museum name")
    date = extract_details(user_input, "date")
    time_slot = extract_details(user_input, "time slot")
    return "Payment"

def chatbot_response(user_input):
    intent = classify_intent(user_input)
    if intent == "enquiry":
        return handle_enquiry(user_input)
    elif intent == "payment":
        return handle_payment(user_input)
    else:
        return "I'm not sure how to handle that request."

# Example Query
# if __name__ == "__main__":
#     user_input = "I want to enquire about booking tickets for the DEF museum in Agra on September 10th at 10:00 AM."
#     response = chatbot_response(user_input)
#     print(response)
