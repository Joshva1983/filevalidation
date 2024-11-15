
# Final Streamlit App Code for Text Analysis with All Options and Features

import streamlit as st
import pandas as pd
import re
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import KMeans
from rake_nltk import Rake
from keybert import KeyBERT
from wordcloud import WordCloud
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk
import yake

nltk.download('stopwords')
nltk.download('punkt')

# Preprocessing Functions
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    tokens = word_tokenize(text)
    tokens = [word for word in tokens if word not in stopwords.words('english')]
    return ' '.join(tokens)

# Deduplication Function
def deduplicate_phrases(phrases):
    return list(set(phrases))

# Frequency Analysis
def perform_frequency_analysis(data, ngram_range=(1, 3)):
    vectorizer = CountVectorizer(ngram_range=ngram_range)
    X = vectorizer.fit_transform(data)
    freqs = zip(vectorizer.get_feature_names_out(), X.sum(axis=0).tolist()[0])
    sorted_freqs = sorted(freqs, key=lambda x: x[1], reverse=True)
    return pd.DataFrame(sorted_freqs, columns=['Phrase', 'Frequency'])

# Keyphrase Extraction
def perform_keyphrase_extraction(data, method='yake', ngram_range=(1, 3)):
    phrases = []
    if method == 'yake':
        kw_extractor = yake.KeywordExtractor(n=ngram_range[1])
        for text in data:
            keywords = kw_extractor.extract_keywords(text)
            phrases.extend([kw[0] for kw in keywords])
    elif method == 'rake':
        rake = Rake()
        for text in data:
            rake.extract_keywords_from_text(text)
            phrases.extend(rake.get_ranked_phrases())
    elif method == 'keybert':
        kw_model = KeyBERT()
        for text in data:
            keywords = kw_model.extract_keywords(text, stop_words='english', top_n=5)
            phrases.extend([kw[0] for kw in keywords])
    return pd.DataFrame(deduplicate_phrases(phrases), columns=['Phrase'])

# Clustering
def perform_clustering(data, n_clusters=5):
    vectorizer = CountVectorizer()
    X = vectorizer.fit_transform(data)
    model = KMeans(n_clusters=n_clusters)
    model.fit(X)
    phrases = [vectorizer.get_feature_names_out()[i] for i in model.cluster_centers_.argsort()[:, -1]]
    return pd.DataFrame(deduplicate_phrases(phrases), columns=['Phrase'])

# Generate Phrase Cloud
def generate_phrase_cloud(phrases):
    text = ' '.join(phrases)
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    return wordcloud

# Streamlit App
st.title("Advanced Text Analysis with Progress Tracking")

uploaded_file = st.file_uploader("Upload your file (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:
    st.write("Data preview:")
    data = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    st.dataframe(data.head())

    # Button to Start Analysis
    if st.button("Run Analysis"):
        with st.spinner("Processing..."):
            # Preprocess and deduplicate
            data['Processed_Text'] = data['LL_TEXT'].apply(preprocess_text)
            data_dedup = data.drop_duplicates(subset=['Processed_Text'])
            
            # Frequency Analysis
            freq_df = perform_frequency_analysis(data_dedup['Processed_Text'])
            st.subheader("Frequency Analysis")
            st.dataframe(freq_df.head(10))
            
            # Keyphrase Extraction
            keyphrase_df = perform_keyphrase_extraction(data_dedup['Processed_Text'])
            st.subheader("Keyphrase Extraction")
            st.dataframe(keyphrase_df.head(10))
            
            # Clustering
            cluster_df = perform_clustering(data_dedup['Processed_Text'])
            st.subheader("Clustering")
            st.dataframe(cluster_df.head(10))

            # Phrase Clouds
            freq_cloud = generate_phrase_cloud(freq_df['Phrase'].tolist()[:100])
            keyphrase_cloud = generate_phrase_cloud(keyphrase_df['Phrase'].tolist()[:100])
            cluster_cloud = generate_phrase_cloud(cluster_df['Phrase'].tolist()[:100])

            st.image(freq_cloud.to_array(), caption="Frequency Phrase Cloud")
            st.image(keyphrase_cloud.to_array(), caption="Keyphrase Extraction Phrase Cloud")
            st.image(cluster_cloud.to_array(), caption="Clustering Phrase Cloud")

            # Save output
            output_file = "/mnt/data/analysis_output.xlsx"
            with pd.ExcelWriter(output_file) as writer:
                freq_df.to_excel(writer, sheet_name='Frequency Analysis', index=False)
                keyphrase_df.to_excel(writer, sheet_name='Keyphrase Extraction', index=False)
                cluster_df.to_excel(writer, sheet_name='Clustering', index=False)

            st.success("Analysis completed successfully!")
            st.markdown(f"[Download the output file](sandbox:/mnt/data/analysis_output.xlsx)")
