import streamlit as st
import requests
import base64
import json
import os
import glob
from PIL import Image
import io
import time

# Set up paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, 'images')
OCR_DIR = os.path.join(BASE_DIR, 'OCR')

# Create directories if they don't exist
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(OCR_DIR, exist_ok=True)

# Set page config
st.set_page_config(
    page_title="Resume Analysis API Demo",
    page_icon="📄",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        margin-top: 10px;
    }
    .main {
        padding: 2rem;
    }
    .stMarkdown {
        padding: 1rem;
    }
    .error {
        color: red;
    }
    .success {
        color: green;
    }
    </style>
""", unsafe_allow_html=True)

# Title and Introduction
st.title("📄 Resume Analysis API Demo")
st.markdown("""
    This application demonstrates two different approaches for analyzing resumes using AI:
    
    1. **Image-based Analysis** (Approach 1)
    2. **OCR-based Analysis** (Approach 2)
    
    Each approach has its own advantages and use cases. Below you'll find detailed information about both methods.
""")

def get_analysis_prompt(user_requirements):
    """Generate the complete analysis prompt combining base criteria with user requirements"""
    base_prompt = '''
    For each provided resume image, evaluate the candidate based on the following criteria:

    1. **Tenure at Previous Companies**: Assess the duration of employment at each company, highlighting instances of long-term commitments (e.g., 5-10 years) and noting any patterns of short-term engagements.

    2. **Job Description Alignment**: Determine how closely the candidate's experience, skills, and qualifications match the specified job description. Identify areas of strong alignment and any gaps.

    3. **Skill Relevance and Proficiency**: Analyze the listed skills, their relevance to the job role, and the proficiency level indicated by the candidate's experience.

    4. **Career Progression**: Examine the trajectory of the candidate's career, noting evidence of growth such as promotions, increased responsibilities, or diversification of skills.

    5. **Educational Background**: Review the candidate's educational qualifications, considering the relevance of degrees, certifications, and continuous learning efforts to the job role.

    6. **Stability and Commitment**: Beyond tenure, assess overall stability by evaluating the frequency of job changes and any patterns that may indicate a lack of commitment.

    7. **Cultural Fit Indicators**: Identify any information suggesting the candidate's alignment with the company's values and culture, such as participation in relevant projects, initiatives, or organizations.
    '''
    
    if user_requirements:
        return f"{base_prompt}\n\nAdditional Requirements:\n{user_requirements}"
    return base_prompt

def analyze_resumes(payload, endpoint, approach_name):
    """Helper function to analyze resumes and show detailed process"""
    st.subheader(f"Analysis Process - {approach_name}")
    
    # Show request details
    with st.expander("View Request Details"):
        st.json(payload)
    
    # Send request with timeout and retries
    max_retries = 3
    retry_delay = 5  # seconds
    current_try = 0
    
    while current_try < max_retries:
        try:
            with st.spinner(f"Attempt {current_try + 1}/{max_retries}: Sending request to API..."):
                # Configure session with longer timeout
                session = requests.Session()
                session.timeout = (60, 300)  # (connect timeout, read timeout) in seconds
                
                # Send request
                start_time = time.time()
                response = session.post(endpoint, json=payload)
                end_time = time.time()
                
                # Show response details
                with st.expander("View Response Details"):
                    st.write(f"Status Code: {response.status_code}")
                    st.write(f"Response Time: {end_time - start_time:.2f} seconds")
                    st.write("Response Headers:")
                    st.json(dict(response.headers))
                    
                    if response.status_code == 200:
                        st.write("Response Body:")
                        st.json(response.json())
                    else:
                        st.error(f"Error Response: {response.text}")
                
                # Handle response
                if response.status_code == 200:
                    result = response.json()
                    st.success("Analysis completed successfully!")
                    return result.get("analysis")
                else:
                    error_msg = response.json().get('error', 'Unknown error occurred')
                    st.error(f"Error: {error_msg}")
                    if current_try < max_retries - 1:
                        st.warning(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    current_try += 1
                    
        except requests.exceptions.Timeout:
            st.error(f"Request timed out on attempt {current_try + 1}/{max_retries}")
            if current_try < max_retries - 1:
                st.warning(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            current_try += 1
            
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed on attempt {current_try + 1}/{max_retries}: {str(e)}")
            if current_try < max_retries - 1:
                st.warning(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            current_try += 1
            
        except Exception as e:
            st.error(f"An unexpected error occurred on attempt {current_try + 1}/{max_retries}: {str(e)}")
            if current_try < max_retries - 1:
                st.warning(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            current_try += 1
    
    st.error("All retry attempts failed. Please try again later.")
    return None

def load_images_from_directory():
    """Load all images from the images directory"""
    images = []
    supported_formats = ["jpg", "jpeg", "png", "webp", "heic"]
    
    for ext in supported_formats:
        pattern = os.path.join(IMAGES_DIR, f"*.{ext}")
        images.extend(glob.glob(pattern))
    
    return sorted(images)  # Sort for consistent ordering

def load_ocr_files():
    """Load all OCR JSON files"""
    pattern = os.path.join(OCR_DIR, "*.json")
    return sorted(glob.glob(pattern))  # Sort for consistent ordering

# Create tabs for different sections
tab1, tab2, tab3 = st.tabs(["Approach 1: Image-based", "Approach 2: OCR-based", "API Documentation"])

# Approach 1: Image-based Analysis
with tab1:
    st.header("Approach 1: Image-based Analysis")
    st.markdown("""
        This approach processes resume images directly using computer vision and AI. It's ideal when you have scanned PDFs or images of resumes.
        
        ### How it works:
        1. Images are converted to base64 format
        2. The API processes the images using advanced AI models
        3. Returns detailed analysis of each resume
        
        ### Advantages:
        - Works with any image format (JPG, PNG, WEBP, HEIC)
        - No preprocessing required
        - Handles complex layouts
    """)
    
    # User requirements input
    st.subheader("Analysis Requirements")
    user_requirements = st.text_area(
        "Enter your specific requirements for resume analysis (optional)",
        placeholder="Example: Looking for candidates with 5+ years of Python experience and experience in cloud platforms like AWS or Azure.",
        height=100,
        key="image_based_requirements"
    )
    
    # Show existing images
    st.subheader("Sample Resumes")
    images = load_images_from_directory()
    
    if images:
        cols = st.columns(3)
        for idx, img_path in enumerate(images):
            with cols[idx % 3]:
                try:
                    image = Image.open(img_path)
                    st.image(image, caption=os.path.basename(img_path))
                except Exception as e:
                    st.error(f"Error loading image {img_path}: {str(e)}")
        
        # Add Analyze button for default images
        if st.button("Analyze Default Resumes"):
            with st.spinner("Processing images..."):
                # Convert images to base64
                base64_images = []
                for img_path in images:
                    try:
                        with open(img_path, "rb") as file:
                            base64_data = base64.b64encode(file.read()).decode('utf-8')
                            base64_images.append({
                                "mime_type": f"image/{os.path.splitext(img_path)[1][1:].lower()}",
                                "data": base64_data
                            })
                    except Exception as e:
                        st.error(f"Error processing {img_path}: {e}")
                
                if base64_images:
                    # Prepare payload with user requirements
                    payload = {
                        "images": base64_images,
                        "prompt": get_analysis_prompt(user_requirements)
                    }
                    
                    # Analyze resumes
                    result = analyze_resumes(payload, 'https://approach1.onrender.com/analyze', "Image-based Analysis")
                    
    else:
        st.info(f"No images found in {IMAGES_DIR}")
    
    # File uploader
    st.subheader("Upload New Resumes")
    uploaded_files = st.file_uploader(
        "Choose resume images", 
        type=["jpg", "jpeg", "png", "webp", "heic"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        st.subheader("Analysis Results")
        with st.spinner("Processing uploaded images..."):
            # Convert images to base64
            images = []
            for file in uploaded_files:
                base64_data = base64.b64encode(file.read()).decode('utf-8')
                images.append({
                    "mime_type": file.type,
                    "data": base64_data
                })
            
            # Prepare payload with user requirements
            payload = {
                "images": images,
                "prompt": get_analysis_prompt(user_requirements)
            }
            
            # Analyze resumes
            result = analyze_resumes(payload, 'https://approach1.onrender.com/analyze', "Image-based Analysis")
            if result:
                st.subheader("Analysis Results")
                st.json(result)

# Approach 2: OCR-based Analysis
with tab2:
    st.header("Approach 2: OCR-based Analysis")
    st.markdown("""
        This approach uses OCR (Optical Character Recognition) to extract text from resumes first, then analyzes the structured data.
        
        ### How it works:
        1. OCR extracts text from resumes
        2. Text is structured into JSON format
        3. API analyzes the structured data
        
        ### Advantages:
        - More accurate text extraction
        - Better handling of structured data
        - Faster processing for text-heavy resumes
    """)
    
    # User requirements input
    st.subheader("Analysis Requirements")
    user_requirements = st.text_area(
        "Enter your specific requirements for resume analysis (optional)",
        placeholder="Example: Looking for candidates with 5+ years of Python experience and experience in cloud platforms like AWS or Azure.",
        height=100,
        key="ocr_based_requirements"
    )
    
    # Show OCR data
    st.subheader("Sample OCR Data")
    ocr_files = load_ocr_files()
    
    if ocr_files:
        with st.expander("View OCR Data"):
            for file_path in ocr_files:
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        st.write(f"File: {os.path.basename(file_path)}")
                        st.json(data)
                except Exception as e:
                    st.error(f"Error loading {file_path}: {e}")
    else:
        st.info(f"No OCR files found in {OCR_DIR}")
    
    # Process OCR data
    if st.button("Analyze OCR Data"):
        with st.spinner("Loading OCR data..."):
            ocr_list = []
            for file_path in ocr_files:
                try:
                    with open(file_path, 'r') as f:
                        ocr_list.append(json.load(f))
                except Exception as e:
                    st.error(f"Error loading {file_path}: {e}")
            
            if ocr_list:
                # Prepare payload with user requirements
                payload = {
                    "ocr_list": ocr_list,
                    "prompt": get_analysis_prompt(user_requirements)
                }
                
                # Analyze resumes
                result = analyze_resumes(payload, 'https://approach2.onrender.com/analyze', "OCR-based Analysis")


# API Documentation
with tab3:
    st.header("API Documentation")
    
    st.markdown("""
        ### Approach 1: Image-based API
        
        **Endpoint:** `https://approach1.onrender.com/analyze`
        
        **Method:** POST
        
        **Request Format:**
        ```json
        {
            "images": [
                {
                    "mime_type": "image/jpeg",
                    "data": "base64_encoded_image_data"
                }
            ],
            "prompt": "your_analysis_prompt"
        }
        ```
        
        **Response Format:**
        ```json
        {
            "analysis": [
                {
                    "Candidate ID": "001",
                    "JD Match Percentage": "85%",
                    "Missing Keywords": ["Python", "Machine Learning"],
                    "Profile Summary": "..."
                }
            ]
        }
        ```
        
        ### Approach 2: OCR-based API
        
        **Endpoint:** `https://approach2.onrender.com/analyze`
        
        **Method:** POST
        
        **Request Format:**
        ```json
        {
            "ocr_list": [
                {
                    "text": "extracted_text",
                    "metadata": {
                        "filename": "resume1.pdf",
                        "pages": 1
                    }
                }
            ],
            "prompt": "your_analysis_prompt"
        }
        ```
        
        **Response Format:**
        ```json
        {
            "analysis": [
                {
                    "Candidate ID": "001",
                    "JD Match Percentage": "85%",
                    "Missing Keywords": ["Python", "Machine Learning"],
                    "Profile Summary": "..."
                }
            ]
        }
        ```
        
        ### Implementation Example
        
        ```python
        # Approach 1: Image-based
        import requests
        import base64
        
        def analyze_resume_image(image_path):
            with open(image_path, "rb") as file:
                base64_data = base64.b64encode(file.read()).decode('utf-8')
            
            payload = {
                "images": [{
                    "mime_type": "image/jpeg",
                    "data": base64_data
                }],
                "prompt": "your_analysis_prompt"
            }
            
            response = requests.post('https://approach1.onrender.com/analyze', json=payload)
            return response.json()
        
        # Approach 2: OCR-based
        import json
        
        def analyze_resume_ocr(ocr_data):
            payload = {
                "ocr_list": [ocr_data],
                "prompt": "your_analysis_prompt"
            }
            
            response = requests.post('https://approach2.onrender.com/analyze', json=payload)
            return response.json()
        ```
    """) 
