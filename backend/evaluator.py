import PyPDF2
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import os
import re
import warnings
import logging
import numpy as np

# Suppress warnings
warnings.filterwarnings('ignore')

log = logging.getLogger(__name__)

# Configure Tesseract path (Windows user installation)
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\Ruthrayini\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# Cache for processed images to avoid re-processing
_image_cache = {}

# Cache for text embeddings to avoid recomputation in plagiarism check
_embedding_cache = {}

# Lazy load model to avoid blocking Flask startup
model = None
model_error = None
try_load = True

def preprocess_image(image_path, target_size=(1024, 1280)):
    """
    Preprocess image for better OCR accuracy.
    
    Optimizations:
    1. Resize to standard size (improves OCR consistency)
    2. Enhance contrast (better text visibility)
    3. Reduce noise (cleaner text)
    4. Correct rotation (for rotated documents)
    5. Compress for efficiency
    
    Args:
        image_path: Path to image file
        target_size: Target image size (width, height)
        
    Returns:
        PIL Image object (preprocessed)
    """
    try:
        # Open image
        img = Image.open(image_path).convert('RGB')
        original_size = img.size
        
        log.debug(f"Preprocessing image: {image_path} (original: {original_size})")
        
        # Step 1: Detect and correct rotation
        img = _detect_and_correct_rotation(img)
        
        # Step 2: Resize image (maintain aspect ratio)
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        log.debug(f"  ✓ Resized to: {img.size}")
        
        # Step 3: Enhance contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)  # Increase contrast by 50%
        log.debug(f"  ✓ Contrast enhanced (1.5x)")
        
        # Step 4: Enhance brightness
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)  # Slight brightness boost
        log.debug(f"  ✓ Brightness enhanced (1.1x)")
        
        # Step 5: Reduce noise with median filter
        img = img.filter(ImageFilter.MedianFilter(size=3))
        log.debug(f"  ✓ Noise reduction applied")
        
        # Step 6: Apply sharpening
        img = img.filter(ImageFilter.SHARPEN)
        log.debug(f"  ✓ Sharpening applied")
        
        return img
        
    except Exception as e:
        log.warning(f"Error preprocessing image {image_path}: {e}. Using original.")
        return Image.open(image_path).convert('RGB')

def _detect_and_correct_rotation(img):
    """
    Detect and correct image rotation using edge detection.
    
    Looks for dominant horizontal/vertical lines to determine rotation angle.
    """
    try:
        # Convert to grayscale for analysis
        gray = img.convert('L')
        
        # Apply edge detection
        edges = np.array(gray.filter(ImageFilter.FIND_EDGES))
        
        # Find dominant angle (simplified: check if more horizontal or vertical edges)
        # This is a simple heuristic; for production, use more sophisticated rotation detection
        height, width = edges.shape
        horizontal_edges = edges.sum(axis=0)  # Sum columns
        vertical_edges = edges.sum(axis=1)    # Sum rows
        
        # Check if image might be rotated 90 degrees
        if width > height and vertical_edges.max() > horizontal_edges.max():
            log.debug("  ✓ 90° rotation detected and corrected")
            return img.rotate(90, expand=True)
        elif height > width and horizontal_edges.max() > vertical_edges.max():
            log.debug("  ✓ 90° rotation detected and corrected")
            return img.rotate(-90, expand=True)
            
    except Exception as e:
        log.debug(f"Rotation detection skipped: {e}")
    
    return img

def _optimize_image_size(image_path, max_size_bytes=5*1024*1024):
    """
    Compress image to reduce file size while maintaining OCR quality.
    
    Target: Keep images under 5MB for faster processing.
    """
    try:
        img = Image.open(image_path)
        original_size = os.path.getsize(image_path)
        
        if original_size > max_size_bytes:
            # Reduce quality progressively
            quality = 85
            while original_size > max_size_bytes and quality > 50:
                img_compressed = img.copy()
                temp_path = image_path + ".tmp.jpg"
                img_compressed.save(temp_path, quality=quality, optimize=True)
                original_size = os.path.getsize(temp_path)
                quality -= 5
                os.remove(temp_path)
            
            log.debug(f"  ✓ Image optimized (quality: {quality}%)")
    except Exception as e:
        log.debug(f"Image optimization skipped: {e}")

def _clear_image_cache():
    """Clear the image cache to free memory."""
    global _image_cache
    _image_cache.clear()
    log.debug("Image cache cleared")

def _get_or_compute_embedding(text, filename=None):
    """
    Get cached embedding or compute and cache it.
    
    Args:
        text: Text to embed
        filename: Optional filename for caching key
        
    Returns:
        Embedding tensor or None if model unavailable
    """
    global _embedding_cache
    
    # Use hash of text as cache key if no filename provided
    cache_key = filename if filename else hash(text)
    
    # Check cache
    if cache_key in _embedding_cache:
        return _embedding_cache[cache_key]
    
    # Compute embedding
    model = get_model()
    if model is None:
        return None
    
    try:
        embedding = model.encode(text, convert_to_tensor=True)
        _embedding_cache[cache_key] = embedding
        log.debug(f"Embedding computed and cached for: {cache_key}")
        return embedding
    except Exception as e:
        log.warning(f"Failed to compute embedding: {e}")
        return None

def _clear_embedding_cache():
    """Clear embedding cache to free GPU/CPU memory."""
    global _embedding_cache
    cache_size = len(_embedding_cache)
    _embedding_cache.clear()
    log.debug(f"Embedding cache cleared ({cache_size} entries)")

