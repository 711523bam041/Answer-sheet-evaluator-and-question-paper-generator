import os
import json
from io import BytesIO
import pandas as pd
from fpdf import FPDF
from datetime import datetime

class ReportPDF(FPDF):
    """Custom FPDF class with modern style, headers, and footers."""
    def __init__(self, report_title="Report"):
        super().__init__()
        self.report_title = report_title
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        # Top banner styling
        self.set_fill_color(30, 41, 59) # Charcoal Blue
        self.rect(0, 0, 210, 10, 'F')
        
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", 'B', 8)
        self.cell(0, -6, "ANSWER EVALUATOR - ADMINISTRATIVE REPORT PANEL", align='R', ln=True)
        
        self.ln(12)
        
    def footer(self):
        self.set_y(-15)
        self.set_text_color(100, 116, 139) # Slate Grey
        self.set_font("Helvetica", 'I', 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align='R')
        self.cell(0, 10, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", align='L')

    def add_report_header(self, title):
        self.set_text_color(15, 23, 42) # Slate Dark
        self.set_font("Helvetica", 'B', 18)
        self.cell(0, 10, title, ln=True)
        self.set_draw_color(226, 232, 240)
        self.set_line_width(0.5)
        self.line(15, self.get_y() + 2, 195, self.get_y() + 2)
        self.ln(8)

    def add_section_header(self, title):
        self.set_text_color(30, 41, 59)
        self.set_font("Helvetica", 'B', 12)
        self.cell(0, 10, title, ln=True)
        self.ln(2)

    def draw_grid_row(self, label, value, col_width=90, label_bold=True, text_color=(51, 65, 85)):
        self.set_text_color(30, 41, 59)
        if label_bold:
            self.set_font("Helvetica", 'B', 9)
        else:
            self.set_font("Helvetica", '', 9)
        self.cell(col_width, 6, f"{label}:", border=0)
        
        self.set_text_color(*text_color)
        self.set_font("Helvetica", '', 9)
        self.cell(col_width, 6, str(value), border=0, ln=True)

    def add_callout(self, text, is_warning=False):
        # Draw a beautiful grey/red callout box
        self.set_font("Helvetica", '', 9)
        if is_warning:
            self.set_fill_color(254, 242, 242) # Light Red
            self.set_text_color(153, 27, 27) # Dark Red
            self.set_draw_color(252, 165, 165)
        else:
            self.set_fill_color(248, 250, 252) # Light Grey
            self.set_text_color(51, 65, 85)
            self.set_draw_color(226, 232, 240)
            
        self.set_line_width(0.5)
        self.cell(0, 8, text, border=1, ln=True, fill=True)
        self.ln(4)


# ==========================================
# 1. STUDENT REPORT
# ==========================================
def generate_student_report(result, format_type):
    if format_type == 'excel':
        # Excel version
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='openpyxl')
        
        # Overview Sheet
        overview_data = {
            "Field": [
                "Student Name", "Roll Number", "Final Score", "Grade", 
                "Evaluation Confidence", "Review Status", "Reviewer Remarks",
                "Evaluation Date", "Submission Filename", "Plagiarism Flag"
            ],
            "Value": [
                result.student_name,
                result.roll_number or "N/A",
                result.marks,
                result.grade or "N/A",
                f"{int(result.confidence_score * 100)}%" if result.confidence_score else "N/A",
                result.review_status,
                result.reviewer_comments or "N/A",
                result.created_at.strftime('%Y-%m-%d %H:%M:%S') if result.created_at else "N/A",
                result.student_filename,
                "YES (Flagged)" if result.is_flagged else "NO (Clear)"
            ]
        }
        pd.DataFrame(overview_data).to_excel(writer, sheet_name="Overview", index=False)
        
        # Question Breakdown Sheet
        evals = result.question_evaluations or []
        breakdown_list = []
        for ev in evals:
            breakdown_list.append({
                "Question Num": ev.get("question_num", "N/A"),
                "Max Marks": ev.get("max_marks", 0.0),
                "Earned Marks": ev.get("earned_marks", 0.0),
                "Correctness Score": ev.get("correctness_score", 0.0),
                "Concept Coverage Score": ev.get("concept_score", 0.0),
                "Keyword Score": ev.get("keyword_score", 0.0),
                "Completeness Score": ev.get("completeness_score", 0.0),
                "Feedback": ev.get("feedback", ""),
                "Deductions / Remarks": ev.get("deduction_reason", "")
            })
        if not breakdown_list:
            breakdown_list = [{"Status": "No question breakdown available"}]
        pd.DataFrame(breakdown_list).to_excel(writer, sheet_name="Question Evaluations", index=False)
        
        # Extracted Text Sheet
        extracted_text_data = {"Extracted Answer Text": [result.extracted_text or ""]}
        pd.DataFrame(extracted_text_data).to_excel(writer, sheet_name="Extracted Text", index=False)
        
        writer.close()
        return output.getvalue()
        
    else:
        # PDF Version
        pdf = ReportPDF("Student Performance Report")
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.add_report_header("Student Evaluation & Performance Report")
        
        # Basic Student Information Table
        pdf.add_section_header("Student Profile & Academic Summary")
        pdf.draw_grid_row("Student Name", result.student_name)
        pdf.draw_grid_row("Roll Number", result.roll_number or "N/A")
        pdf.draw_grid_row("Final Score", f"{result.marks} / 100", text_color=(37, 99, 235))
        pdf.draw_grid_row("Letter Grade", result.grade or "N/A", text_color=(37, 99, 235))
        pdf.draw_grid_row("AI Confidence Level", f"{int(result.confidence_score * 100)}%" if result.confidence_score else "N/A")
        pdf.draw_grid_row("Evaluation Date", result.created_at.strftime('%Y-%m-%d %H:%M:%S') if result.created_at else "N/A")
        pdf.draw_grid_row("Review Status", result.review_status)
        pdf.draw_grid_row("Reviewer Comments", result.reviewer_comments or "None")
        pdf.ln(4)
        
        # Flag Callout if Flagged
        if result.is_flagged:
            reasons_str = ""
            if result.flag_details and result.flag_details.get("reasons"):
                reasons_str = " Reasons: " + " | ".join(result.flag_details["reasons"])
            pdf.add_callout(f"FLAGGED: This submission has been flagged for audit review.{reasons_str}", is_warning=True)
            
        pdf.ln(2)
        
        # Question-by-Question Evaluations
        pdf.add_section_header("Question-by-Question Grading Breakdown")
        
        evals = result.question_evaluations or []
        if evals:
            # Table Headers
            pdf.set_fill_color(241, 245, 249)
            pdf.set_font("Helvetica", 'B', 9)
            pdf.cell(15, 8, "Q#", border=1, fill=True)
            pdf.cell(20, 8, "Score", border=1, fill=True)
            pdf.cell(20, 8, "Max Marks", border=1, fill=True)
            pdf.cell(125, 8, "Feedback & Deduction Explanations", border=1, fill=True, ln=True)
            
            pdf.set_font("Helvetica", '', 8)
            for ev in evals:
                q_num = str(ev.get("question_num", ""))
                marks = f"{ev.get('earned_marks', 0.0):.2f}"
                max_m = f"{ev.get('max_marks', 0.0):.2f}"
                
                feedback = ev.get("feedback", "")
                deductions = ev.get("deduction_reason", "")
                full_feedback = f"{feedback} {deductions}".strip()
                if not full_feedback:
                    full_feedback = "N/A"
                
                # Check for height
                y_before = pdf.get_y()
                pdf.cell(15, 6, q_num, border=0)
                pdf.cell(20, 6, marks, border=0)
                pdf.cell(20, 6, max_m, border=0)
                
                # feedback multi-cell
                pdf.set_x(70)
                pdf.multi_cell(125, 5, full_feedback, border=0)
                y_after = pdf.get_y()
                row_height = max(y_after - y_before, 6)
                
                # Draw separating line
                pdf.set_draw_color(241, 245, 249)
                pdf.line(15, y_before + row_height, 195, y_before + row_height)
                pdf.set_y(y_before + row_height)
        else:
            pdf.cell(0, 8, "No question breakdown details available for this result.", ln=True)
            
        pdf.ln(8)
        
        # Extracted Text Section
        pdf.add_section_header("OCR Extracted Answers text")
        pdf.set_font("Helvetica", '', 9)
        pdf.set_fill_color(250, 250, 250)
        # Wrap the extracted text safely
        safe_text = result.extracted_text or "No extracted text available."
        pdf.multi_cell(0, 5, safe_text, border=1, fill=True)
        
        return bytes(pdf.output())


