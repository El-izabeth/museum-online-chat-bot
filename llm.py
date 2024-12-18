import google.generativeai as genai
from pymongo import MongoClient
from fuzzywuzzy import process  

genai.configure(api_key="")

model = genai.GenerativeModel('gemini-1.5-flash')

def get_database():
    CONNECTION_STRING = ""
    client = MongoClient(CONNECTION_STRING)
    return client['museum']

db = get_database()
collection = db['museums']

def classify_intent(user_input):
    prompt = f". Remember that you have to give answer only in one word. It should only be either 'enquiry' or  'payment' . Classify the following user input as either 'enquiry' or 'payment': {user_input}"
    response = model.generate_content(prompt)
    intent = response.text.strip().lower()
    return intent

def extract_details(user_input, detail_type):
    prompt = f"Extract the {detail_type} from the following input: {user_input} . Remember that you have to give only the obtained {detail_type}'s value as output, and not any sentence."
    response = model.generate_content(prompt)
    extracted_detail = response.text.strip()
    return extracted_detail

def fetch_museum_details(city=None):
    query = {}
    if city:
        query['city'] = city
    results = collection.find(query)
    museums = [result for result in results]
    return museums

def match_museum_name(user_museum_name, museums):
    museum_names = [museum['name'] for museum in museums]
    closest_match = process.extractOne(user_museum_name, museum_names)
    return closest_match[0] if closest_match else None

def handle_enquiry(user_input):
    city = extract_details(user_input, "city")
    user_museum_name = extract_details(user_input, "museum name")
    print(city, user_museum_name)
    
    museums = fetch_museum_details(city)
    
    if user_museum_name:
        matched_museum_name = match_museum_name(user_museum_name, museums)
        if matched_museum_name:
            matched_museum = next(museum for museum in museums if museum['name'] == matched_museum_name)
            prompt = f'''Here are the details for {matched_museum['name']} museum in {matched_museum['city']}. The available time slots are {matched_museum['time_slots']}. 
                        You have to provide details about this museum with the details provided in the prompt in a natural language like humans speak, so that the user can understand.
                        Also while providing details do not say that you don't have additional details about the museum. Just provide the positive reply with all the details that has been provided to you.'''
            response = model.generate_content(prompt)
        else:
            response = "Sorry, I couldn't find a museum that closely matches your query."
    elif city:
        if museums:
            museum_list = "\n".join([museum['name'] for museum in museums])
            prompt = f"Here are the museums available in {city}: {museum_list}."
            response = model.generate_content(prompt)
        else:
            response = "Sorry, I couldn't find any museums in the city you mentioned."
    else:
        response = "Please provide more details like the museum name or city."
    print(response)
    if type(response)==str:
        return response
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

# if __name__ == "__main__":
#     user_input = "I want to enquire about booking tickets for the DEF museum in Agra on September 10th at 10:00 AM."
#     response = chatbot_response(user_input)
#     print(response)
