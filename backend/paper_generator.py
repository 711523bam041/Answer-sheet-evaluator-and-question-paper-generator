import os
import json
import requests
import random
import re
import logging
from io import BytesIO
from fpdf import FPDF

log = logging.getLogger(__name__)

# Predefined high-quality questions for common subjects/topics to provide premium local fallback
PREDEFINED_BANK = {
    "machine learning": {
        "topics": ["neural networks", "regression", "supervised learning", "unsupervised learning", "classification", "clustering", "overfitting"],
        "questions": [
            {
                "marks": 1,
                "type": "MCQ",
                "question": "Which of the following activation functions is commonly used in the output layer of a binary classification neural network?",
                "options": ["ReLU", "Sigmoid", "Tanh", "Softmax"],
                "answer": "Sigmoid",
                "bloom_taxonomy": "Remembering"
            },
            {
                "marks": 1,
                "type": "MCQ",
                "question": "What is the primary goal of regularization in machine learning?",
                "options": ["Increase training accuracy", "Decrease training time", "Prevent overfitting", "Feature scaling"],
                "answer": "Prevent overfitting",
                "bloom_taxonomy": "Understanding"
            },
            {
                "marks": 1,
                "type": "True/False",
                "question": "True or False: K-Means clustering is an example of supervised learning.",
                "options": ["True", "False"],
                "answer": "False",
                "bloom_taxonomy": "Remembering"
            },
            {
                "marks": 1,
                "type": "Fill in the blanks",
                "question": "The process of scaling features so they have a mean of 0 and standard deviation of 1 is called _______.",
                "options": [],
                "answer": "Standardization / Z-score normalization",
                "bloom_taxonomy": "Remembering"
            },
            {
                "marks": 2,
                "type": "Short Answer",
                "question": "Explain the difference between L1 (Lasso) and L2 (Ridge) regularization.",
                "options": [],
                "answer": "L1 regularization adds absolute value of coefficients as penalty term and can lead to sparse outputs (feature selection), while L2 adds squared magnitude of coefficients and shrinks them close to zero but not exactly zero.",
                "bloom_taxonomy": "Understanding"
            },
            {
                "marks": 2,
                "type": "Short Answer",
                "question": "What is overfitting, and how can it be detected using validation datasets?",
                "options": [],
                "answer": "Overfitting occurs when a model learns noise in training data. It is detected when training error continues to decrease but validation error starts to increase.",
                "bloom_taxonomy": "Understanding"
            },
            {
                "marks": 5,
                "type": "Brief Answer",
                "question": "Describe the Backpropagation algorithm used in neural networks. Explain the mathematical basis (Chain Rule) briefly.",
                "options": [],
                "answer": "Backpropagation computes the gradient of the loss function with respect to weights using the Chain Rule of calculus. It propagates errors backward from output layer to input layer to update weights via gradient descent.",
                "bloom_taxonomy": "Applying"
            },
            {
                "marks": 5,
                "type": "Brief Answer",
                "question": "Compare and contrast Supervised and Unsupervised learning with examples of algorithms for each.",
                "options": [],
                "answer": "Supervised learning uses labeled training data (e.g., Linear Regression, SVM) to map inputs to outputs. Unsupervised learning finds hidden patterns in unlabeled data (e.g., K-Means, PCA).",
                "bloom_taxonomy": "Analyzing"
            },
            {
                "marks": 10,
                "type": "Descriptive Answer",
                "question": "Discuss the Bias-Variance Tradeoff in detail. Explain how model complexity affects bias and variance, draw a qualitative plot, and explain strategies to optimize this trade-off.",
                "options": [],
                "answer": "Bias is error from erroneous assumptions (underfitting). Variance is error from sensitivity to small fluctuations in training set (overfitting). High complexity = Low Bias, High Variance. Low complexity = High Bias, Low Variance. Optimization strategies include cross-validation, regularization, and ensemble methods.",
                "bloom_taxonomy": "Evaluating"
            },
            {
                "marks": 13,
                "type": "Case Study Questions",
                "question": "You are hired by a medical diagnostic institute to build a classifier that identifies a rare but critical disease from clinical test reports. The dataset has 99.9% negative classes and only 0.1% positive classes. Explain in detail: (a) Why standard accuracy is a bad metric. (b) What metrics you would use (Precision, Recall, F1, AUC-ROC) and why. (c) What strategies (undersampling, oversampling, SMOTE, class weights) you would implement to tackle class imbalance.",
                "options": [],
                "answer": "(a) Accuracy is misleading because a dumb model predicting negative for all cases achieves 99.9% accuracy but fails to detect the disease. (b) Recall is critical since false negatives mean untreated patients. F1-score balances precision and recall. (c) SMOTE creates synthetic minority samples. Class weights penalize minority class errors higher.",
                "bloom_taxonomy": "Creating"
            }
        ]
    },
    "data structures": {
        "topics": ["arrays", "linked lists", "trees", "graphs", "sorting", "searching", "hash tables", "stacks", "queues"],
        "questions": [
            {
                "marks": 1,
                "type": "MCQ",
                "question": "What is the worst-case time complexity of searching for an element in a binary search tree (BST)?",
                "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
                "answer": "O(n)",
                "bloom_taxonomy": "Remembering"
            },
            {
                "marks": 1,
                "type": "True/False",
                "question": "True or False: A queue operates on a Last-In, First-Out (LIFO) basis.",
                "options": ["True", "False"],
                "answer": "False",
                "bloom_taxonomy": "Remembering"
            },
            {
                "marks": 1,
                "type": "Fill in the blanks",
                "question": "The data structure used internally to implement function calls and recursion is the _______.",
                "options": [],
                "answer": "Stack",
                "bloom_taxonomy": "Remembering"
            },
            {
                "marks": 2,
                "type": "Short Answer",
                "question": "Explain the difference between a singly linked list and a doubly linked list.",
                "options": [],
                "answer": "A singly linked list node contains data and a pointer to the next node. A doubly linked list node also contains a pointer to the previous node, allowing bidirectional traversal.",
                "bloom_taxonomy": "Understanding"
            },
            {
                "marks": 5,
                "type": "Brief Answer",
                "question": "Explain the working of Hash Collisions and how they are resolved using Chaining versus Open Addressing.",
                "options": [],
                "answer": "Collisions occur when different keys hash to the same index. Chaining stores colliding elements in a linked list at that index. Open addressing finds another open slot in the hash table using probing (linear, quadratic, or double hashing).",
                "bloom_taxonomy": "Analyzing"
            },
            {
                "marks": 10,
                "type": "Descriptive Answer",
                "question": "Detail the QuickSort algorithm. Write the pseudo-code for the partition step, trace it with an example array [12, 7, 14, 9, 10, 11], and discuss its best, average, and worst-case time complexities.",
                "options": [],
                "answer": "QuickSort is a divide-and-conquer algorithm. It picks a pivot, partitions the array around the pivot, and recursively sorts sub-arrays. Partition pseudo-code: rearrange elements < pivot to the left, > pivot to the right. Worst case O(n^2) when array is already sorted, best/average O(n log n).",
                "bloom_taxonomy": "Applying"
            },
            {
                "marks": 13,
                "type": "Case Study Questions",
                "question": "Design a package routing system for a large logistics firm. The system must find the shortest delivery path between multiple cities (nodes) with varying travel times (weighted edges). Explain: (a) Which graph algorithm is most suitable (Dijkstra's vs Bellman-Ford vs Floyd-Warshall) and why. (b) The exact data structures needed to optimize search speed (e.g. Min-Priority Queue). (c) How you would handle dynamic additions of new roadblocks (weight updates) in real-time.",
                "options": [],
                "answer": "(a) Dijkstra's is best for single-source shortest path with non-negative weights due to efficiency O((V+E)log V). (b) Min-heap priority queue enables fast extraction of min distance. (c) Dynamic graph algorithms or re-running Dijkstra's on sub-grids can handle roadblocks.",
                "bloom_taxonomy": "Creating"
            }
        ]
    }
}