# ==========================================
# 2. FACULTY REPORT
# ==========================================
def generate_faculty_report(results, format_type, batch_id=None):
    # Aggregated metrics for Faculty
    total_students = len(results)
    avg_score = round(sum(r.marks for r in results) / total_students, 2) if total_students > 0 else 0.0
    flagged_count = sum(1 for r in results if r.is_flagged)
    
    # Pass rate (threshold >= 60)
    passed_count = sum(1 for r in results if r.marks >= 60)
    pass_rate = round((passed_count / total_students) * 100, 2) if total_students > 0 else 0.0
    
    # Review statuses
    statuses = {"Approved": 0, "Rejected": 0, "Pending Review": 0}
    for r in results:
        status = r.review_status or "Pending Review"
        statuses[status] = statuses.get(status, 0) + 1

    if format_type == 'excel':
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='openpyxl')
        
        # Summary Sheet
        summary_data = {
            "Metric": ["Total Student Sheets", "Class Average Score", "Passed Count (>=60%)", "Pass Rate (%)", "Flagged Submissions", "Approved Count", "Rejected Count", "Pending Review Count"],
            "Value": [total_students, avg_score, passed_count, pass_rate, flagged_count, statuses.get("Approved", 0), statuses.get("Rejected", 0), statuses.get("Pending Review", 0)]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name="Class Summary", index=False)
        
        # Submissions Sheet
        sub_list = []
        for r in results:
            sub_list.append({
                "Student Name": r.student_name,
                "Roll Number": r.roll_number or "N/A",
                "Marks Scored": r.marks,
                "Grade": r.grade or "N/A",
                "Similarity Max (%)": r.similarity_score,
                "Flagged": "Yes" if r.is_flagged else "No",
                "Review Status": r.review_status or "Pending Review",
                "Reviewer Remarks": r.reviewer_comments or "",
                "Evaluation Date": r.created_at.strftime('%Y-%m-%d %H:%M:%S') if r.created_at else ""
            })
        pd.DataFrame(sub_list).to_excel(writer, sheet_name="Submissions List", index=False)
        
        writer.close()
        return output.getvalue()
        
    else:
        # PDF Version
        pdf = ReportPDF("Faculty Audit & Evaluation Report")
        pdf.alias_nb_pages()
        pdf.add_page()
        
        batch_title_suffix = f" (Batch: {batch_id[:8]}...)" if batch_id else ""
        pdf.add_report_header(f"Faculty Evaluation Summary Report{batch_title_suffix}")
        
        pdf.add_section_header("Batch Summary Metrics")
        pdf.draw_grid_row("Total Answer Sheets Audited", total_students)
        pdf.draw_grid_row("Average Marks Scored", f"{avg_score} %")
        pdf.draw_grid_row("Students Passed (>=60%)", f"{passed_count} / {total_students} ({pass_rate}%)")
        pdf.draw_grid_row("Submissions Flagged", flagged_count, text_color=(220, 38, 38) if flagged_count > 0 else (30, 41, 59))
        pdf.ln(4)
        
        pdf.add_section_header("Faculty Review Board Audit Trail")
        pdf.draw_grid_row("Audit Approved", statuses.get("Approved", 0))
        pdf.draw_grid_row("Audit Rejected", statuses.get("Rejected", 0))
        pdf.draw_grid_row("Audit Pending Review", statuses.get("Pending Review", 0), text_color=(180, 83, 9) if statuses.get("Pending Review", 0) > 0 else (30, 41, 59))
        pdf.ln(4)
        
        # Submissions Table
        pdf.add_section_header("Detailed Student Submission Roster")
        if results:
            pdf.set_fill_color(241, 245, 249)
            pdf.set_font("Helvetica", 'B', 8)
            pdf.cell(35, 7, "Student Name", border=1, fill=True)
            pdf.cell(20, 7, "Roll No", border=1, fill=True)
            pdf.cell(15, 7, "Score", border=1, fill=True)
            pdf.cell(12, 7, "Grade", border=1, fill=True)
            pdf.cell(15, 7, "Similarity", border=1, fill=True)
            pdf.cell(15, 7, "Flagged", border=1, fill=True)
            pdf.cell(25, 7, "Review Status", border=1, fill=True)
            pdf.cell(43, 7, "Reviewer Remarks", border=1, fill=True, ln=True)
            
            pdf.set_font("Helvetica", '', 7.5)
            for r in results:
                flag_str = "YES" if r.is_flagged else "NO"
                pdf.cell(35, 6, r.student_name[:20], border=0)
                pdf.cell(20, 6, str(r.roll_number or "N/A")[:12], border=0)
                pdf.cell(15, 6, f"{r.marks:.1f}", border=0)
                pdf.cell(12, 6, r.grade or "N/A", border=0)
                pdf.cell(15, 6, f"{r.similarity_score:.1f}%", border=0)
                
                # Flagged column color highlighting
                if r.is_flagged:
                    pdf.set_text_color(220, 38, 38)
                pdf.cell(15, 6, flag_str, border=0)
                pdf.set_text_color(30, 41, 59)
                
                pdf.cell(25, 6, r.review_status or "Pending", border=0)
                pdf.cell(43, 6, (r.reviewer_comments or "")[:28], border=0, ln=True)
                
                # Line separator
                y = pdf.get_y()
                pdf.set_draw_color(241, 245, 249)
                pdf.line(15, y, 195, y)
        else:
            pdf.cell(0, 8, "No submissions found for this batch.", ln=True)
            
        return bytes(pdf.output())


