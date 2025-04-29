import streamlit as st
import lasio
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO, BytesIO
import zipfile

# --- Page setup ---
st.set_page_config(page_title="LAS Curve Standardizer", layout="wide")
st.title("🛢️ LAS Curve Standardizer and Viewer")

# --- Sidebar ---
st.sidebar.header("📂 Upload and Settings")

# Upload LAS file(s)
uploaded_las_files = st.sidebar.file_uploader(
    "Upload LAS file(s)", type=["las"], accept_multiple_files=True
)

# Upload petrophysical analysis file (CSV or Excel)
uploaded_petrophys_file = st.sidebar.file_uploader(
    "Upload Petrophysical Analysis File (CSV/Excel)", type=["csv", "xlsx"], accept_multiple_files=False
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
if uploaded_las_files and standard_names:
    # Read LAS files into dictionary
    las_files = {}
    for uploaded_file in uploaded_las_files:
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8", errors="ignore"))
        las = lasio.read(stringio)
        las_files[uploaded_file.name] = las

    # Read petrophysical analysis file if uploaded
    petro_df = None
    if uploaded_petrophys_file:
        try:
            if uploaded_petrophys_file.name.endswith('.csv'):
                petro_df = pd.read_csv(uploaded_petrophys_file)
            elif uploaded_petrophys_file.name.endswith('.xlsx'):
                petro_df = pd.read_excel(uploaded_petrophys_file)
            st.success("Petrophysical file loaded successfully!")
        except Exception as e:
            st.error(f"Error reading petrophysical file: {e}")

    # --- Select Well to View ---
    selected_well = st.sidebar.selectbox(
        "Select Well to View",
        list(las_files.keys())
    )

    las = las_files[selected_well]

    # --- Apply Standard Renaming ---
    for curve in las.curves:
        original_name = curve.mnemonic.upper()
        for standard in standard_names:
            if standard in original_name:
                curve.mnemonic = standard
                break

    # Convert LAS data to DataFrame
    las_df = las.df().reset_index()

    # Merge with petrophysical data if available
    if petro_df is not None:
        try:
            # Assume petrophysical data has a 'DEPT' or 'Depth' column for merging
            depth_col = next((col for col in petro_df.columns if col.lower() in ['dept', 'depth']), None)
            if depth_col:
                # Merge on depth, keeping all LAS depths (left join)
                merged_df = pd.merge(
                    las_df, petro_df, 
                    left_on='DEPT', right_on=depth_col, 
                    how='left'
                )
                # Drop the redundant depth column from petrophysical data if different
                if depth_col != 'DEPT':
                    merged_df = merged_df.drop(columns=[depth_col])
                las_df = merged_df
                st.success("Petrophysical data merged successfully!")
            else:
                st.warning("No 'DEPT' or 'Depth' column found in petrophysical file. Skipping merge.")
        except Exception as e:
            st.error(f"Error merging data: {e}")

    st.subheader(f"📄 Curves in `{selected_well}`")

    # Display Curves Before and After Renaming
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ➡️ Original Curves")
        curves_before = [curve.mnemonic for curve in las.curves]
        st.write(curves_before)

    with col2:
        st.markdown("### 🔁 Standardized Curves")
        curves_after = las_df.columns.tolist()
        if 'DEPT' in curves_after:
            curves_after.remove('DEPT')
        st.write(curves_after)

    st.divider()

    # --- Visualization ---
    st.subheader("📈 Quick Log Viewer")

    available_logs = las_df.columns.tolist()
    if 'DEPT' in available_logs:
        available_logs.remove('DEPT')
    selected_logs = st.multiselect(
        "Select Logs to Plot",
        available_logs,
        default=available_logs[:3] if len(available_logs) >= 3 else available_logs
    )

    if selected_logs:
        fig, ax = plt.subplots(figsize=(8, 12))
        for log in selected_logs:
            if log in las_df.columns:
                ax.plot(las_df[log], las_df['DEPT'], label=log)

        ax.set_xlabel("Log Values")
        ax.set_ylabel("Depth (m)")
        ax.invert_yaxis()
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

    st.divider()

    # --- Individual Download Section in Sidebar ---
    st.sidebar.subheader("📥 Download LAS File")

    # Update LAS object with merged data
    las_new = lasio.LASFile()
    las_new.well = las.well
    las_new.params = las.params
    las_new.other = las.other
    las_new.set_data_from_df(las_df, depth_col='DEPT')

    output_text = StringIO()
    las_new.write(output_text, version=2.0)
    las_content = output_text.getvalue().encode()
    output_text.close()

    original_filename = selected_well

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

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP puol-DEFLATED) as zip_file:
        for file_name, las in las_files.items():
            # Apply standard renaming
            for curve in las.curves:
                original_name = curve.mnemonic.upper()
                for standard in standard_names:
                    if standard in original_name:
                        curve.mnemonic = standard
                        break

            # Convert LAS to DataFrame
            las_df = las.df().reset_index()

            # Merge with petrophysical data if available
            if petro_df is not None:
                try:
                    depth_col = next((col for col in petro_df.columns if col.lower() in ['dept', 'depth']), None)
                    if depth_col:
                        merged_df = pd.merge(
                            las_df, petro_df, 
                            left_on='DEPT', right_on=depth_col, 
                            how='left'
                        )
                        if depth_col != 'DEPT':
                            merged_df = merged_df.drop(columns=[depth_col])
                        las_df = merged_df
                except Exception as e:
                    st.error(f"Error merging data for {file_name}: {e}")

            # Create new LAS file with merged data
            las_new = lasio.LASFile()
            las_new.well = las.well
            las_new.params = las.params
            las_new.other = las.other
            las_new.set_data_from_df(las_df, depth_col='DEPT')

            # Write to LAS format
            output_text = StringIO()
            las_new.write(output_text, version=2.0)
            las_content = output_text.getvalue().encode()
            output_text.close()

            # Add to zip
            zip_file.writestr(file_name, las_content)

    zip_buffer.seek(0)

    st.sidebar.download_button(
        label="Download All LAS Files (Standardized & Merged)",
        data=zip_buffer,
        file_name="all_standardized_merged_las_files.zip",
        mime="application/zip",
    )

else:
    st.info("⬅️ Please upload LAS files and enter standard log names to get started.")