# General templates for any custom subject/topics
TEMPLATE_BANK = {
    1: {
        "MCQ": [
            "Which of the following is a primary feature or characteristic of {topic}?",
            "What is the main purpose of utilizing {topic} in modern systems?",
            "In the context of {subject}, which of the following is directly related to {topic}?",
            "Identify the correct statement regarding {topic} from the options below."
        ],
        "True/False": [
            "True or False: {topic} plays a key role in optimizing processes within {subject}.",
            "True or False: The implementation of {topic} is entirely independent of other components of {subject}.",
            "True or False: {topic} is widely recognized as a standard practice for basic operations in this domain."
        ],
        "Fill in the blanks": [
            "In the context of {subject}, {topic} is defined as a mechanism to _______.",
            "The primary parameter configured when working with {topic} is _______.",
            "_______ is a critical requirement for successfully deploying {topic}."
        ]
    },
    2: {
        "Short Answer": [
            "Define {topic} and list its two main components or attributes.",
            "Why is {topic} considered essential in the study of {subject}?",
            "Briefly explain one major challenge associated with {topic}.",
            "Give a real-world example where {topic} is applied."
        ]
    },
    5: {
        "Brief Answer": [
            "Explain the operational workflow or process flow of {topic} in detail.",
            "Compare {topic} with other alternative methodologies in {subject}. What are its advantages?",
            "Analyze the impact of changing key parameters on the overall performance of {topic}.",
            "Describe the underlying principles that govern the behavior of {topic}."
        ]
    },
    10: {
        "Descriptive Answer": [
            "Provide a comprehensive overview of {topic}. Draw a block diagram showing its architecture, explain each component, and discuss its practical limitations.",
            "Discuss the integration of {topic} with overall systems in {subject}. What are the design trade-offs, configuration options, and performance bottlenecks?",
            "Critically analyze the evolution of {topic}. How has it solved traditional problems in {subject}, and what are the current research frontiers in its implementation?"
        ]
    },
    13: {
        "Descriptive Answer": [
            "Provide a comprehensive, end-to-end design specification for a system utilizing {topic}. Detail the architecture, the algorithmic steps, data flow diagrams, and error handling mechanisms. Support your design with a concrete scenario.",
            "Elaborate on how {topic} handles high-load, complex operational environments. What are the scaling architectures, failover mechanisms, and mathematical/logical proofs validating its stability?"
        ],
        "Case Study Questions": [
            "Case Study: A large enterprise plans to upgrade its legacy infrastructure in {subject} by adopting {topic}. However, they face budget constraints, legacy compatibility issues, and a lack of skilled personnel. (a) Formulate a step-by-step migration blueprint. (b) Identify three critical risk factors and propose mitigation strategies. (c) Establish key performance indicators (KPIs) to measure the success of the {topic} implementation.",
            "Case Study: During the deployment of {topic} at a high-transaction facility, engineers observed a sudden drop in throughput and resource exhaustion. (a) Map out a diagnostic workflow to locate the root cause. (b) Explain how you would optimize the configuration of {topic} to resolve these issues. (c) Propose a preventive maintenance system using {subject} guidelines."
        ]
    }
}