# ==========================================
# 3. CLASS PERFORMANCE REPORT
# ==========================================
def generate_class_report(results, format_type, batch_id=None):
    total_students = len(results)
    avg_score = round(sum(r.marks for r in results) / total_students, 2) if total_students > 0 else 0.0
    highest_score = max(r.marks for r in results) if total_students > 0 else 0.0
    lowest_score = min(r.marks for r in results) if total_students > 0 else 0.0
    
    passed_count = sum(1 for r in results if r.marks >= 60)
    pass_rate = round((passed_count / total_students) * 100, 2) if total_students > 0 else 0.0
    
    # Grade breakdown
    grades = {}
    for r in results:
        gr = r.grade or "N/A"
        grades[gr] = grades.get(gr, 0) + 1
        
    # Sorted rankings
    rankings = sorted(results, key=lambda x: x.marks, reverse=True)
    
    # Dimension aggregations (Correctness, coverage, keyword match, completeness)
    # Extracts from result.question_evaluations
    avg_correctness = 0.0
    avg_concept = 0.0
    avg_keyword = 0.0
    avg_completeness = 0.0
    eval_counts = 0
    
    for r in results:
        evals = r.question_evaluations or []
        for ev in evals:
            # We assume dimensions are out of 10.0 or normalize to percentage
            max_m = ev.get("max_marks", 10.0) or 10.0
            avg_correctness += (ev.get("correctness_score", 0.0) / max_m)
            avg_concept += (ev.get("concept_score", 0.0) / max_m)
            avg_keyword += (ev.get("keyword_score", 0.0) / max_m)
            avg_completeness += (ev.get("completeness_score", 0.0) / max_m)
            eval_counts += 1
            
    if eval_counts > 0:
        avg_correctness = round((avg_correctness / eval_counts) * 100, 1)
        avg_concept = round((avg_concept / eval_counts) * 100, 1)
        avg_keyword = round((avg_keyword / eval_counts) * 100, 1)
        avg_completeness = round((avg_completeness / eval_counts) * 100, 1)

    if format_type == 'excel':
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='openpyxl')
        
        # Summary Statistics
        stats_data = {
            "Metric": ["Total Students", "Class Average Score", "Highest Score", "Lowest Score", "Pass Rate (%)", "Average Correctness Alignment (%)", "Average Concept Coverage (%)", "Average Keyword Match Rate (%)", "Average Answer Completeness (%)"],
            "Value": [total_students, avg_score, highest_score, lowest_score, pass_rate, avg_correctness, avg_concept, avg_keyword, avg_completeness]
        }
        pd.DataFrame(stats_data).to_excel(writer, sheet_name="Class Analytics", index=False)
        
        # Rankings Sheet
        rank_list = []
        for rank, r in enumerate(rankings, 1):
            rank_list.append({
                "Rank": rank,
                "Student Name": r.student_name,
                "Roll Number": r.roll_number or "N/A",
                "Marks Scored": r.marks,
                "Grade": r.grade or "N/A"
            })
        pd.DataFrame(rank_list).to_excel(writer, sheet_name="Rankings & Scores", index=False)
        
        # Grade Distribution Sheet
        grade_dist = []
        for g, count in sorted(grades.items()):
            pct = round((count / total_students) * 100, 2) if total_students > 0 else 0.0
            grade_dist.append({"Grade": g, "Count": count, "Percentage (%)": pct})
        pd.DataFrame(grade_dist).to_excel(writer, sheet_name="Grade Distribution", index=False)
        
        writer.close()
        return output.getvalue()
        
    else:
        # PDF Version
        pdf = ReportPDF("Class Performance Report")
        pdf.alias_nb_pages()
        pdf.add_page()
        
        batch_title_suffix = f" (Batch: {batch_id[:8]}...)" if batch_id else ""
        pdf.add_report_header(f"Class Performance & Analytics Report{batch_title_suffix}")
        
        pdf.add_section_header("Key Performance Metrics")
        pdf.draw_grid_row("Class Average Score", f"{avg_score}%")
        pdf.draw_grid_row("Highest Score Achieved", f"{highest_score}%")
        pdf.draw_grid_row("Lowest Score Achieved", f"{lowest_score}%")
        pdf.draw_grid_row("Class Pass Rate (>=60%)", f"{pass_rate}%")
        pdf.ln(4)
        
        pdf.add_section_header("Multi-Dimensional Grading Alignment")
        pdf.draw_grid_row("Semantic Correctness Alignment (SBERT)", f"{avg_correctness}%")
        pdf.draw_grid_row("Key Concept Coverage", f"{avg_concept}%")
        pdf.draw_grid_row("Keyword Matching Success Rate", f"{avg_keyword}%")
        pdf.draw_grid_row("Answer Length & Completeness Alignment", f"{avg_completeness}%")
        pdf.ln(4)
        
        # Grade Distribution
        pdf.add_section_header("Grade Distribution Summary")
        pdf.set_fill_color(241, 245, 249)
        pdf.set_font("Helvetica", 'B', 9)
        pdf.cell(50, 7, "Grade", border=1, fill=True)
        pdf.cell(50, 7, "Count", border=1, fill=True)
        pdf.cell(80, 7, "Percentage (%)", border=1, fill=True, ln=True)
        
        pdf.set_font("Helvetica", '', 9)
        for g, count in sorted(grades.items()):
            pct = (count / total_students) * 100 if total_students > 0 else 0.0
            pdf.cell(50, 6, g, border=1)
            pdf.cell(50, 6, str(count), border=1)
            pdf.cell(80, 6, f"{pct:.1f}%", border=1, ln=True)
        pdf.ln(6)
        
        # Top Performers List
        pdf.add_section_header("Top Performers (Ranked)")
        pdf.set_fill_color(241, 245, 249)
        pdf.set_font("Helvetica", 'B', 8)
        pdf.cell(20, 7, "Rank", border=1, fill=True)
        pdf.cell(70, 7, "Student Name", border=1, fill=True)
        pdf.cell(40, 7, "Roll No", border=1, fill=True)
        pdf.cell(30, 7, "Score Achieved", border=1, fill=True)
        pdf.cell(20, 7, "Grade", border=1, fill=True, ln=True)
        
        pdf.set_font("Helvetica", '', 8)
        for i, r in enumerate(rankings[:10], 1): # Show top 10
            pdf.cell(20, 6, str(i), border=1)
            pdf.cell(70, 6, r.student_name, border=1)
            pdf.cell(40, 6, r.roll_number or "N/A", border=1)
            pdf.cell(30, 6, f"{r.marks:.2f}%", border=1)
            pdf.cell(20, 6, r.grade or "N/A", border=1, ln=True)
            
        return bytes(pdf.output())


