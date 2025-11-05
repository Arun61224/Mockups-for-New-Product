import streamlit as st
import cv2
import numpy as np

st.set_page_config(layout="wide")
st.title("👕 T-Shirt Print Extractor")
st.write("Aapki T-shirt ki image se print nikaalne ki koshish karega.")

# --- Sidebar mein settings ---
st.sidebar.header("Rang (Color) Settings")
st.sidebar.info("Yahan par aap us rang ki settings ko adjust kar sakte hain jise aap hatana (remove) chahte hain (jaise T-shirt ka rang).")

# Image ko HSV (Hue, Saturation, Value) format mein process karna behtar hota hai
h_min = st.sidebar.slider('Hue Min', 0, 179, 140)
h_max = st.sidebar.slider('Hue Max', 0, 179, 170)
s_min = st.sidebar.slider('Saturation Min', 0, 255, 50)
s_max = st.sidebar.slider('Saturation Max', 0, 255, 255)
v_min = st.sidebar.slider('Value Min', 0, 255, 50)
v_max = st.sidebar.slider('Value Max', 0, 255, 255)

st.sidebar.header("Noise Reduction Settings")
open_iter = st.sidebar.slider('Opening Iterations', 0, 10, 1)
close_iter = st.sidebar.slider('Closing Iterations', 0, 10, 2)

# --- Main App ---
uploaded_file = st.file_uploader("Apni T-shirt ki image upload karein", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Uploaded file ko OpenCV format mein read karna
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1) # 1 = cv2.IMREAD_COLOR
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) # Streamlit display ke liye RGB

    col1, col2 = st.columns(2)

    with col1:
        st.header("Original Image")
        st.image(img_rgb, caption='Aapki upload ki gayi image', use_column_width=True)

    with col2:
        st.header("Extracted Print (PNG)")
        
        # --- 1. Rang ke liye Range define karna ---
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_range = np.array([h_min, s_min, v_min])
        upper_range = np.array([h_max, s_max, v_max])

        # --- 2. Mask banana ---
        mask = cv2.inRange(hsv, lower_range, upper_range)

        # --- 3. Mask ko clean karna (Noise hatane ke liye) ---
        kernel = np.ones((3, 3), np.uint8)
        if open_iter > 0:
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=open_iter)
        if close_iter > 0:
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=close_iter)

        # --- 4. Mask ko Invert karna ---
        mask_inv = cv2.bitwise_not(mask)

        # --- 5. Transparent PNG banana ---
        b, g, r = cv2.split(img)
        alpha = mask_inv
        png_image = cv2.merge([b, g, r, alpha])

        # Streamlit mein display karna
        st.image(png_image, caption='Background hatane ke baad', use_column_width=True)

        # --- 6. Download Button banana ---
        # Image ko memory mein encode karna
        _, buf = cv2.imencode('.png', png_image)
        
        st.download_button(
            label="Processed PNG Download Karein",
            data=buf,
            file_name=f"extracted_{uploaded_file.name}.png",
            mime="image/png"
        )
else:
    st.info("Kripya shuru karne ke liye ek image file upload karein.")