def _calculate_plagiarism_pairs_optimized(student_texts, threshold=0.80, max_results=None):
    """
    Optimized plagiarism detection using embedding caching.
    
    Improvements:
    1. Cache embeddings to avoid recomputation
    2. Progressive detection with early reporting
    3. Efficient batch comparison
    4. Memory management
    
    Args:
        student_texts: Dict of {filename: text}
        threshold: Similarity threshold for flagging
        max_results: Max plagiarism pairs to report (None = all)
        
    Returns:
        List of (file1, file2, similarity_score) tuples
    """
    filenames = list(student_texts.keys())
    plagiarism_pairs = []
    model = get_model()
    
    log.info(f"Optimized plagiarism check: {len(filenames)} files, threshold={threshold:.0%}")
    
    # Step 1: Compute embeddings (with caching)
    if model is not None:
        log.info("Computing embeddings for plagiarism detection...")
        embeddings = {}
        for filename in filenames:
            text = student_texts[filename]
            if text.strip():
                emb = _get_or_compute_embedding(text, filename=filename)
                if emb is not None:
                    embeddings[filename] = emb
        
        log.info(f"Embeddings computed: {len(embeddings)}/{len(filenames)} files")
        
        # Step 2: Compare embeddings (O(n²) but optimized)
        if len(embeddings) > 1:
            from sentence_transformers import util
            comparisons = 0
            
            for i, file1 in enumerate(filenames):
                if file1 not in embeddings:
                    continue
                    
                for j in range(i + 1, len(filenames)):
                    file2 = filenames[j]
                    if file2 not in embeddings:
                        continue
                    
                    try:
                        # Compute similarity
                        emb1 = embeddings[file1]
                        emb2 = embeddings[file2]
                        similarity = util.cos_sim(emb1, emb2).item()
                        comparisons += 1
                        
                        # Check threshold
                        if similarity >= threshold:
                            plagiarism_pairs.append((file1, file2, similarity))
                            log.warning(f"Plagiarism detected: {file1} ↔ {file2} ({similarity*100:.1f}%)")
                            
                            # Check max results
                            if max_results and len(plagiarism_pairs) >= max_results:
                                log.info(f"Max plagiarism results ({max_results}) reached, stopping scan")
                                return plagiarism_pairs
                                
                    except Exception as e:
                        log.warning(f"Comparison failed for {file1} vs {file2}: {e}")
                        # Fallback to simple similarity
                        similarity = simple_text_similarity(
                            student_texts[file1],
                            student_texts[file2]
                        )
                        if similarity >= threshold:
                            plagiarism_pairs.append((file1, file2, similarity))
            
            log.info(f"Comparisons completed: {comparisons} pairs checked, {len(plagiarism_pairs)} instances detected")
    
    # Fallback: Use simple similarity if no model
    else:
        log.info("AI model unavailable, using simple similarity for plagiarism detection")
        for i, file1 in enumerate(filenames):
            for j in range(i + 1, len(filenames)):
                file2 = filenames[j]
                text1 = student_texts[file1]
                text2 = student_texts[file2]
                
                if text1.strip() and text2.strip():
                    similarity = simple_text_similarity(text1, text2)
                    if similarity >= threshold:
                        plagiarism_pairs.append((file1, file2, similarity))
                        log.warning(f"Plagiarism detected: {file1} ↔ {file2} ({similarity*100:.1f}%)")
    
    return plagiarism_pairs



def get_model():
    global model, model_error, try_load
    if model is None and try_load:
        try:
            log.info("Loading SBERT model: all-MiniLM-L6-v2")
            from sentence_transformers import SentenceTransformer
            # Set torch to use CPU only to avoid CUDA issues
            import os as os_module
            os_module.environ['CUDA_VISIBLE_DEVICES'] = '-1'
            model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
            log.info("✓ Model loaded successfully")
        except Exception as e:
            log.warning(f"Could not load AI model: {str(e)}")
            model_error = str(e)
            try_load = False
    return model

def simple_text_similarity(text1, text2):
    """
    Fallback text similarity using multiple algorithms.
    
    Combines:
    1. Jaccard similarity (set-based)
    2. Word overlap ratio
    3. Length penalty
    
    Returns similarity score (0-1)
    """
    text1_lower = text1.lower().split()
    text2_lower = text2.lower().split()
    
    if not text1_lower or not text2_lower:
        return 0.0
    
    # Jaccard similarity
    set1 = set(text1_lower)
    set2 = set(text2_lower)
    
    if len(set1.union(set2)) == 0:
        return 0.0
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    jaccard = intersection / union
    
    # Word overlap ratio
    overlap_ratio = intersection / max(len(set1), len(set2))
    
    # Combined similarity (weighted average)
    similarity = (jaccard * 0.6) + (overlap_ratio * 0.4)
    
    return max(0.0, min(1.0, similarity))

def _preprocess_text_for_eval(text):
    """
    Preprocess text for evaluation.
    
    Operations:
    - Convert to lowercase
    - Remove extra whitespace
    - Keep basic punctuation for semantic meaning
    """
    # Lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text

def _calculate_length_penalty(student_text, answer_key_text):
    """
    Calculate penalty for answers that are too short or too long.
    
    - Very short: High penalty (likely incomplete)
    - Similar length: No penalty
    - Very long: Moderate penalty (likely padded)
    
    Returns: Multiplier (0.5 - 1.0)
    """
    key_length = len(answer_key_text.split())
    student_length = len(student_text.split())
    
    if student_length == 0:
        return 0.0
    
    # Length ratio
    ratio = student_length / max(key_length, 1)
    
    # Calculate penalty
    if ratio < 0.3:  # Very short (< 30% of key)
        penalty = 0.5
    elif ratio < 0.5:  # Short (< 50% of key)
        penalty = 0.7
    elif ratio > 2.0:  # Very long (> 200% of key)
        penalty = 0.85
    elif ratio > 1.5:  # Long (> 150% of key)
        penalty = 0.90
    else:
        penalty = 1.0  # No penalty for reasonable length
    
    return penalty

def _calculate_keyword_match_score(student_text, answer_key_text):
    """
    Calculate score based on important keywords from answer key.
    
    Extracts key terms and checks if student answer contains them.
    
    Returns: Match score (0-1)
    """
    # Extract potential keywords (longer words, nouns)
    key_words = set()
    for word in answer_key_text.lower().split():
        # Consider words > 4 chars as potentially important
        if len(word) > 4 and word.isalpha():
            key_words.add(word)
    
    if not key_words:
        return 0.5  # Can't determine, neutral score
    
    # Count matched keywords
    student_words = set(student_text.lower().split())
    matched_keywords = len(key_words.intersection(student_words))
    keyword_match_ratio = matched_keywords / len(key_words)
    
    return keyword_match_ratio


def _calculate_grade(percentage):
    """Calculate letter grade based on percentage score."""
    if percentage >= 90:
        return 'A+'
    elif percentage >= 80:
        return 'A'
    elif percentage >= 70:
        return 'B'
    elif percentage >= 60:
        return 'C'
    elif percentage >= 50:
        return 'D'
    else:
        return 'F'


def _evaluate_keywords(student_answer, keywords):
    """
    Evaluate student's answer against a list of keywords.
    Returns:
        tuple: (match_ratio, list of dicts with matching details)
    """
    if not keywords:
        return 1.0, []
        
    matched_count = 0
    details = []
    student_lower = student_answer.lower()
    
    for kw in keywords:
        kw_clean = kw.strip().lower()
        if not kw_clean:
            continue
            
        # Use simple word boundary check or substring match
        pattern = re.compile(rf'\b{re.escape(kw_clean)}s?\b', re.IGNORECASE)
        is_matched = bool(pattern.search(student_lower))
        if not is_matched:
            # check if simple substring
            is_matched = kw_clean in student_lower
            
        if is_matched:
            matched_count += 1
            
        details.append({
            "keyword": kw,
            "matched": is_matched
        })
        
    ratio = matched_count / len(keywords) if keywords else 1.0
    return ratio, details