TEMPLATE_ANSWERS = {
    "MCQ": {
        "options": ["Option A (Primary standard choice)", "Option B (Secondary alternative)", "Option C (Inefficient constraint)", "Option D (None of the above)"],
        "answer": "Option A (Primary standard choice)"
    },
    "True/False": {
        "options": ["True", "False"],
        "answer": "True"
    },
    "Fill in the blanks": {
        "options": [],
        "answer": "Key industry-standard term"
    },
    "Short Answer": {
        "options": [],
        "answer": "Requires explanation of definition, components, and primary application."
    },
    "Brief Answer": {
        "options": [],
        "answer": "Requires step-by-step workflow explanation, comparative analysis, and parameter trade-offs."
    },
    "Descriptive Answer": {
        "options": [],
        "answer": "Requires architecture diagrams, comprehensive operational trade-offs, scaling limits, and full integration details."
    },
    "Case Study Questions": {
        "options": [],
        "answer": "Detailed case solution addressing migration planning, risk factors, KPIs, diagnostics, and system optimization rules."
    }
}

BLOOM_TAXONOMY_MAP = {
    1: ["Remembering", "Understanding"],
    2: ["Understanding", "Applying"],
    5: ["Applying", "Analyzing"],
    10: ["Analyzing", "Evaluating"],
    13: ["Evaluating", "Creating"]
}

