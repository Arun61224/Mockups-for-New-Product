import streamlit as st
import cv2
import numpy as np
import colorsys
from streamlit_cropper import st_cropper
from PIL import Image # <- YEH NAYA IMPORT HAI

st.set_page_config(layout="wide")
st.title("👕 T-Shirt Print Extractor")
st.write("Pehle image upload karein, fir design ko crop karein, aur fir T-shirt ka rang select karein.")

# --- Helper Functions (Rang Convert karne ke liye) ---
def hex_to_rgb(hex_val):
    """Hex color string ko RGB tuple mein badalta hai"""
    hex_val = hex_val.lstrip('#')
    return tuple(int(hex_val[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hsv(r, g, b):
    """RGB values (0-255) ko OpenCV ke HSV format (H:0-179, S:0-255, V:0-255) mein badalta hai"""
    r_norm, g_norm, b_norm = r/255.0, g/255.0, b/255.0
    h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
    h_cv = int(h * 179)
    s_cv = int(s * 255)
    v_cv = int(v * 255)
    return (h_cv, s_cv, v_cv)

# --- Sidebar (Settings) ---
st.sidebar.header("Rang (Color) Settings")
st.sidebar.info("Pehle T-shirt ka main rang chunein, fir 'Tolerance' sliders se range ko adjust karein.")

base_color_hex = st.sidebar.color_picker('1. T-Shirt Ka Main Rang Chunein', '#D90166')
r, g, b = hex_to_rgb(base_color_hex)
h, s, v = rgb_to_hsv(r, g, b)
st.sidebar.success(f"Chuna gaya rang (HSV): ({h}, {s}, {v})")

st.sidebar.subheader("2. Rang ki Range (Tolerance)")
h_tolerance = st.sidebar.slider('Hue Tolerance (Rang mein fark)', 0, 90, 15)
s_tolerance = st.sidebar.slider('Saturation Tolerance (Feeka/Gehra)', 0, 127, 70)
v_tolerance = st.sidebar.slider('Value Tolerance (Roshni/Andhera)', 0, 127, 70)

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
uploaded_file = st.file_uploader("1. Apni T-shirt ki image upload karein", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 1. Image ko read karna
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img_to_crop = cv2.imdecode(file_bytes, 1)
    img_to_crop_rgb = cv2.cvtColor(img_to_crop, cv2.COLOR_BGR2RGB)
    
    # --- YAHAN BADLAAV HAI ---
    # NumPy array ko PIL Image mein convert karna
    img_to_crop_pil = Image.fromarray(img_to_crop_rgb)
    # -------------------------

    st.header("2. Design ko Crop Karein")
    st.write("Box ko adjust karke design ko select karein. Cropper ke neeche result dikhega.")
    
    # 2. CROPPER COMPONENT
    # Ab hum PIL image ko cropper mein bhej rahe hain
    cropped_img_pil = st_cropper(
        img_to_crop_pil, 
        realtime_update=True, 
        box_color='blue', 
        aspect_ratio=None, 
        return_type='image' # Yeh humein ek PIL image hi wapas dega
    )
    
    # 3. Cropped image (jo PIL format mein hai) ko OpenCV (BGR) format mein wapas convert karna
    img = cv2.cvtColor(np.array(cropped_img_pil), cv2.COLOR_RGB2BGR)

    st.header("3. Result")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Aapki Cropped Image")
        st.image(cropped_img_pil, caption='Yeh hissa process hoga', use_column_width=True)

    with col2:
        st.subheader("Extracted Print (PNG)")
        
        # Baaki ka process ab CROP ki hui image par chalega
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_range = np.array([h_min, s_min, v_min])
        upper_range = np.array([h_max, s_max, v_max])

        mask = cv2.inRange(hsv, lower_range, upper_range)

        kernel = np.ones((3, 3), np.uint8)
        if open_iter > 0:
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=open_iter)
        if close_iter > 0:
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=close_iter)

        mask_inv = cv2.bitwise_not(mask)

        b, g, r = cv2.split(img)
        alpha = mask_inv
        png_image = cv2.merge([b, g, r, alpha])

        st.image(png_image, caption='Background hatane ke baad', use_column_width=True)

        _, buf = cv2.imencode('.png', png_image)
        st.download_button(
            label="Processed PNG Download Karein",
            data=buf,
            file_name="extracted_print.png",
            mime="image/png"
        )
else:
    st.info("Kripya shuru karne ke liye ek image file upload karein.")