def _evaluate_concepts(student_answer, expected_concepts):
    """
    Evaluate student's answer against expected concepts using SBERT sentence-level matching.
    Returns:
        tuple: (coverage_ratio, list of dicts with concept coverage details)
    """
    if not expected_concepts:
        return 1.0, []
        
    # Split student answer into sentences
    sentences = [s.strip() for s in re.split(r'[.!?]+', student_answer) if s.strip()]
    if not sentences:
        sentences = [student_answer]
        
    model = get_model()
    covered_count = 0
    details = []
    
    if model is not None and len(sentences) > 0:
        try:
            from sentence_transformers import util
            # Pre-compute SBERT embeddings for expected concepts and student sentences
            c_embs = model.encode(expected_concepts, convert_to_tensor=True)
            s_embs = model.encode(sentences, convert_to_tensor=True)
            
            # Reshape if 1D
            if len(expected_concepts) == 1:
                c_embs = c_embs.unsqueeze(0)
            if len(sentences) == 1:
                s_embs = s_embs.unsqueeze(0)
                
            for idx, concept in enumerate(expected_concepts):
                c_emb = c_embs[idx]
                best_sim = 0.0
                best_sentence = ""
                
                for s_idx, sentence in enumerate(sentences):
                    s_emb = s_embs[s_idx]
                    sim = util.cos_sim(c_emb, s_emb).item()
                    if sim > best_sim:
                        best_sim = sim
                        best_sentence = sentence
                        
                # SBERT similarity threshold of 0.65 represents semantic match
                is_covered = best_sim >= 0.65
                if is_covered:
                    covered_count += 1
                    
                details.append({
                    "concept": concept,
                    "covered": is_covered,
                    "similarity": round(best_sim * 100, 2),
                    "matched_text": best_sentence if is_covered else None
                })
        except Exception as e:
            log.warning(f"SBERT concept evaluation failed: {e}. Falling back to text similarity.")
            # Fallback to text similarity
            for concept in expected_concepts:
                best_sim = 0.0
                for sentence in sentences:
                    sim = simple_text_similarity(concept, sentence)
                    if sim > best_sim:
                        best_sim = sim
                is_covered = best_sim >= 0.45
                if is_covered:
                    covered_count += 1
                details.append({
                    "concept": concept,
                    "covered": is_covered,
                    "similarity": round(best_sim * 100, 2),
                    "matched_text": None
                })
    else:
        # Fallback without AI model
        for concept in expected_concepts:
            best_sim = 0.0
            for sentence in sentences:
                sim = simple_text_similarity(concept, sentence)
                if sim > best_sim:
                    best_sim = sim
            is_covered = best_sim >= 0.45
            if is_covered:
                covered_count += 1
            details.append({
                "concept": concept,
                "covered": is_covered,
                "similarity": round(best_sim * 100, 2),
                "matched_text": None
            })
            
    ratio = covered_count / len(expected_concepts) if expected_concepts else 1.0
    return ratio, details


def _detect_ai_content(text):
    """
    Detects if the text has indicators of being AI-generated.
    Checks for common LLM transition phrases, prefix templates, or refusal markers.
    Returns:
        tuple: (confidence_score, list of detected markers)
    """
    if not text or not text.strip():
        return 0.0, []
        
    text_lower = text.lower()
    
    # Common refusal or self-identification phrases from popular LLMs
    direct_refusals = [
        "as an ai language model",
        "as an ai,",
        "my knowledge cutoff",
        "i cannot fulfill this request",
        "i am an ai assistant",
        "as a large language model",
        "i do not have real-time",
        "based on my training data",
        "last update in january 2025"
    ]
    
    # Common helper or intro filler phrases that LLMs frequently prepend/append
    intro_fillers = [
        "certainly! here is",
        "here is the explanation",
        "to summarize,",
        "in conclusion,",
        "it is important to note",
        "please note that",
        "another key point is",
        "firstly,",
        "secondly,",
        "finally, in summary",
        "delve into",
        "tapestry of",
        "testament to",
        "moreover,",
        "furthermore,"
    ]
    
    detected = []
    score = 0.0
    
    # Check for direct LLM self-identifiers (high weight)
    for phrase in direct_refusals:
        if phrase in text_lower:
            detected.append(phrase)
            score += 0.85
            
    # Check for common LLM filler patterns (moderate weight)
    filler_matches = 0
    for phrase in intro_fillers:
        if phrase in text_lower:
            detected.append(phrase)
            filler_matches += 1
            score += 0.15
            
    # Cap score at 1.0
    score = min(1.0, score)
    return round(score, 2), detected


def _check_student_self_duplicates(student_qa):
    """
    Checks if a student copied the same answer text across multiple questions on their own sheet.
    Returns list of duplicate pairs found.
    """
    if not student_qa or len(student_qa) < 2:
        return []
        
    duplicates = []
    keys = sorted(list(student_qa.keys()))
    for i in range(len(keys)):
        q1 = keys[i]
        ans1 = student_qa[q1].strip()
        if not ans1 or len(ans1.split()) < 5: # Skip empty or very short replies
            continue
            
        for j in range(i + 1, len(keys)):
            q2 = keys[j]
            ans2 = student_qa[q2].strip()
            if not ans2 or len(ans2.split()) < 5:
                continue
                
            # Compute similarity
            sim = simple_text_similarity(ans1, ans2)
            if sim >= 0.85:
                duplicates.append({
                    "q1": q1,
                    "q2": q2,
                    "similarity": round(sim * 100, 2)
                })
    return duplicates


def _enrich_question_details(question_text, answer_text, marks):
    """
    Enriches a question dict with fallback keywords and expected concepts
    if none are already provided. Matches the logic from ensure_answer_key_details.
    """
    # Pick keywords from question text
    words = [w.strip("?,.()").capitalize() for w in question_text.split() 
             if len(w) > 4 and w.lower() not in ["which", "what", "explain", "describe", "discuss", "following", "primary", "second", "example", "detail"]]
    # Default keywords
    keywords = list(set(["Concept"] + words[:4]))[:5]
    
    # Default concepts
    expected_concepts = [
        f"Demonstrate understanding of the core question requirements",
        f"Explain key elements and logic of the answer"
    ]
    
    ideal_length = "Short response"
    if marks == 1:
        ideal_length = "Single word or option"
    elif marks == 2:
        ideal_length = "30-50 words (2-3 sentences)"
    elif marks == 5:
        ideal_length = "100-150 words (1-2 paragraphs)"
    elif marks == 10:
        ideal_length = "250-350 words (1-1.5 pages)"
    else:
        ideal_length = "400-500 words (2 pages)"
        
    return {
        "model_answer": answer_text,
        "keywords": keywords,
        "expected_concepts": expected_concepts,
        "ideal_length": ideal_length
    }