def clean_pdf_text(text):
    """Clean text for FPDF compatibility to prevent encoding crashes."""
    if not text:
        return ""
    replacements = {
        '\u201c': '"', '\u201d': '"',
        '\u2018': "'", '\u2019': "'",
        '\u2013': '-', '\u2014': '-',
        '\u2022': '*',
        '\u03b1': 'alpha', '\u03b2': 'beta', '\u03b3': 'gamma',
        '\u2212': '-', '\u2265': '>=', '\u2264': '<='
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)
    return text.encode('latin-1', 'replace').decode('latin-1')

class ExamPDF(FPDF):
    def __init__(self, subject_name, duration, total_marks, difficulty, is_answer_key=False):
        super().__init__()
        self.subject_name = subject_name
        self.duration = duration
        self.total_marks = total_marks
        self.difficulty = difficulty
        self.is_answer_key = is_answer_key

    def header(self):
        # Header block
        self.set_font("Helvetica", "B", 14)
        title = "ANSWER KEY & EVALUATION MANUAL" if self.is_answer_key else "INSTITUTION SEMESTER EXAMINATION"
        self.cell(0, 8, clean_pdf_text(title), ln=True, align="C")
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 6, clean_pdf_text(f"SUBJECT: {self.subject_name.upper()}"), ln=True, align="C")
        
        # Metadata block
        self.ln(2)
        self.set_font("Helvetica", "", 10)
        self.cell(50, 6, clean_pdf_text(f"Duration: {self.duration}"), border=0)
        self.cell(90, 6, clean_pdf_text(f"Difficulty: {self.difficulty}"), border=0, align="C")
        self.cell(50, 6, clean_pdf_text(f"Max Marks: {self.total_marks}"), border=0, align="R", ln=True)
        
        # Horizontal divider line
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        tag = "Grading Rubric Manual" if self.is_answer_key else "Exam Question Sheet"
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} | {tag}", align="C")

def ensure_answer_key_details(q, subject, topic):
    """
    Enforces a structured answer key schema containing model answers, marking schemes,
    keywords, expected concepts, and ideal lengths. Fills in fallback data dynamically if missing.
    """
    marks = q.get("marks", 1)
    q_type = q.get("type", "Short Answer")
    q_text = q.get("question", "")
    ans_text = q.get("answer", "Answer details here")

    # If details already exist, validate and complement them
    details = q.get("answer_key_details", {})
    if not isinstance(details, dict):
        details = {}

    # 1. Model Answer
    if "model_answer" not in details or not details["model_answer"]:
        details["model_answer"] = ans_text

    # 2. Keywords
    if "keywords" not in details or not details["keywords"]:
        # Pick relevant uppercase terms from question
        words = [w.strip("?,.()").capitalize() for w in q_text.split() 
                 if len(w) > 4 and w.lower() not in ["which", "what", "explain", "describe", "discuss", "following", "primary", "second", "example", "detail"]]
        details["keywords"] = list(set([topic.capitalize()] + words[:4]))[:5]

    # 3. Expected Concepts
    if "expected_concepts" not in details or not details["expected_concepts"]:
        details["expected_concepts"] = [
            f"Introduce the foundational aspects of {topic}",
            f"Analyze parameter variables and implementation constraints in {subject}"
        ]

    # 4. Ideal Length
    if "ideal_length" not in details or not details["ideal_length"]:
        if marks == 1:
            details["ideal_length"] = "Single option / word selection"
        elif marks == 2:
            details["ideal_length"] = "30-50 words (2-3 sentences)"
        elif marks == 5:
            details["ideal_length"] = "100-150 words (1-2 paragraphs)"
        elif marks == 10:
            details["ideal_length"] = "250-350 words (1-1.5 pages)"
        else:
            details["ideal_length"] = "400-500 words (2 pages)"

    # 5. Marking Scheme
    if "marking_scheme" not in details or not details["marking_scheme"]:
        if marks == 1:
            details["marking_scheme"] = [{"criteria": "Select/state correct answer", "marks": 1.0}]
        elif marks == 2:
            details["marking_scheme"] = [
                {"criteria": "Correct definition or direct explanation", "marks": 1.0},
                {"criteria": "Accompanying basic examples or list components", "marks": 1.0}
            ]
        elif marks == 5:
            details["marking_scheme"] = [
                {"criteria": f"Definition and introductory concepts of {topic}", "marks": 1.0},
                {"criteria": "Explanation of core process / operational steps", "marks": 2.0},
                {"criteria": "Analysis of benefits and practical examples", "marks": 2.0}
            ]
        elif marks == 10:
            details["marking_scheme"] = [
                {"criteria": f"Architectural schema or block diagram of {topic}", "marks": 3.0},
                {"criteria": "Detailed conceptual discussion of components", "marks": 4.0},
                {"criteria": "Critical trade-off analysis and practical limitations", "marks": 3.0}
            ]
        else:  # 13 marks
            details["marking_scheme"] = [
                {"criteria": "Migration blueprint / Scenario mapping analysis", "marks": 4.0},
                {"criteria": "Comprehensive risk identification & mitigation plan", "marks": 4.0},
                {"criteria": "KPI metric parameters and architectural optimization checklist", "marks": 5.0}
            ]

    q["answer_key_details"] = details
    return q

