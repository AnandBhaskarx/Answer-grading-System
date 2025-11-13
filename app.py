from flask import Flask, render_template, request
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline

# Initialize Flask app
app = Flask(__name__)

# Load GPT-2 model for text generation using Hugging Face (for feedback)
generator = pipeline('text-generation', model='gpt2')

# Load Sentence-BERT model for comparing answers
model = SentenceTransformer('all-MiniLM-L6-v2')

# Read the ignore words from the static file
def load_ignore_words():
    with open("static/ignore_words.txt", "r") as file:
        ignore_words = file.read().splitlines()
    return set(ignore_words)

IGNORE_WORDS = load_ignore_words()

# Function to generate AI model answer using GPT-2
def generate_ai_model_answer(question):
    result = generator(question, max_length=100, num_return_sequences=1)
    return result[0]['generated_text']

# Function to compare the model answer with the student answer
def compare_answers(model_answer, student_answer):
    emb_ref = model.encode(model_answer, convert_to_tensor=True)
    emb_stu = model.encode(student_answer, convert_to_tensor=True)
    similarity = util.cos_sim(emb_ref, emb_stu).item()
    return similarity

# Function to filter out the ignore words from a given answer
def filter_keywords(answer):
    words = answer.lower().split()
    return [word for word in words if word not in IGNORE_WORDS and len(word) > 1]  # Filter out short words

# Function to generate feedback based on the similarity score
def generate_feedback(model_answer, student_answer, similarity_score):
    feedback = ""
    strengths = []
    weaknesses = []
    feedback_class = ""

    # Fine-tune feedback based on the similarity score
    if similarity_score > 0.8:
        feedback = "Excellent answer, covers all key points."
        feedback_class = "bg-green-100 text-green-600"  # Green for success
        strengths.append("You covered most of the important details well.")
    elif similarity_score > 0.6:
        feedback = "Good answer but missing some key details."
        feedback_class = "bg-yellow-100 text-yellow-600"  # Yellow for moderate
        strengths.append("You explained the core concepts effectively.")
        weaknesses.append("However, consider adding more detailed explanations or examples.")
    else:
        feedback = "The answer is too basic. Consider adding more details."
        feedback_class = "bg-red-100 text-red-600"  # Red for failure
        weaknesses.append("Your answer lacks several key details and important concepts.")

    # Filter out the ignore words
    model_terms = filter_keywords(model_answer)
    student_terms = filter_keywords(student_answer)

    # Formulate feedback based on common terms
    common_terms = set(model_terms).intersection(set(student_terms))
    missing_terms = set(model_terms).difference(set(student_terms))

    # Combine the important common terms into a paragraph-like format
    if common_terms:
        strengths.append(f"You did well by including important terms like: {', '.join(common_terms)}.")

    # Combine missing terms into a readable sentence
    if missing_terms:
        weaknesses.append(f"Your answer missed key terms such as: {', '.join(missing_terms)}. These are essential for a complete response.")

    # Construct final feedback with strengths and weaknesses in HTML format, each on a new line
    final_feedback = f"{feedback}<br><br><strong>Strengths:</strong><br>" + "<br>".join(strengths) if strengths else "No significant strengths noted."
    final_feedback += f"<br><br><strong>Weaknesses:</strong><br>" + "<br>".join(weaknesses) if weaknesses else "No significant weaknesses noted."

    return final_feedback, feedback_class

# Route to handle form and generate answers
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        question = request.form["question"]
        student_answer = request.form["student_answer"]
        input_type = request.form["input_type"]

        # Generate model answer based on input type
        if input_type == "manual":
            model_answer = request.form["model_answer"]
        else:  # AI-generated answer using GPT-2
            model_answer = generate_ai_model_answer(question)

        # Compare the generated model answer with the student's answer
        similarity_score = compare_answers(model_answer, student_answer)

        # Generate feedback based on similarity score
        feedback, feedback_class = generate_feedback(model_answer, student_answer, similarity_score)

        # Calculate the score based on similarity
        score = round(similarity_score * 5, 2)

        return render_template("index.html", score=score, feedback=feedback, model_answer=model_answer, feedback_class=feedback_class)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