# ==========================================
# 4. SIMILARITY & PLAGIARISM REPORT
# ==========================================
def generate_similarity_report(results, format_type, batch_id=None):
    # Extracts all matches with similarity >= 80
    student_matches = []
    model_matches = []
    
    for r in results:
        plag = r.plagiarism_details or {}
        matches = plag.get("matches", [])
        for m in matches:
            sim = m.get("similarity", 0.0)
            if sim >= 80.0:
                match_type = m.get("type", "student")
                matched_to = m.get("matched_to", "")
                reason = m.get("reason", "Similarity exceeds threshold (80%).")
                
                # Check for duplicates or store
                entry = {
                    "student_name": r.student_name,
                    "roll_number": r.roll_number or "N/A",
                    "matched_to": matched_to,
                    "similarity": sim,
                    "reason": reason,
                    "review_status": r.review_status or "Pending Review"
                }
                
                if match_type == 'model_answer':
                    model_matches.append(entry)
                else:
                    # To avoid duplicates in student-student matches (A<->B and B<->A)
                    # We can store them sorted
                    pair = sorted([r.student_name, matched_to])
                    pair_key = f"{pair[0]} <-> {pair[1]}"
                    # Check if already added
                    if not any(x.get("pair_key") == pair_key for x in student_matches):
                        entry["pair_key"] = pair_key
                        student_matches.append(entry)

    # Sort matches by similarity descending
    student_matches = sorted(student_matches, key=lambda x: x["similarity"], reverse=True)
    model_matches = sorted(model_matches, key=lambda x: x["similarity"], reverse=True)

    if format_type == 'excel':
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='openpyxl')
        
        # Student-Student Plagiarism Matches
        std_list = []
        for idx, m in enumerate(student_matches, 1):
            std_list.append({
                "Match ID": idx,
                "Student Pair": m["pair_key"],
                "Similarity Score (%)": m["similarity"],
                "Flag Reason": m["reason"],
                "Review Status": m["review_status"]
            })
        if not std_list:
            std_list = [{"Status": "No student-student similarity matches exceeding 80%"}]
        pd.DataFrame(std_list).to_excel(writer, sheet_name="Student-to-Student Matches", index=False)
        
        # Student-Model Matches
        mod_list = []
        for idx, m in enumerate(model_matches, 1):
            mod_list.append({
                "Student Name": m["student_name"],
                "Roll Number": m["roll_number"],
                "Matched To": m["matched_to"],
                "Similarity Score (%)": m["similarity"],
                "Flag Reason": m["reason"],
                "Review Status": m["review_status"]
            })
        if not mod_list:
            mod_list = [{"Status": "No student-to-model similarity matches exceeding 80%"}]
        pd.DataFrame(mod_list).to_excel(writer, sheet_name="Student-to-Model Matches", index=False)
        
        writer.close()
        return output.getvalue()
        
    else:
        # PDF Version
        pdf = ReportPDF("Plagiarism & Similarity Audit Report")
        pdf.alias_nb_pages()
        pdf.add_page()
        
        batch_title_suffix = f" (Batch: {batch_id[:8]}...)" if batch_id else ""
        pdf.add_report_header(f"Plagiarism & Similarity Audit Report{batch_title_suffix}")
        
        # Summary
        total_plag_flags = len(student_matches) + len(model_matches)
        pdf.add_section_header("Similarity Audit Summary")
        pdf.draw_grid_row("Total Student-Student Matches (>=80%)", len(student_matches))
        pdf.draw_grid_row("Total Student-Model Key Matches (>=80%)", len(model_matches))
        pdf.draw_grid_row("Total Similarity Incidents Flagged", total_plag_flags, text_color=(220, 38, 38) if total_plag_flags > 0 else (30, 41, 59))
        pdf.ln(4)
        
        # Student-Student Plagiarism Table
        pdf.add_section_header("Student-to-Student Similarity Incidents")
        if student_matches:
            pdf.set_fill_color(254, 242, 242) # Reddish header
            pdf.set_text_color(153, 27, 27)
            pdf.set_font("Helvetica", 'B', 8)
            pdf.cell(75, 7, "Student Pair", border=1, fill=True)
            pdf.cell(25, 7, "Similarity", border=1, fill=True)
            pdf.cell(45, 7, "Flag Reason", border=1, fill=True)
            pdf.cell(35, 7, "Review Status", border=1, fill=True, ln=True)
            
            pdf.set_text_color(30, 41, 59)
            pdf.set_font("Helvetica", '', 8)
            for m in student_matches:
                pdf.cell(75, 6, m["pair_key"], border=1)
                pdf.cell(25, 6, f"{m['similarity']:.2f}%", border=1)
                pdf.cell(45, 6, m["reason"][:28], border=1)
                pdf.cell(35, 6, m["review_status"], border=1, ln=True)
        else:
            pdf.cell(0, 8, "No student-to-student similarity flags recorded in this batch.", ln=True)
        pdf.ln(6)
        
        # Student-Model Key Table
        pdf.add_section_header("Student-to-Model Answer Key Copying Incidents")
        if model_matches:
            pdf.set_fill_color(254, 242, 242)
            pdf.set_text_color(153, 27, 27)
            pdf.set_font("Helvetica", 'B', 8)
            pdf.cell(45, 7, "Student Name", border=1, fill=True)
            pdf.cell(30, 7, "Roll No", border=1, fill=True)
            pdf.cell(25, 7, "Similarity", border=1, fill=True)
            pdf.cell(45, 7, "Flag Reason", border=1, fill=True)
            pdf.cell(35, 7, "Review Status", border=1, fill=True, ln=True)
            
            pdf.set_text_color(30, 41, 59)
            pdf.set_font("Helvetica", '', 8)
            for m in model_matches:
                pdf.cell(45, 6, m["student_name"], border=1)
                pdf.cell(30, 6, m["roll_number"], border=1)
                pdf.cell(25, 6, f"{m['similarity']:.2f}%", border=1)
                pdf.cell(45, 6, m["reason"][:28], border=1)
                pdf.cell(35, 6, m["review_status"], border=1, ln=True)
        else:
            pdf.cell(0, 8, "No student-to-model similarity flags recorded in this batch.", ln=True)
            
        return bytes(pdf.output())