def generate_local_paper(subject, topics, syllabus, difficulty, duration, total_marks, distribution):
    """
    Intelligent rules-based fallback generator when Gemini API is unavailable.
    """
    log.info(f"Generating local fallback question paper for subject: {subject}")
    
    topics_clean = [t.strip() for t in topics.replace('\n', ',').split(',') if t.strip()]
    if not topics_clean:
        topics_clean = [subject]
        
    questions = []
    
    # Check if we have predefined database for this subject
    subject_lower = subject.lower().strip()
    matching_bank = None
    for k in PREDEFINED_BANK:
        if k in subject_lower:
            matching_bank = PREDEFINED_BANK[k]
            break
            
    question_counter = 1
    for marks_str, count in distribution.items():
        marks = int(marks_str)
        count = int(count)
        if count <= 0:
            continue
            
        # Select possible question types for this mark value
        if marks == 1:
            q_types = ["MCQ", "Fill in the blanks", "True/False"]
        elif marks == 2:
            q_types = ["Short Answer"]
        elif marks == 5:
            q_types = ["Brief Answer", "Short Answer"]
        elif marks == 10:
            q_types = ["Descriptive Answer"]
        else:  # 13 marks
            q_types = ["Case Study Questions", "Descriptive Answer"]
            
        for _ in range(count):
            q_type = random.choice(q_types)
            topic = random.choice(topics_clean)
            bloom = random.choice(BLOOM_TAXONOMY_MAP.get(marks, ["Understanding"]))
            
            question_obj = None
            
            # 1. Try predefined database match
            if matching_bank:
                available_q = [
                    q for q in matching_bank["questions"]
                    if q["marks"] == marks and q["type"] == q_type and q not in questions
                ]
                if not available_q:
                    available_q = [
                        q for q in matching_bank["questions"]
                        if q["marks"] == marks and q not in questions
                    ]
                if available_q:
                    question_obj = random.choice(available_q).copy()
                    
            # 2. Dynamic generation using templates
            if not question_obj:
                templates = TEMPLATE_BANK.get(marks, {}).get(q_type, [])
                if not templates:
                    all_q_types = TEMPLATE_BANK.get(marks, {})
                    if all_q_types:
                        q_type = list(all_q_types.keys())[0]
                        templates = all_q_types[q_type]
                    else:
                        templates = ["Discuss key concepts of {topic} in the context of {subject}."]
                        q_type = "Descriptive Answer"
                        
                template = random.choice(templates)
                question_text = template.format(topic=topic, subject=subject)
                
                ans_data = TEMPLATE_ANSWERS.get(q_type, {"options": [], "answer": "Answer details here"})
                
                options = ans_data.get("options", [])
                if q_type == "MCQ":
                    options = [
                        f"Optimal {topic} application",
                        f"Inefficient {topic} variant",
                        f"Alternative parameter in {subject}",
                        f"Incompatible choice for {topic}"
                    ]
                    random.shuffle(options)
                    answer = options[0]
                else:
                    options = []
                    answer = ans_data.get("answer", "Answer details here")
                    
                question_obj = {
                    "marks": marks,
                    "type": q_type,
                    "question": question_text,
                    "options": options,
                    "answer": answer,
                    "bloom_taxonomy": bloom
                }
            
            # Formulate structured answer keys
            question_obj = ensure_answer_key_details(question_obj, subject, topic)
            questions.append(question_obj)
            question_counter += 1
            
    return {"questions": questions}

