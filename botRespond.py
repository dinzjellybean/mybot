import os
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from fuzzywuzzy import fuzz, process
import csv
import urllib.parse
from botConfig import confidenceLevel
import pandas as pd
import spacy
from spacy.matcher import PhraseMatcher
import random

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

nlp = spacy.load("en_core_web_sm")
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

def load_vacancies(csv_path='data/course_vacancies.csv'):
    try:
        return pd.read_csv(csv_path)
    except Exception as e:
        print(f"Failed to load vacancies data: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error

vacancies_df = load_vacancies('data/course_vacancies.csv')

def add_patterns(df):
   
    # Adding patterns to the matcher directly
    for course in df['Course'].unique():
        matcher.add("COURSE", None, nlp.make_doc(course))  # Add each course as a pattern
    for university in df['University'].unique():
        matcher.add("UNIVERSITY", None, nlp.make_doc(university))

add_patterns(vacancies_df)

def extract_entities_with_spacy(text):
    doc = nlp(text)
    matches = matcher(doc)
    entities = {"university": None, "course": None}
    for match_id, start, end in matches:
        span = doc[start:end]
        if nlp.vocab.strings[match_id] == "COURSE":
            entities["course"] = span.text
        elif nlp.vocab.strings[match_id] == "UNIVERSITY":
            entities["university"] = span.text
    print("Extracted Entities:", entities)
    return entities

# The check_vacancy function remains unchanged

def check_vacancy(university, course):
    """
    Checks if there is a vacancy for a given course at a given university.

    :param university: The name of the university as extracted from the user query.
    :param course: The name of the course as extracted from the user query.
    :return: A string indicating whether there is a vacancy.
    """
    # Ensure the university and course names are matched case-insensitively
    match = vacancies_df[(vacancies_df['University'].str.lower() == university.lower()) &
                        # (vacancies_df['Available'].str.lower() == available.lower()) &
                        # (vacancies_df['Vacancy'].str.lower() == vacancy.lower()) &
                        # (vacancies_df['Vacancies'].str.lower() == vacancies.lower()) &
                         (vacancies_df['Course'].str.lower() == course.lower())]
    if not match.empty:
        return "Yes" if match.iloc[0]['Vacancy'] == "Yes" else "No"
    return "Information not available"

def get_random_response(user_input):
    user_input = user_input.strip().lower()
    print("User Input:", user_input)
    with open('data/chatbot.csv', encoding='utf-8') as csv_file:
        responses = []
        for row in csv.reader(csv_file):
            if row[0].strip().lower() == user_input:
                responses.append(row[1].strip())  # Assuming the second column contains responses
        print("Possible Responses:", responses)
        return random.choice(responses) if responses else None

def getResponse(sendMsg, conversation_history=[]):
    sendMsg = urllib.parse.unquote(sendMsg)

    if sendMsg.lower().startswith("translate"):
        return "Translation functionality is not yet implemented."
    
    # Move entity extraction here
    entities = extract_entities_with_spacy(sendMsg)
    university, course = entities["university"], entities["course"]

    if sendMsg.strip() == "":
        print("No input provided.")
        return "I didn't quite catch that. Could you please specify what you're looking for?"

    if university and course:
        print("Detected university:", university)
        print("Detected course:", course)
        return handle_vacancy_query(university, course)
    
    # Random response handling
    random_response = get_random_response(sendMsg)
    if random_response:
        print("Random response selected:", random_response)
        return random_response
    
    print("No specific response matched.")
    return handle_fallback(sendMsg)

def handle_vacancy_query(university, course):
    vacancy_status = check_vacancy(university, course)
    return f"Yes, there are vacancies for {course} at {university}." if vacancy_status == "Yes" else f"No, there are no vacancies for {course} at {university}."

def handle_fallback(sendMsg):
    tokens = word_tokenize(sendMsg.lower())

    highest_similarity = 0
    best_response = None
    comeBacks = []

    with open('data/chatbot.csv', encoding='utf-8') as g:
        lines = csv.reader(g)
        for line in lines:
            if line and len(line) >= 2:
                userText = line[0]  # Always take the first element as userText
                botReply = line[1]  # Always take the second element as botReply
                
                user_tokens = word_tokenize(userText.lower())
                similarity = fuzz.token_sort_ratio(tokens, user_tokens)
                if similarity >= confidenceLevel:
                    comeBacks.append((similarity, botReply))
                    print("Possible match:", userText)
                    print("Similarity is:", similarity)
    if comeBacks:
        comeBacks.sort(reverse=True)
        _, best_response = comeBacks[0]

    if best_response:
        return best_response

    highest_similarity = 0
    best_response = None
    with open('data/chatbot.csv', encoding='utf-8') as csv_file:
        for user_query, bot_response in csv.reader(csv_file):
            similarity = fuzz.token_sort_ratio(tokens, word_tokenize(user_query.lower()))
            if similarity > highest_similarity and similarity >= confidenceLevel:
                best_response = bot_response
                highest_similarity = similarity
    return best_response if best_response else "I'm not sure how to answer that. Can you ask in a different way?"



if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        print("Bot:", getResponse(user_input, []))