# ==========================================
# 5. FLAGGED SUBMISSION REPORT
# ==========================================
def generate_flagged_report(results, format_type, batch_id=None):
    # Filter only flagged results
    flagged_results = [r for r in results if r.is_flagged]

    if format_type == 'excel':
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='openpyxl')
        
        flag_list = []
        for r in flagged_results:
            reasons = r.flag_details.get("reasons", []) if r.flag_details else []
            reasons_str = "; ".join(reasons)
            
            ai_score = "N/A"
            if r.flag_details and r.flag_details.get("ai_details"):
                ai_score = f"{int(r.flag_details['ai_details'].get('score', 0.0) * 100)}%"

            flag_list.append({
                "Student Name": r.student_name,
                "Roll Number": r.roll_number or "N/A",
                "Marks Scored": r.marks,
                "Grade": r.grade or "N/A",
                "Flag Reasons": reasons_str,
                "AI Content Confidence": ai_score,
                "Review Status": r.review_status or "Pending Review",
                "Reviewer Remarks": r.reviewer_comments or "",
                "Flagged Date": r.created_at.strftime('%Y-%m-%d %H:%M:%S') if r.created_at else ""
            })
        if not flag_list:
            flag_list = [{"Status": "No flagged submissions found in this batch"}]
        pd.DataFrame(flag_list).to_excel(writer, sheet_name="Flagged Submissions", index=False)
        
        writer.close()
        return output.getvalue()
        
    else:
        # PDF Version
        pdf = ReportPDF("Flagged Submissions Audit Trail")
        pdf.alias_nb_pages()
        pdf.add_page()
        
        batch_title_suffix = f" (Batch: {batch_id[:8]}...)" if batch_id else ""
        pdf.add_report_header(f"Flagged Submissions Audit Trail{batch_title_suffix}")
        
        # Summary
        pdf.add_section_header("Flagged Submissions Overview")
        pdf.draw_grid_row("Total Submissions Audited", len(results))
        pdf.draw_grid_row("Total Submissions Flagged", len(flagged_results), text_color=(220, 38, 38) if flagged_results else (30, 41, 59))
        
        pending_audit = sum(1 for r in flagged_results if r.review_status == 'Pending Review')
        pdf.draw_grid_row("Pending Faculty Audit Decision", pending_audit, text_color=(180, 83, 9) if pending_audit > 0 else (30, 41, 59))
        pdf.ln(4)
        
        # Flagged Submissions Table
        pdf.add_section_header("Audit Details of Flagged Cases")
        if flagged_results:
            pdf.set_fill_color(254, 242, 242)
            pdf.set_text_color(153, 27, 27)
            pdf.set_font("Helvetica", 'B', 8)
            pdf.cell(35, 7, "Student Name", border=1, fill=True)
            pdf.cell(15, 7, "Roll No", border=1, fill=True)
            pdf.cell(12, 7, "Score", border=1, fill=True)
            
            # Reasons column needs to be wide or multi_cell
            pdf.cell(50, 7, "Flag Reasons Summary", border=1, fill=True)
            pdf.cell(15, 7, "AI Conf.", border=1, fill=True)
            pdf.cell(20, 7, "Status", border=1, fill=True)
            pdf.cell(33, 7, "Reviewer Comments", border=1, fill=True, ln=True)
            
            pdf.set_text_color(30, 41, 59)
            pdf.set_font("Helvetica", '', 7.5)
            
            for r in flagged_results:
                reasons = r.flag_details.get("reasons", []) if r.flag_details else []
                # Clean up reasons to make them fit or summarize
                reasons_clean = []
                for re in reasons:
                    if "AI-generated" in re:
                        reasons_clean.append("AI Content")
                    elif "Similarity to" in re:
                        reasons_clean.append("High Sim")
                    elif "Suspicious pattern" in re:
                        reasons_clean.append("Low Score Match")
                    else:
                        reasons_clean.append(re[:15])
                reasons_str = ", ".join(reasons_clean)
                if not reasons_str:
                    reasons_str = "Flagged"
                
                ai_score = "N/A"
                if r.flag_details and r.flag_details.get("ai_details"):
                    ai_score = f"{int(r.flag_details['ai_details'].get('score', 0.0) * 100)}%"
                    
                pdf.cell(35, 6, r.student_name[:20], border=1)
                pdf.cell(15, 6, str(r.roll_number or "N/A")[:10], border=1)
                pdf.cell(12, 6, f"{r.marks:.1f}", border=1)
                pdf.cell(50, 6, reasons_str[:32], border=1)
                pdf.cell(15, 6, ai_score, border=1)
                pdf.cell(20, 6, r.review_status or "Pending", border=1)
                pdf.cell(33, 6, (r.reviewer_comments or "")[:22], border=1, ln=True)
        else:
            pdf.cell(0, 8, "No flagged submissions recorded in this batch.", ln=True)
            
        return bytes(pdf.output())
