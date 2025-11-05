import streamlit as st
import cv2
import numpy as np
import colorsys

st.set_page_config(layout="wide")
st.title("👕 T-Shirt Print Extractor")
st.write("Aapki T-shirt ki image se print nikaalne ki koshish karega.")

# --- Helper Functions (Rang Convert karne ke liye) ---

def hex_to_rgb(hex_val):
    """Hex color string ko RGB tuple mein badalta hai"""
    hex_val = hex_val.lstrip('#')
    return tuple(int(hex_val[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hsv(r, g, b):
    """RGB values (0-255) ko OpenCV ke HSV format (H:0-179, S:0-255, V:0-255) mein badalta hai"""
    # Pehle RGB ko 0-1 range mein laayein
    r_norm, g_norm, b_norm = r/255.0, g/255.0, b/255.0
    # colorsys se HSV (0-1 range) mein convert karein
    h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
    # OpenCV ki range mein convert karein
    h_cv = int(h * 179)
    s_cv = int(s * 255)
    v_cv = int(v * 255)
    return (h_cv, s_cv, v_cv)

# --- Sidebar mein NAYI settings ---
st.sidebar.header("Rang (Color) Settings")
st.sidebar.info("Pehle T-shirt ka main rang chunein, fir 'Tolerance' sliders se range ko adjust karein.")

# 1. Color Picker
# Default color hamne pink rakha hai, aapki image ke hisab se
base_color_hex = st.sidebar.color_picker('1. T-Shirt Ka Main Rang Chunein', '#D90166')

# Pick kiye gaye rang (HEX) ko pehle RGB, fir HSV mein convert karna
r, g, b = hex_to_rgb(base_color_hex)
h, s, v = rgb_to_hsv(r, g, b)

st.sidebar.success(f"Aapne jo rang chuna hai: (H:{h}, S:{s}, V:{v})")

# 2. Tolerance Sliders
st.sidebar.subheader("2. Rang ki Range (Tolerance)")
h_tolerance = st.sidebar.slider('Hue Tolerance (Rang mein fark)', 0, 90, 15) # 0-179 range
s_tolerance = st.sidebar.slider('Saturation Tolerance (Feeka/Gehra)', 0, 127, 70) # 0-255 range
v_tolerance = st.sidebar.slider('Value Tolerance (Roshni/Andhera)', 0, 127, 70) # 0-255 range

# Tolerance ke hisab se Min aur Max values calculate karna
h_min = max(0, h - h_tolerance)
h_max = min(179, h + h_tolerance)
s_min = max(0, s - s_tolerance)
s_max = min(255, s + s_tolerance)
v_min = max(0, v - v_tolerance)
v_max = min(255, v + v_tolerance)

st.sidebar.header("Noise Reduction Settings")
open_iter = st.sidebar.slider('Opening Iterations', 0, 10, 1)
close_iter = st.sidebar.slider('Closing Iterations', 0, 10, 2)

# --- Main App ---
uploaded_file = st.file_uploader("Apni T-shirt ki image upload karein", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Uploaded file ko OpenCV format mein read karna
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
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
        _, buf = cv2.imencode('.png', png_image)
        
        st.download_button(
            label="Processed PNG Download Karein",
            data=buf,
            file_name=f"extracted_{uploaded_file.name}.png",
            mime="image/png"
        )
else:
    st.info("Kripya shuru karne ke liye ek image file upload karein.")
