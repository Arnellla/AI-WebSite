import os
import re

from nltk.corpus import stopwords
from requests.compat import chardet
from sklearn.feature_extraction.text import TfidfVectorizer
from rapidfuzz import fuzz
import numpy as np



MAX_CHARS = 240000

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
    return text.strip().lower()

def extract_text(txt_path):
    with open(txt_path, 'rb') as file:
        raw_data = file.read()

    result = chardet.detect(raw_data)
    encoding = result['encoding']

    try:
        text = raw_data.decode(encoding)
    except (UnicodeDecodeError, TypeError):
        raise Exception(f"Не удалось декодировать файл с кодировкой: {encoding} в {txt_path}")

    cleaned_text = clean_text(text)
    return cleaned_text

def vectorize_text(texts):
    vectorizer = TfidfVectorizer(stop_words=stopwords.words('russian'))
    text_matrix = vectorizer.fit_transform(texts)
    return vectorizer, text_matrix

def really_most_relevant_text(question, text_matrix, vectorizer, texts):
    question_vec = vectorizer.transform([question])
    similarities = (text_matrix * question_vec.T).toarray().flatten()
    relevant_index = similarities.argmax()
    return texts[relevant_index], relevant_index

def process_txt(folder_path, specific_files=None):
    all_texts = []
    filenames = []

    if specific_files is None:
        specific_files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]

    for filename in specific_files:
        txt_path = os.path.join(folder_path, filename)
        try:
            text = extract_text(txt_path)
            all_texts.append(text)
            filenames.append(filename)
        except Exception as e:
            print(f"Ошибка при обработке файла {filename}: {e}")

    return all_texts, filenames

def vectorize_text_with_filenames(texts, filenames):
    combined_texts = [f"{filename} {text}" for filename, text in zip(filenames, texts)]
    vectorizer = TfidfVectorizer(stop_words=stopwords.words('russian'))
    text_matrix = vectorizer.fit_transform(combined_texts)
    return vectorizer, text_matrix

def get_top_relevant_texts(question, text_matrix, vectorizer, texts, filenames, top_n=3):
    from rapidfuzz import fuzz

    for idx, filename in enumerate(filenames):
        base_filename = os.path.splitext(filename)[0].lower()
        match_score = fuzz.token_set_ratio(base_filename, question.lower())
        if match_score > 80:
            return [texts[idx]], [idx], [filename]

    question_vec = vectorizer.transform([question])
    similarities = (text_matrix * question_vec.T).toarray().flatten()

    filename_scores = [fuzz.partial_ratio(question.lower(), filename.lower()) for filename in filenames]

    similarities_normalized = similarities / np.max(similarities) if np.max(similarities) != 0 else similarities
    filename_scores_normalized = np.array(filename_scores) / 100.0

    combined_scores = similarities_normalized + 0.3 * filename_scores_normalized

    top_indices = combined_scores.argsort()[::-1]
    seen_files = set()
    unique_top_indices = []
    for idx in top_indices:
        base_filename = os.path.splitext(filenames[idx])[0]
        if base_filename not in seen_files:
            seen_files.add(base_filename)
            unique_top_indices.append(idx)
        if len(unique_top_indices) == top_n:
            break

    top_texts = [texts[idx] for idx in unique_top_indices]
    top_filenames = [filenames[idx] for idx in unique_top_indices]
    return top_texts, unique_top_indices, top_filenames



async def split_large_text_file(filepath, output_folder):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(filepath, 'rb') as f:
            content = f.read()
            detected_encoding = chardet.detect(content)['encoding']
            content = content.decode(detected_encoding)

    if len(content) > MAX_CHARS:
        os.remove(filepath)
        for i in range(0, len(content), MAX_CHARS):
            part_content = content[i:i + MAX_CHARS]
            part_filename = f"{os.path.basename(filepath).replace('.txt', '')}_chap{i // MAX_CHARS + 1}.txt"
            with open(os.path.join(output_folder, part_filename), 'w', encoding='utf-8') as part_file:
                part_file.write(part_content)