
Streamlit LAS Curve Standardizer
is a web application built with Streamlit that allows geoscientists and engineers to upload, visualize, and standardize LAS (Log ASCII Standard) files, making it easier to handle well log data with different log names and tool names. This tool helps to align and unify the names of logging tools used in different wells and data sources, saving time and ensuring consistent data for analysis.
Installation
1. Clone the Repository
You can clone the repository to your local machine by running:

bash
Copy
Edit
git clone https://github.com/yourusername/streamlit-las-curve-standardizer.git
2. Install Dependencies
Make sure you have Python 3.x installed. You will also need Streamlit and other required libraries. Install the dependencies using the following command:

bash
Copy
Edit
pip install -r requirements.txt
Here is the list of dependencies:

Streamlit

lasio

pandas

matplotlib

3. Run the Application
After installing the dependencies, you can run the Streamlit app locally:

bash
Copy
Edit
streamlit run app.py
The app will open in your browser. You can interact with the LAS file standardizer through the web interface.

Usage
Upload LAS Files: Click the "Upload" button to upload your LAS files.

Standardize Log Names: Enter your desired standard log names or use the predefined names.

Visualize Data: The app will display the well logs and allow you to verify the data.

Download Files: You can download each file individually, or click "Download All" to download all files in bulk