def evaluate_answer_components(student_answer, max_marks, answer_key_details):
    """
    Evaluates student answer against detailed key using 4-component rubrics:
    1. Correctness (40%): Semantic similarity to model answer
    2. Concept Coverage (30%): Coverage of expected concepts
    3. Keyword Matching (20%): Matching of important keywords
    4. Completeness (10%): Length and detail depth relative to model answer
    """
    if not student_answer.strip():
        return {
            "earned_marks": 0.0,
            "similarity": 0.0,
            "feedback": "Blank or missing answer",
            "confidence": 1.0,
            "correctness_score": 0.0,
            "concept_score": 0.0,
            "keyword_score": 0.0,
            "completeness_score": 0.0,
            "concepts_details": [],
            "keywords_details": []
        }
        
    model_answer = answer_key_details.get("model_answer", "")
    keywords = answer_key_details.get("keywords", [])
    expected_concepts = answer_key_details.get("expected_concepts", [])
    
    # 1. Correctness: Semantic Similarity
    model = get_model()
    correctness_ratio = 0.0
    if model is not None:
        try:
            from sentence_transformers import util
            # Preprocess for semantic similarity
            emb1 = model.encode(_preprocess_text_for_eval(model_answer), convert_to_tensor=True)
            emb2 = model.encode(_preprocess_text_for_eval(student_answer), convert_to_tensor=True)
            correctness_ratio = max(0.0, min(1.0, util.cos_sim(emb1, emb2).item()))
        except Exception as e:
            log.warning(f"Component SBERT correctness check failed: {e}")
            correctness_ratio = simple_text_similarity(model_answer, student_answer)
    else:
        correctness_ratio = simple_text_similarity(model_answer, student_answer)
        
    # 2. Concept Coverage
    concept_ratio, concepts_details = _evaluate_concepts(student_answer, expected_concepts)
    
    # 3. Keyword Matching
    keyword_ratio, keywords_details = _evaluate_keywords(student_answer, keywords)
    
    # 4. Completeness (Length analysis)
    student_words = len(student_answer.split())
    model_words = max(len(model_answer.split()), 1)
    length_ratio = student_words / model_words
    
    if length_ratio < 0.3:
        completeness_ratio = length_ratio * 3.33  # severe penalty for very short text
    elif length_ratio < 0.5:
        completeness_ratio = 0.6
    elif length_ratio > 2.5:
        completeness_ratio = 0.8  # moderate penalty for extremely wordy answers
    else:
        completeness_ratio = 1.0
        
    # Cap between 0 and 1
    completeness_ratio = max(0.0, min(1.0, completeness_ratio))
    
    # Weights: Correctness = 40%, Concept Coverage = 30%, Keywords = 20%, Completeness = 10%
    correctness_score = correctness_ratio * 0.40 * max_marks
    concept_score = concept_ratio * 0.30 * max_marks
    keyword_score = keyword_ratio * 0.20 * max_marks
    completeness_score = completeness_ratio * 0.10 * max_marks
    
    earned_marks = round(correctness_score + concept_score + keyword_score + completeness_score, 2)
    earned_marks = min(earned_marks, max_marks)
    
    # Calculate overall similarity percentage for display
    # (Weighted average of correctness, concept, and keyword ratios)
    overall_sim = (correctness_ratio * 0.5) + (concept_ratio * 0.3) + (keyword_ratio * 0.2)
    overall_sim_percent = round(overall_sim * 100, 2)
    
    # Remark/feedback generator
    if overall_sim >= 0.90:
        feedback = "Excellent - Clear, complete, and conceptually perfect answer."
    elif overall_sim >= 0.80:
        feedback = "Excellent - Very strong answer covering all concepts."
    elif overall_sim >= 0.70:
        feedback = "Very Good - High correctness with slight keyword/concept omissions."
    elif overall_sim >= 0.60:
        feedback = "Good - Mostly correct, but lacks details or key concepts."
    elif overall_sim >= 0.50:
        feedback = "Fair - Covered some basic ideas, but incomplete."
    elif overall_sim >= 0.35:
        feedback = "Needs Review - Incomplete response with major conceptual gaps."
    else:
        feedback = "Weak - Answer is mostly unrelated or fails to match rubrics."
        
    confidence = 0.85 if model is not None else 0.75
    
    # Identify missing keywords and concepts for Explainable Evaluation (Module 5)
    missing_keywords = [kw["keyword"] for kw in keywords_details if not kw["matched"]]
    missing_concepts = [c["concept"] for c in concepts_details if not c["covered"]]
    
    if earned_marks >= max_marks:
        deduction_reason = "None - Full marks awarded."
    else:
        reasons = []
        if completeness_score < (max_marks * 0.1) * 0.8:
            reasons.append("Answer is too brief or incomplete.")
        if missing_keywords:
            reasons.append(f"Important keywords not mentioned: {', '.join([f'\"{k}\"' for k in missing_keywords[:3]])}.")
        if missing_concepts:
            reasons.append(f"Important concepts not covered: {', '.join([f'\"{c}\"' for c in missing_concepts[:2]])}.")
        if correctness_score < (max_marks * 0.4) * 0.75:
            reasons.append("Answer lacks accuracy or semantic correctness compared to the reference key.")
            
        if not reasons:
            reasons.append("Minor vocabulary or structural alignment deviations from reference key.")
            
        deduction_reason = " ".join(reasons)
        
    return {
        "earned_marks": earned_marks,
        "similarity": overall_sim_percent,
        "feedback": feedback,
        "confidence": confidence,
        "correctness_score": round(correctness_score, 2),
        "concept_score": round(concept_score, 2),
        "keyword_score": round(keyword_score, 2),
        "completeness_score": round(completeness_score, 2),
        "concepts_details": concepts_details,
        "keywords_details": keywords_details,
        "deduction_reason": deduction_reason
    }