def generate_paper(subject, topics, syllabus, difficulty, duration, total_marks, distribution):
    """
    Main entrypoint for paper generation. Attempts Gemini API first, falls back to local rules-based if fails/no key.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        log.info("No GEMINI_API_KEY found. Using local fallback generator.")
        return generate_local_paper(subject, topics, syllabus, difficulty, duration, total_marks, distribution)
        
    try:
        log.info("Attempting Gemini API question paper generation with detailed answer keys...")
        
        dist_details = []
        for marks, count in distribution.items():
            if int(count) > 0:
                dist_details.append(f"- {count} questions of {marks} marks each")
        dist_str = "\n".join(dist_details)
        
        prompt = f"""
You are an expert academic professor. Generate a high-quality question paper for the following subject:
Subject: {subject}
Topics: {topics}
Syllabus: {syllabus}
Difficulty Level: {difficulty} (Easy / Medium / Hard)
Exam Duration: {duration}
Total Marks: {total_marks}

Generate exactly the following question distribution:
{dist_str}

Ensure the questions correspond to Bloom's Taxonomy levels (Remembering, Understanding, Applying, Analyzing, Evaluating, Creating) appropriately distributed based on difficulty ({difficulty}).
Easy papers should have more Remembering/Understanding questions.
Medium papers should have more Applying/Analyzing questions.
Hard papers should have more Evaluating/Creating/Case Study questions.

Support all standard mark categories (1, 2, 5, 10, 13) and question types (MCQ, Fill in the blanks, True/False, Short Answer, Brief Answer, Descriptive Answer, Case Study Questions) as requested.

