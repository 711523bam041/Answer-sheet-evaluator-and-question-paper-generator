import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_pdf(filename, title, content_list):
    filepath = os.path.join("d:\\answer-evaluator", filename)
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    story = []
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        spaceAfter=15
    )
    
    q_style = ParagraphStyle(
        'QStyle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        spaceBefore=10,
        spaceAfter=5
    )
    
    a_style = ParagraphStyle(
        'AStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        spaceAfter=10
    )
    
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 10))
    
    for q, a in content_list:
        story.append(Paragraph(q, q_style))
        story.append(Paragraph(a, a_style))
        
    doc.build(story)
    print(f"Created: {filename}")

if __name__ == "__main__":
    questions_answers = [
        ("Q1: What is machine learning?", 
         "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It uses algorithms to analyze data and make predictions based on patterns."),
        ("Q2: Explain supervised learning", 
         "Supervised learning is a machine learning approach where the algorithm learns from labeled training data. Each training example includes both input features and the correct output label. The model learns the mapping between inputs and outputs through this labeled data."),
        ("Q3: What is the difference between regression and classification?", 
         "Regression is used to predict continuous numerical values such as house prices or temperature. Classification is used to predict discrete categorical values such as whether something is a cat or dog. These are two different types of supervised learning problems."),
    ]
    generate_pdf("sample_answer_key.pdf", "Answer Key - Machine Learning Basics", questions_answers)

    student_answers = [
        ("Q1: What is machine learning?", 
         "Machine learning is a type of AI where computers can learn from data and make decisions without being told how to do it. It finds patterns in data using algorithms."),
        ("Q2: Explain supervised learning", 
         "Supervised learning is when a machine learning model is trained with labeled examples. The training data has both input and correct output, so the algorithm learns to map inputs to outputs."),
        ("Q3: What is the difference between regression and classification?", 
         "Regression predicts numbers like prices, classification predicts categories like cat or dog. They are different types of machine learning tasks."),
    ]
    generate_pdf("sample_student_answer.pdf", "Student Answers - Machine Learning", student_answers)