def evaluate_answer(answer_key_text, student_text, method='hybrid'):
    """
    Evaluate student answer against key using multiple algorithms.
    
    Args:
        answer_key_text: The answer key text
        student_text: The student's answer text
        method: Evaluation method:
            'semantic' - Use AI model only
            'simple' - Use fallback algorithms only
            'hybrid' - Combine semantic + simple (default)
    
    Returns:
        Tuple: (marks, similarity_percentage, remark, confidence)
    """
    if not student_text.strip():
        log.warning("Blank student answer detected")
        return 0, 0.0, "Blank Answer", 0.0

    # Preprocess texts
    key_processed = _preprocess_text_for_eval(answer_key_text)
    student_processed = _preprocess_text_for_eval(student_text)

    model = get_model()
    semantic_sim = None
    simple_sim = None
    keyword_match = None
    
    # Calculate semantic similarity (AI-based)
    if method in ['semantic', 'hybrid'] and model is not None:
        try:
            from sentence_transformers import util
            emb1 = model.encode(key_processed, convert_to_tensor=True)
            emb2 = model.encode(student_processed, convert_to_tensor=True)
            semantic_sim = util.cos_sim(emb1, emb2).item()
            semantic_sim = max(0.0, min(1.0, semantic_sim))
            log.debug(f"Semantic similarity: {semantic_sim:.3f}")
        except Exception as e:
            log.warning(f"Semantic evaluation failed: {e}")
    
    # Calculate simple similarity (fallback)
    if method in ['simple', 'hybrid'] or semantic_sim is None:
        try:
            simple_sim = simple_text_similarity(key_processed, student_processed)
            log.debug(f"Simple similarity: {simple_sim:.3f}")
        except Exception as e:
            log.warning(f"Simple evaluation failed: {e}")
            simple_sim = 0.0
    
    # Calculate keyword match
    try:
        keyword_match = _calculate_keyword_match_score(student_processed, key_processed)
        log.debug(f"Keyword match: {keyword_match:.3f}")
    except Exception as e:
        log.warning(f"Keyword matching failed: {e}")
        keyword_match = 0.5
    
    # Combine similarities based on method
    if method == 'semantic' and semantic_sim is not None:
        similarity = semantic_sim
        confidence = 0.95
    elif method == 'simple':
        similarity = simple_sim
        confidence = 0.70
    else:  # hybrid
        if semantic_sim is not None:
            # Combine semantic + simple + keyword matching
            similarity = (semantic_sim * 0.6) + (simple_sim * 0.25) + (keyword_match * 0.15)
            confidence = 0.85
        else:
            similarity = (simple_sim * 0.7) + (keyword_match * 0.3)
            confidence = 0.75
    
    # Apply length penalty
    length_penalty = _calculate_length_penalty(student_processed, key_processed)
    similarity = similarity * length_penalty
    
    # Clamp to 0-1
    similarity = max(0.0, min(1.0, similarity))
    sim_percent = round(similarity * 100, 2)
    
    # Generate marks based on similarity
    from config import PLAGIARISM_THRESHOLD
    
    # Scoring brackets (adjustable via config in future)
    if similarity >= 0.90:
        marks = 100
        remark = "Excellent - Comprehensive and accurate answer"
    elif similarity >= 0.80:
        marks = 95
        remark = "Excellent - Very strong similarity to key"
    elif similarity >= 0.70:
        marks = 85
        remark = "Very Good - High similarity with minor differences"
    elif similarity >= 0.60:
        marks = 75
        remark = "Good - Mostly correct with some gaps"
    elif similarity >= 0.50:
        marks = 65
        remark = "Fair - Partially correct answer"
    elif similarity >= 0.40:
        marks = 55
        remark = "Needs Review - Limited accuracy"
    elif similarity >= 0.30:
        marks = 40
        remark = "Weak - Significant gaps in response"
    elif similarity >= 0.15:
        marks = 20
        remark = "Poor - Very limited accuracy"
    else:
        marks = 0
        remark = "No Match - Answer unrelated to key"
    
    # Add confidence note to remark
    if confidence < 0.80:
        remark += " (Low Confidence)"
    
    return marks, sim_percent, remark, confidence

def extract_text_from_file(file_path):
    """
    Extract text from PDF, image, or text file with optimized OCR.
    
    Uses preprocessing for images to improve OCR accuracy:
    - Rotation detection and correction
    - Contrast enhancement
    - Noise reduction
    - Optimized Tesseract configuration
    """
    text = ""
    try:
        if file_path.lower().endswith(".pdf"):
            # PDF extraction
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                page_count = len(reader.pages)
                log.info(f"Extracting text from PDF: {file_path} ({page_count} pages)")
                
                for page_num, page in enumerate(reader.pages):
                    page_text = page.extract_text() or ""
                    text += page_text
                    if page_text.strip():
                        log.debug(f"  Page {page_num + 1}: {len(page_text)} chars extracted")
            
            log.info(f"PDF extraction complete: {len(text)} chars")
            
            # Fallback to OCR if extracted text is empty (scanned PDF)
            if not text.strip():
                log.info("PDF contains no digital text. Attempting OCR fallback using PyMuPDF...")
                try:
                    import fitz  # PyMuPDF
                    from io import BytesIO
                    
                    doc = fitz.open(file_path)
                    ocr_text = []
                    for page_num, page in enumerate(doc):
                        log.info(f"  Running OCR on PDF page {page_num + 1}/{len(doc)}...")
                        pix = page.get_pixmap(dpi=150)
                        img_data = pix.tobytes("png")
                        img = Image.open(BytesIO(img_data))
                        
                        custom_config = r'--psm 3 --oem 1 -l eng'
                        page_ocr = pytesseract.image_to_string(img, config=custom_config)
                        ocr_text.append(page_ocr)
                    text = "\n".join(ocr_text)
                    log.info(f"OCR fallback complete: {len(text)} chars extracted from PDF")
                except Exception as ocr_err:
                    log.warning(f"OCR fallback failed: {ocr_err}")
        elif file_path.lower().endswith((".png", ".jpg", ".jpeg")):
            # Image extraction with preprocessing
            log.info(f"Processing image: {file_path}")
            
            # Check cache first
            if file_path in _image_cache:
                log.debug(f"  ✓ Using cached preprocessed image")
                img = _image_cache[file_path]
            else:
                # Optimize image size first
                _optimize_image_size(file_path)
                
                # Preprocess image for better OCR
                img = preprocess_image(file_path)
                _image_cache[file_path] = img
                log.debug(f"  ✓ Image cached for potential reuse")
            
            # OCR with optimized configuration
            # psm (page segmentation mode):
            #   3 = Fully automatic
            #   6 = Assume single uniform block of text
            # oem (OCR engine mode):
            #   1 = LSTM only
            #   3 = Legacy + LSTM
            custom_config = r'--psm 6 --oem 1 -l eng'
            text = pytesseract.image_to_string(img, config=custom_config)
            log.info(f"Image OCR complete: {file_path} ({len(text)} chars)")
            
        elif file_path.lower().endswith(".txt"):
            # Plain text
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            log.info(f"Extracted text from TXT: {file_path} ({len(text)} chars)")
            
        elif file_path.lower().endswith((".docx", ".doc")):
            # DOCX extraction
            try:
                from docx import Document
                doc = Document(file_path)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                log.info(f"Extracted text from DOCX: {file_path} ({len(text)} chars)")
            except Exception as e:
                log.warning(f"DOCX parsing failed, attempting text-based fallback: {e}")
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                    
    except Exception as e:
        log.error(f"Error extracting text from {file_path}: {e}")
        
    return text.strip()

