import streamlit as st
import lasio
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO
import zipfile
from io import BytesIO

# --- Page setup ---
st.set_page_config(page_title="LAS Curve Standardizer", layout="wide")
st.title("🛢️ LAS Curve Standardizer and Viewer")

# --- Sidebar ---
st.sidebar.header("📂 Upload and Settings")

uploaded_files = st.sidebar.file_uploader(
    "Upload LAS file(s)", type=["las"], accept_multiple_files=True
)

# --- Dynamic Table for Standard Log Names ---
default_logs = pd.DataFrame({
    'Standard Log Name': ["GR", "NPHI", "RHOB", "DT", "CALI"]
})

st.sidebar.subheader("📝 Enter Standard Log Names")
log_names_df = st.sidebar.data_editor(
    default_logs,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    column_config={
        "Standard Log Name": st.column_config.TextColumn(
            "Standard Log Name",
            required=True,
            help="Enter the desired final log names (e.g., GR, NPHI, RHOB...)"
        ),
    }
)

# Extract standard names list
standard_names = [row["Standard Log Name"].strip().upper() for _, row in log_names_df.iterrows() if row["Standard Log Name"].strip() != ""]

# --- Process Uploaded Files ---
if uploaded_files and standard_names:
    # Read LAS files into dictionary
    las_files = {}
    for uploaded_file in uploaded_files:
        # Read the file correctly
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8", errors="ignore"))
        las = lasio.read(stringio)
        las_files[uploaded_file.name] = las

    # --- Select Well to View ---
    selected_well = st.sidebar.selectbox(
        "Select Well to View",
        list(las_files.keys())
    )

    las = las_files[selected_well]

    st.subheader(f"📄 Curves in `{selected_well}`")

    # Display Curves Before and After Renaming
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ➡️ Original Curves")
        curves_before = [curve.mnemonic for curve in las.curves]
        st.write(curves_before)

    with col2:
        st.markdown("### 🔁 Standardized Curves")
        # --- Apply Standard Renaming ---
        for curve in las.curves:
            original_name = curve.mnemonic.upper()
            for standard in standard_names:
                if standard in original_name:
                    curve.mnemonic = standard
                    break

        curves_after = [curve.mnemonic for curve in las.curves]
        st.write(curves_after)

    st.divider()

    # --- Visualization ---
    st.subheader("📈 Quick Log Viewer")

    available_logs = [curve.mnemonic for curve in las.curves]
    selected_logs = st.multiselect(
        "Select Logs to Plot",
        available_logs,
        default=available_logs[:3] if len(available_logs) >= 3 else available_logs
    )

    if selected_logs:
        fig, ax = plt.subplots(figsize=(8, 12))
        for log in selected_logs:
            if log in las.keys():
                ax.plot(las[log], las.index, label=log)

        ax.set_xlabel("Log Values")
        ax.set_ylabel("Depth (m)")
        ax.invert_yaxis()
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

    st.divider()

    # --- Individual Download Section in Sidebar (with original file name) ---
    st.sidebar.subheader("📥 Download LAS File")

    output_text = StringIO()
    las.write(output_text, version=2.0)
    las_content = output_text.getvalue().encode()
    output_text.close()

    # Extract the original file name from the uploaded file
    original_filename = uploaded_files[0].name  # assuming we use the first file for the name

    st.sidebar.download_button(
        label=f"Download {selected_well}",
        data=las_content,
        file_name=original_filename,
        mime="application/octet-stream",
    )

    st.divider()

    # --- Download All Button ---
    st.sidebar.subheader("📥 Download All LAS Files")

    # Create a zip buffer
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_name, las in las_files.items():
            # Apply standard renaming to each LAS file
            for curve in las.curves:
                original_name = curve.mnemonic.upper()
                for standard in standard_names:
                    if standard in original_name:
                        curve.mnemonic = standard
                        break

            # Write each updated LAS file into the zip
            output_text = StringIO()
            las.write(output_text, version=2.0)
            las_content = output_text.getvalue().encode()
            output_text.close()

            # Add updated LAS content to zip
            zip_file.writestr(file_name, las_content)

    zip_buffer.seek(0)  # Reset buffer to the beginning for download

    # Add the "Download All" button
    st.sidebar.download_button(
        label="Download All LAS Files (Standardized)",
        data=zip_buffer,
        file_name="all_standardized_las_files.zip",
        mime="application/zip",
    )

else:
    st.info("⬅️ Please upload LAS files and enter standard log names to get started.")
