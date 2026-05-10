import streamlit as st
import requests


def render_plant_doctor_ui(plant_doctor_url, key_suffix="", style="dashboard"):
    if style == "wizard":
        st.markdown("""
            <div style='background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                        border: 2px solid #2ecc71; border-radius: 15px;
                        padding: 30px; margin-bottom: 20px;'>
                <h2 style='color: #2ecc71; text-align: center; margin: 0;'>
                    🩺 Plant Doctor AI
                </h2>
                <p style='color: #7f8c8d; text-align: center; margin: 5px 0 0 0;'>
                    Upload a leaf image for instant disease diagnosis
                </p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("### 🩺 Plant Doctor: AI Crop Disease Diagnosis")
        st.write("Upload a photo of your crop leaf to identify diseases and get treatment recommendations.")

    st.markdown("---")

    uploaded_file = st.file_uploader(
        "📸 Choose a leaf image...",
        type=["jpg", "jpeg", "png"],
        key=f"pd_upload_{key_suffix}"
    )

    if uploaded_file is not None:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.image(uploaded_file, caption="Uploaded Leaf Image", width='stretch')

        with col2:
            with st.spinner("🔄 Processing image with EfficientNetB0..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(f"{plant_doctor_url}/predict", files=files, timeout=30)

                    if response.status_code == 200:
                        result = response.json()
                        disease = result.get('disease', 'Unknown')
                        conf_raw = result.get('confidence', 0)
                        confidence = float(str(conf_raw).replace('%', '')) / (100 if '%' in str(conf_raw) else 1)
                        treatment = result.get('treatment', {})

                        if style == "wizard":
                            conf_color = "#27ae60" if confidence > 0.8 else "#f39c12" if confidence > 0.5 else "#e74c3c"
                            st.markdown(f"""
                                <div style='background: #1a1a2e; border: 2px solid {conf_color};
                                            border-radius: 10px; padding: 20px; margin-bottom: 15px;'>
                                    <h3 style='color: {conf_color}; margin: 0;'>🔬 Diagnosis Result</h3>
                                    <hr style='border-color: {conf_color}; opacity: 0.3;'>
                                    <p style='color: white; font-size: 1.3rem; margin: 10px 0;'>
                                        <b>Disease:</b> {disease}
                                    </p>
                                    <p style='color: {conf_color}; font-size: 1.1rem; margin: 5px 0;'>
                                        <b>Confidence:</b> {confidence*100:.1f}%
                                    </p>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"### 📋 Diagnosis: **{disease}**")
                            st.progress(min(confidence, 1.0))
                            st.write(f"**Confidence Level:** {conf_raw}")

                        st.markdown("---")
                        st.markdown("### 💊 Recommended Treatment")
                        if isinstance(treatment, dict):
                            for key, value in treatment.items():
                                st.write(f"**{key}:** {value}")
                        else:
                            st.success(treatment)

                        if style == "dashboard" and "Healthy" in disease:
                            st.balloons()
                    else:
                        st.error(f"Error from API: {response.text}")
                except requests.exceptions.ConnectionError:
                    st.error(f"❌ Could not connect to Plant Doctor API at {plant_doctor_url}")
                except Exception as e:
                    st.error(f"Error: {e}")