def parse_question_answers(text):
    """
    Parses a text block into individual question/answer segments using common markers:
    e.g., Q1, Q2, Question 1, Answer 1, Ans 1, 1), 2)
    Returns a dictionary of {question_num: answer_text} where question_num is an integer.
    """
    pattern = re.compile(
        r'(?:(?:^|\n)\s*)'                      # Start of line or text
        r'(?:'                                  # Optional prefix group
            r'(?:[Qq]uestion|[Qq]|[Aa]nswer|[Aa]ns|[Aa])' # Matches Q, Question, Answer, Ans, A
            r'(?:\.|\s+)?'                      # Optional dot or spacing
        r')?'                                   # Prefix optional
        r'(\d+)'                                # Question number (Group 1)
        r'(?:\.|\)|:|\s|-|\])+'                 # Separator chars
    )
    
    matches = list(pattern.finditer(text))
    if not matches:
        return {}
        
    qa_map = {}
    for i in range(len(matches)):
        start = matches[i].end()
        end = matches[i+1].start() if i + 1 < len(matches) else len(text)
        
        q_num = int(matches[i].group(1))
        q_text = text[start:end].strip()
        
        if q_num in qa_map:
            qa_map[q_num] += "\n" + q_text
        else:
            qa_map[q_num] = q_text
            
    return qa_map