You must output a JSON object with a single top-level key "questions" containing an array of questions.
Each question object must contain:
1. "marks": integer (e.g., 1, 2, 5, 10, 13)
2. "type": string (must be one of: "MCQ", "Fill in the blanks", "True/False", "Short Answer", "Brief Answer", "Descriptive Answer", "Case Study Questions")
3. "question": string (the actual question text)
4. "options": array of strings (ONLY for "MCQ", must have exactly 4 items, null or empty array for other types)
5. "answer": string (a concise answer key or explanation for this question)
6. "bloom_taxonomy": string (one of: "Remembering", "Understanding", "Applying", "Analyzing", "Evaluating", "Creating")
7. "answer_key_details": object containing:
   - "model_answer": string (a comprehensive model answer or explanation for this question)
   - "marking_scheme": array of objects (each object has "criteria" (string) and "marks" (number) representing a step-by-step mark distribution. Sum of marks in criteria must match this question's marks value)
   - "keywords": array of strings (list of 3-10 essential keywords or terms related to this question)
   - "expected_concepts": array of strings (list of core conceptual areas the student must explain)
   - "ideal_length": string (recommended answer length, e.g. "150-200 words", "Single option", etc.)

Double check that the sum of marks of all generated questions matches exactly {total_marks} marks, and the count of questions for each mark value matches exactly the requested distribution. Do not output any formatting wrappers like markdown code blocks. Just output raw, valid JSON.
"""

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        
        if response.status_code == 200:
            res_json = response.json()
            text_content = res_json['candidates'][0]['content']['parts'][0]['text']
            
            content_clean = re.sub(r'^```json\s*', '', text_content, flags=re.MULTILINE)
            content_clean = re.sub(r'```$', '', content_clean, flags=re.MULTILINE).strip()
            
            data = json.loads(content_clean)
            
            if "questions" in data and isinstance(data["questions"], list):
                # Clean and populate any missing properties
                topics_list = [t.strip() for t in topics.split(",") if t.strip()]
                main_topic = topics_list[0] if topics_list else subject
                
                for q in data["questions"]:
                    ensure_answer_key_details(q, subject, main_topic)
                    
                actual_sum = sum(int(q.get("marks", 0)) for q in data["questions"])
                if actual_sum != int(total_marks):
                    log.warning(f"Gemini output marks sum ({actual_sum}) mismatch with requested ({total_marks}).")
                return data
            else:
                raise ValueError("Invalid JSON structure returned by Gemini")
        else:
            log.error(f"Gemini API returned status code {response.status_code}: {response.text}")
            raise RuntimeError("Gemini API call failed")
            
    except Exception as e:
        log.error(f"Gemini generation error: {str(e)}. Falling back to local rules-based generator.")
        return generate_local_paper(subject, topics, syllabus, difficulty, duration, total_marks, distribution)

def generate_paper_pdf(paper_dict, include_answers=False):
    """
    Generate professional printable PDF for a question paper.
    If include_answers is True, appends the full answer key manual at the end.
    """
    subject = paper_dict.get("subject_name", "Exam")
    duration = paper_dict.get("duration", "3 Hours")
    total_marks = paper_dict.get("total_marks", 100)
    difficulty = paper_dict.get("difficulty", "Medium")
    questions = paper_dict.get("paper_content", {}).get("questions", [])

    # Step 1: Create Question Paper Pages
    pdf = ExamPDF(subject, duration, total_marks, difficulty, is_answer_key=False)
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Instructions Section
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "GENERAL INSTRUCTIONS:", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "1. Read all questions carefully before answering.", ln=True)
    pdf.cell(0, 5, "2. Underline/highlight keywords and draw neat diagrams where appropriate.", ln=True)
    pdf.cell(0, 5, "3. Answer all parts of a question sequentially.", ln=True)
    pdf.ln(5)
    
    # Group questions by mark value
    from collections import defaultdict
    grouped = defaultdict(list)
    for q in questions:
        grouped[int(q.get("marks", 0))].append(q)
        
    sorted_marks = sorted(grouped.keys())
    
    part_labels = ["PART A", "PART B", "PART C", "PART D", "PART E", "PART F"]
    
    question_num = 1
    for idx, mark in enumerate(sorted_marks):
        part_name = part_labels[idx] if idx < len(part_labels) else f"PART {idx + 1}"
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 8, clean_pdf_text(f"{part_name} - ({mark} Mark Questions)"), ln=True, fill=True)
        pdf.ln(3)
        
        for q in grouped[mark]:
            q_type = q.get("type", "General")
            q_text = q.get("question", "")
            bloom = q.get("bloom_taxonomy", "Understanding")
            
            # Print question number and metadata
            header_str = f"Q{question_num}. [{bloom}] ({q_type})"
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(150, 5, clean_pdf_text(header_str))
            
            # Align marks to the right margin
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(40, 5, clean_pdf_text(f"[{mark} Mark]"), ln=True, align="R")
            
            # Print actual question content
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 5, clean_pdf_text(q_text))
            
            # If MCQ, print options
            options = q.get("options", [])
            if options and q_type == "MCQ":
                letters = ["A", "B", "C", "D"]
                pdf.ln(1)
                for opt_idx, opt in enumerate(options):
                    letter = letters[opt_idx] if opt_idx < len(letters) else str(opt_idx + 1)
                    pdf.cell(10) # Indent
                    pdf.cell(0, 5, clean_pdf_text(f"({letter}) {opt}"), ln=True)
            
            pdf.ln(4)
            question_num += 1

    # Step 2: Append Answer Key & Rubric Pages if requested
    if include_answers:
        # Re-initialize header state for Answer Key
        pdf.is_answer_key = True
        pdf.add_page()
        
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(0, 100, 0)
        pdf.cell(0, 8, "SECTION II: OFFICIAL EVALUATION RUBRIC", ln=True, align="C")
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, "This rubric manual outlines point-wise distributions and model answers for student grading.", ln=True, align="C")
        pdf.ln(5)

        question_num = 1
        for idx, mark in enumerate(sorted_marks):
            part_name = part_labels[idx] if idx < len(part_labels) else f"PART {idx + 1}"
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_fill_color(220, 240, 220) # Greenish shaded divider for answers
            pdf.cell(0, 8, clean_pdf_text(f"GRADING FOR {part_name} ({mark} Mark Questions)"), ln=True, fill=True)
            pdf.ln(3)
            
            for q in grouped[mark]:
                q_type = q.get("type", "General")
                q_text = q.get("question", "")
                bloom = q.get("bloom_taxonomy", "Understanding")
                details = q.get("answer_key_details", {})
                
                # Question Reference Header
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(150, 5, clean_pdf_text(f"Q{question_num}. [{bloom}] {q_text[:70]}..."))
                pdf.cell(40, 5, clean_pdf_text(f"[{mark} Marks Max]"), ln=True, align="R")
                pdf.ln(1)
                
                # Full question text
                pdf.set_font("Helvetica", "I", 9)
                pdf.set_text_color(80, 80, 80)
                pdf.multi_cell(0, 4.5, clean_pdf_text(f"Full Question: {q_text}"))
                pdf.set_text_color(0, 0, 0)
                pdf.ln(1.5)

                # Ideal Length
                pdf.set_font("Helvetica", "B", 9)
                pdf.cell(45, 5, clean_pdf_text("Expected Answer Length: "))
                pdf.set_font("Helvetica", "", 9)
                pdf.cell(0, 5, clean_pdf_text(details.get("ideal_length", "N/A")), ln=True)

                # Keywords
                pdf.set_font("Helvetica", "B", 9)
                pdf.cell(45, 5, clean_pdf_text("Essential Keywords: "))
                pdf.set_font("Helvetica", "", 9)
                keywords_str = ", ".join(details.get("keywords", []))
                pdf.cell(0, 5, clean_pdf_text(keywords_str or "N/A"), ln=True)

                # Expected Concepts
                pdf.set_font("Helvetica", "B", 9)
                pdf.cell(0, 5, clean_pdf_text("Expected Conceptual Areas:"), ln=True)
                pdf.set_font("Helvetica", "", 9)
                for conc in details.get("expected_concepts", []):
                    pdf.cell(5) # indent
                    pdf.cell(0, 4.5, clean_pdf_text(f"- {conc}"), ln=True)

                # Step-by-Step Marking Scheme
                pdf.ln(1)
                pdf.set_font("Helvetica", "B", 9)
                pdf.cell(0, 5, clean_pdf_text("Marking Scheme Breakdown:"), ln=True)
                pdf.set_font("Helvetica", "", 9)
                for step in details.get("marking_scheme", []):
                    pdf.cell(5) # indent
                    pdf.cell(140, 4.5, clean_pdf_text(f"* {step.get('criteria')}:"))
                    pdf.cell(45, 4.5, clean_pdf_text(f"{step.get('marks')} Mark(s)"), ln=True, align="R")

                # Model Answer / Explanation
                pdf.ln(1.5)
                pdf.set_font("Helvetica", "B", 9)
                pdf.cell(0, 5, clean_pdf_text("Model Answer / Grading Guideline:"), ln=True)
                pdf.set_font("Helvetica", "", 9)
                pdf.multi_cell(0, 4.5, clean_pdf_text(details.get("model_answer", "No answer guidelines.")))
                
                # Divider line
                pdf.ln(3)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(3)
                
                question_num += 1
            
    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return output.getvalue()