def evaluate_and_check_plagiarism(answerkey_path, answers_folder, paper_questions=None):
    """
    Evaluate students and check for plagiarism among them.
    Supports question-by-question grading if paper_questions is provided.
    """
    from config import PLAGIARISM_THRESHOLD
    
    log.info(f"Starting evaluation with plagiarism threshold: {PLAGIARISM_THRESHOLD}")
    
    # 1. Fetch/Extract Answer Key information
    answerkey_text = ""
    key_qa = {}
    if not paper_questions:
        if not answerkey_path:
            raise ValueError("Either a generated question paper or an uploaded answer key file is required.")
        answerkey_text = extract_text_from_file(answerkey_path)
        if not answerkey_text.strip():
            log.error("Answer key file is empty")
            raise ValueError(
                "Answer key has no extractable text. Please ensure the uploaded file contains digital text, "
                "or install Tesseract OCR on the system to enable image text extraction."
            )
        # Try parsing answer key into individual questions
        key_qa = parse_question_answers(answerkey_text)
    else:
        # Build answerkey_text by combining model answers from paper_questions
        combined_answers = []
        for q in paper_questions:
            q_details = q.get("answer_key_details", {})
            ans = q_details.get("model_answer", q.get("answer", ""))
            if ans:
                combined_answers.append(ans)
        answerkey_text = "\n\n".join(combined_answers)

    results = []
    student_texts = {}

    # 2. Gather student files and extract text
    files = os.listdir(answers_folder)
    log.info(f"Found {len(files)} student files")
    
    for file in files:
        path = os.path.join(answers_folder, file)
        text = extract_text_from_file(path)
        if not text.strip():
            parts = file.split('_')
            student_name = parts[0] if parts else file
            student_name_display = student_name.replace('_', ' ')
            raise ValueError(
                f"Student answer sheet for '{student_name_display}' has no extractable text. "
                f"Ensure the PDF contains digital text, or install Tesseract OCR."
            )
        student_texts[file] = text

    # 3. Evaluate student answers
    log.info("Evaluating student answers against key")
    for file, text in student_texts.items():
        student_qa = parse_question_answers(text)
        
        # Scenario A: Structured Question Paper from DB is selected
        if paper_questions:
            q_evals = []
            total_possible = 0
            total_earned = 0
            
            if student_qa:
                # Question-by-question matching
                for idx, q in enumerate(paper_questions):
                    q_idx = idx + 1
                    q_max_marks = float(q.get("marks", 1))
                    total_possible += q_max_marks
                    
                    q_details = q.get("answer_key_details", {})
                    # Ensure details exist
                    if not q_details or not q_details.get("model_answer"):
                        q_details = _enrich_question_details(q.get("question", ""), q.get("answer", ""), q_max_marks)
                        
                    q_student_answer = student_qa.get(q_idx, "")
                    
                    if q_student_answer.strip():
                        eval_details = evaluate_answer_components(q_student_answer, q_max_marks, q_details)
                    else:
                        eval_details = evaluate_answer_components("", q_max_marks, q_details)
                        
                    q_earned_marks = eval_details["earned_marks"]
                    total_earned += q_earned_marks
                    
                    q_evals.append({
                        "question_num": q_idx,
                        "question": q.get("question", ""),
                        "max_marks": q_max_marks,
                        "earned_marks": q_earned_marks,
                        "similarity": eval_details["similarity"],
                        "student_answer": q_student_answer,
                        "model_answer": q_details.get("model_answer"),
                        "feedback": eval_details["feedback"],
                        "confidence": eval_details["confidence"],
                        "correctness_score": eval_details["correctness_score"],
                        "concept_score": eval_details["concept_score"],
                        "keyword_score": eval_details["keyword_score"],
                        "completeness_score": eval_details["completeness_score"],
                        "concepts_details": eval_details["concepts_details"],
                        "keywords_details": eval_details["keywords_details"],
                        "deduction_reason": eval_details["deduction_reason"]
                    })
            else:
                # Fallback: Compare full text with combined answers if no Q1/Q2 markers found
                combined_key = "\n\n".join([q.get("answer_key_details", {}).get("model_answer", q.get("answer", "")) for q in paper_questions])
                q_details = _enrich_question_details("Full Question Paper", combined_key, sum(float(qd.get("marks", 1)) for qd in paper_questions))
                
                eval_details = evaluate_answer_components(text, sum(float(qd.get("marks", 1)) for qd in paper_questions), q_details)
                total_possible = sum(float(qd.get("marks", 1)) for qd in paper_questions)
                total_earned = eval_details["earned_marks"]
                
                for idx, q in enumerate(paper_questions):
                    q_idx = idx + 1
                    q_max_marks = float(q.get("marks", 1))
                    q_details_q = q.get("answer_key_details", {})
                    if not q_details_q or not q_details_q.get("model_answer"):
                        q_details_q = _enrich_question_details(q.get("question", ""), q.get("answer", ""), q_max_marks)
                        
                    # Proportional fraction of the overall grade
                    q_prop_earned = round((eval_details["earned_marks"] / total_possible) * q_max_marks, 2) if total_possible > 0 else 0.0
                    
                    q_evals.append({
                        "question_num": q_idx,
                        "question": q.get("question", ""),
                        "max_marks": q_max_marks,
                        "earned_marks": q_prop_earned,
                        "similarity": eval_details["similarity"],
                        "student_answer": "(Full sheet compared)",
                        "model_answer": q_details_q.get("model_answer"),
                        "feedback": "Graded using overall text fallback.",
                        "confidence": eval_details["confidence"],
                        "correctness_score": round(q_prop_earned * 0.4, 2),
                        "concept_score": round(q_prop_earned * 0.3, 2),
                        "keyword_score": round(q_prop_earned * 0.2, 2),
                        "completeness_score": round(q_prop_earned * 0.1, 2),
                        "concepts_details": [],
                        "keywords_details": [],
                        "deduction_reason": eval_details["deduction_reason"]
                    })
            
            avg_similarity = round(sum(qe["similarity"] for qe in q_evals) / len(q_evals), 2) if q_evals else 0.0
            avg_confidence = round(sum(qe["confidence"] for qe in q_evals) / len(q_evals), 2) if q_evals else 0.75
            scaled_score = round((total_earned / total_possible) * 100.0, 2) if total_possible > 0 else 0.0
            grade = _calculate_grade(scaled_score)
            
            results.append({
                "filename": file,
                "similarity": avg_similarity,
                "marks": scaled_score,
                "grade": grade,
                "remark": f"Graded {len(q_evals)} questions. Score: {total_earned}/{total_possible}",
                "confidence": avg_confidence,
                "extracted_text": text,
                "question_evaluations": q_evals,
                "is_flagged": False
            })

        # Scenario B: Uploaded Answer Key has question markers (Q1, Q2) and so does Student text
        elif key_qa and student_qa and len(set(key_qa.keys()).intersection(set(student_qa.keys()))) > 0:
            common_keys = sorted(list(set(key_qa.keys()).intersection(set(student_qa.keys()))))
            q_evals = []
            total_earned = 0
            total_possible = len(common_keys) * 10.0 # Assign 10 marks per matched question by default
            
            for q_idx in common_keys:
                q_model = key_qa[q_idx]
                q_student = student_qa[q_idx]
                
                q_details = _enrich_question_details(f"Question {q_idx}", q_model, 10.0)
                eval_details = evaluate_answer_components(q_student, 10.0, q_details)
                q_earned = eval_details["earned_marks"]
                total_earned += q_earned
                
                q_evals.append({
                    "question_num": q_idx,
                    "question": f"Question {q_idx} (Extracted)",
                    "max_marks": 10.0,
                    "earned_marks": q_earned,
                    "similarity": eval_details["similarity"],
                    "student_answer": q_student,
                    "model_answer": q_model,
                    "feedback": eval_details["feedback"],
                    "confidence": eval_details["confidence"],
                    "correctness_score": eval_details["correctness_score"],
                    "concept_score": eval_details["concept_score"],
                    "keyword_score": eval_details["keyword_score"],
                    "completeness_score": eval_details["completeness_score"],
                    "concepts_details": eval_details["concepts_details"],
                    "keywords_details": eval_details["keywords_details"],
                    "deduction_reason": eval_details["deduction_reason"]
                })
                
            avg_similarity = round(sum(qe["similarity"] for qe in q_evals) / len(q_evals), 2)
            avg_confidence = round(sum(qe["confidence"] for qe in q_evals) / len(q_evals), 2)
            scaled_score = round((total_earned / total_possible) * 100.0, 2)
            grade = _calculate_grade(scaled_score)
            
            results.append({
                "filename": file,
                "similarity": avg_similarity,
                "marks": scaled_score,
                "grade": grade,
                "remark": f"Graded {len(q_evals)} mapped questions from file. Score: {total_earned}/{total_possible}",
                "confidence": avg_confidence,
                "extracted_text": text,
                "question_evaluations": q_evals,
                "is_flagged": False
            })

        # Scenario C: Fallback to full document matching (Standard method)
        else:
            q_details = _enrich_question_details("Full Answer Key", answerkey_text, 100.0)
            eval_details = evaluate_answer_components(text, 100.0, q_details)
            scaled_score = eval_details["earned_marks"]
            grade = _calculate_grade(scaled_score)
            
            results.append({
                "filename": file,
                "similarity": eval_details["similarity"],
                "marks": scaled_score,
                "grade": grade,
                "remark": eval_details["feedback"],
                "confidence": eval_details["confidence"],
                "extracted_text": text,
                "question_evaluations": [{
                    "question_num": 1,
                    "question": "Full Sheet Evaluation",
                    "max_marks": 100.0,
                    "earned_marks": eval_details["earned_marks"],
                    "similarity": eval_details["similarity"],
                    "student_answer": text,
                    "model_answer": answerkey_text,
                    "feedback": eval_details["feedback"],
                    "confidence": eval_details["confidence"],
                    "correctness_score": eval_details["correctness_score"],
                    "concept_score": eval_details["concept_score"],
                    "keyword_score": eval_details["keyword_score"],
                    "completeness_score": eval_details["completeness_score"],
                    "concepts_details": eval_details["concepts_details"],
                    "keywords_details": eval_details["keywords_details"],
                    "deduction_reason": eval_details["deduction_reason"]
                }],
                "is_flagged": False
            })

    # 4. AI Content Detection Check
    log.info("Running AI content detection checks")
    ai_flags = {}
    for filename, text in student_texts.items():
        ai_score, detected_markers = _detect_ai_content(text)
        if ai_score >= 0.85:
            ai_flags[filename] = {
                "score": ai_score,
                "markers": detected_markers,
                "reason": f"AI-generated content confidence ({int(ai_score * 100)}%) exceeds threshold (85%). Matched markers: {', '.join([f'\"{m}\"' for m in detected_markers[:3]])}."
            }

    # 5. Suspicious Answer Patterns Check (Self-Duplicates)
    log.info("Running suspicious answer pattern checks (self-duplicates)")
    pattern_flags = {}
    for filename, text in student_texts.items():
        student_qa = parse_question_answers(text)
        self_duplicates = _check_student_self_duplicates(student_qa)
        if self_duplicates:
            reasons = []
            for dup in self_duplicates:
                reasons.append(f"Suspicious pattern: Identical response copied across Question {dup['q1']} and Question {dup['q2']} ({dup['similarity']}% similarity).")
            pattern_flags[filename] = {
                "self_duplicates": self_duplicates,
                "reasons": reasons
            }

    # 6. Plagiarism Detection (optimized)
    log.info("Starting plagiarism detection")
    
    # Query historical results from database for cross-batch plagiarism check
    historical_texts = {}
    try:
        from flask import current_app
        if current_app:
            from models import Result
            from flask_jwt_extended import get_jwt_identity
            user_identity = get_jwt_identity()
            
            query = Result.query
            if user_identity:
                query = query.filter_by(user_id=int(user_identity))
                
            historical_results = query.all()
            for r in historical_results:
                if r.extracted_text and r.extracted_text.strip():
                    # Format key as Historical_<id>_<student_name>
                    key = f"Historical_{r.id}_{r.student_name}"
                    historical_texts[key] = r.extracted_text
            log.info(f"Loaded {len(historical_texts)} historical submissions for cross-batch plagiarism check")
    except Exception as e:
        log.warning(f"Could not load historical results for cross-batch plagiarism: {str(e)}")

    # Prepare comparison texts (include Model Answer and historical texts if available)
    comparison_texts = student_texts.copy()
    if answerkey_text.strip():
        comparison_texts["Model_Answer"] = answerkey_text
        
    for k, v in historical_texts.items():
        comparison_texts[k] = v
        
    plagiarism_pairs = _calculate_plagiarism_pairs_optimized(
        comparison_texts,
        threshold=PLAGIARISM_THRESHOLD,
        max_results=None
    )
    
    plagiarism_map = {}
    for file1, file2, similarity in plagiarism_pairs:
        if file1 == "Model_Answer" and file2 == "Model_Answer":
            continue
            
        # We only want pairs where at least one of them is in the current batch (student_texts).
        is_file1_new = file1 in student_texts
        is_file2_new = file2 in student_texts
        
        if not is_file1_new and not is_file2_new:
            continue
            
        if file1 == "Model_Answer":
            if file2 not in plagiarism_map:
                plagiarism_map[file2] = []
            plagiarism_map[file2].append(("Model_Answer", similarity))
        elif file2 == "Model_Answer":
            if file1 not in plagiarism_map:
                plagiarism_map[file1] = []
            plagiarism_map[file1].append(("Model_Answer", similarity))
        elif file1.startswith("Historical_"):
            if file2 not in plagiarism_map:
                plagiarism_map[file2] = []
            plagiarism_map[file2].append((file1, similarity))
        elif file2.startswith("Historical_"):
            if file1 not in plagiarism_map:
                plagiarism_map[file1] = []
            plagiarism_map[file1].append((file2, similarity))
        else:
            if file1 not in plagiarism_map:
                plagiarism_map[file1] = []
            if file2 not in plagiarism_map:
                plagiarism_map[file2] = []
            plagiarism_map[file1].append((file2, similarity))
            plagiarism_map[file2].append((file1, similarity))
            
    # Update results with plagiarism and flagging warnings
    for r in results:
        filename = r["filename"]
        matches_list = []
        is_plagiarism_flagged = False
        reasons_list = []
        
        # 1. Plagiarism check
        if filename in plagiarism_map:
            is_plagiarism_flagged = True
            pairs_info = plagiarism_map[filename]
            plagiarism_details = []
            for paired_file, sim_score in pairs_info:
                if paired_file == "Model_Answer":
                    matched_to_display = "Model Answer"
                    reasons_list.append(f"Similarity to Model Answer ({sim_score*100:.1f}%) exceeds threshold ({int(PLAGIARISM_THRESHOLD * 100)}%).")
                    matches_list.append({
                        "matched_to": matched_to_display,
                        "type": "model_answer",
                        "similarity": round(sim_score * 100, 2),
                        "reason": f"Similarity exceeds threshold ({int(PLAGIARISM_THRESHOLD * 100)}%)."
                    })
                    plagiarism_details.append(f"{matched_to_display} ({sim_score*100:.1f}%)")
                elif paired_file.startswith("Historical_"):
                    parts = paired_file.split("_", 2)
                    hist_name = parts[2] if len(parts) >= 3 else paired_file
                    matched_to_display = f"{hist_name} (Historical)"
                    reasons_list.append(f"Similarity to historical submission of student {hist_name} ({sim_score*100:.1f}%) exceeds threshold ({int(PLAGIARISM_THRESHOLD * 100)}%).")
                    
                    # Try to fetch actual student_filename of the historical result so compare button works
                    hist_filename = hist_name
                    try:
                        from models import Result
                        hist_res = Result.query.get(int(parts[1]))
                        if hist_res:
                            hist_filename = hist_res.student_filename
                    except:
                        pass
                        
                    matches_list.append({
                        "matched_to": hist_filename,
                        "type": "student",
                        "similarity": round(sim_score * 100, 2),
                        "reason": f"Similarity to historical submission of {hist_name} exceeds threshold ({int(PLAGIARISM_THRESHOLD * 100)}%)."
                    })
                    plagiarism_details.append(f"{hist_name} [Historical] ({sim_score*100:.1f}%)")
                else:
                    matched_to_display = paired_file
                    reasons_list.append(f"Similarity to student {matched_to_display} ({sim_score*100:.1f}%) exceeds threshold ({int(PLAGIARISM_THRESHOLD * 100)}%).")
                    if r.get("marks", 0) < 60:
                        reasons_list.append(f"Suspicious pattern: High answer overlap with student {matched_to_display} ({sim_score*100:.1f}%) but low score ({r.get('marks')}%).")
                    
                    matches_list.append({
                        "matched_to": matched_to_display,
                        "type": "student",
                        "similarity": round(sim_score * 100, 2),
                        "reason": f"Similarity exceeds threshold ({int(PLAGIARISM_THRESHOLD * 100)}%)."
                    })
                    plagiarism_details.append(f"{matched_to_display} ({sim_score*100:.1f}%)")
            
            if plagiarism_details:
                details_str = ", ".join(plagiarism_details)
                r["remark"] += f" ⚠️ PLAGIARISM DETECTED with: {details_str}"
            r["plagiarism_matches"] = pairs_info
            log.warning(f"Flagged plagiarism: {filename} matched with {len(pairs_info)} other(s)")
            
        # 2. AI check
        has_ai_flag = False
        ai_details = None
        if filename in ai_flags:
            has_ai_flag = True
            ai_details = ai_flags[filename]
            reasons_list.append(ai_details["reason"])
            r["remark"] += f" ⚠️ AI-CONTENT DETECTED ({int(ai_details['score']*100)}% confidence)"
            
        # 3. Pattern check (Self-Duplicates)
        has_pattern_flag = False
        pattern_details = None
        if filename in pattern_flags:
            has_pattern_flag = True
            pattern_details = pattern_flags[filename]
            reasons_list.extend(pattern_details["reasons"])
            r["remark"] += f" ⚠️ SUSPICIOUS PATTERN DETECTED"
            
        # Overall flag decision
        r["is_flagged"] = is_plagiarism_flagged or has_ai_flag or has_pattern_flag
        
        # Populate flag_details structure
        r["flag_details"] = {
            "is_flagged": r["is_flagged"],
            "reasons": reasons_list,
            "ai_details": ai_details,
            "pattern_details": pattern_details,
            "review_status": "Pending Review",
            "reviewer_comments": None
        }
        
        r["plagiarism_details"] = {
            "is_flagged": is_plagiarism_flagged,
            "threshold": int(PLAGIARISM_THRESHOLD * 100),
            "matches": matches_list
        }
    
    log.info(f"Plagiarism & Flag checks complete: {len(plagiarism_pairs)} pairs flagged")
    
    _clear_image_cache()
    _clear_embedding_cache()
    
    return results