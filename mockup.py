import streamlit as st
import cv2
import numpy as np
import colorsys
from streamlit_cropper import st_cropper
from PIL import Image
import io  # <- MOCKUP KO SAVE KARNE KE LIYE NAYA IMPORT

st.set_page_config(layout="wide")
st.title("👕 T-Shirt Print Extractor & Mockup Tool")
st.write("Pehle image upload karein, design crop karein, background hatayein, aur fir use mockup par lagayein.")

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

st.sidebar.header("Noise Reduction Settings")
st.sidebar.info("Ye sliders print ke kinaaron aur chhote spots ko saaf karne mein madad karte hain.")
open_iter = st.sidebar.slider('Opening Iterations', 0, 10, 1) 
close_iter = st.sidebar.slider('Closing Iterations', 0, 10, 2)

# --- Main App ---
uploaded_file = st.file_uploader("1. Apni T-shirt ki image upload karein", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 1. Image ko read karna
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img_to_crop = cv2.imdecode(file_bytes, 1)
    img_to_crop_rgb = cv2.cvtColor(img_to_crop, cv2.COLOR_BGR2RGB)
    img_to_crop_pil = Image.fromarray(img_to_crop_rgb)

    st.header("2. Design ko Crop Karein")
    st.write("Box ko adjust karke design ko close select karein. Faltu background hata dein.")
    
    # 2. CROPPER COMPONENT
    cropped_img_pil = st_cropper(
        img_to_crop_pil, 
        realtime_update=True, 
        box_color='blue', 
        aspect_ratio=None, 
        return_type='image'
    )
    
    # 3. Cropped image ko OpenCV (BGR) format mein wapas convert karna
    img = cv2.cvtColor(np.array(cropped_img_pil), cv2.COLOR_RGB2BGR)

    st.header("3. Result (Extracted Print)")
    
    # --- Background Removal Logic ---
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
    png_image_bgra = cv2.merge([b, g, r, alpha])
    png_image_rgba = cv2.cvtColor(png_image_bgra, cv2.COLOR_BGRA2RGBA)
    # --- End of Background Removal ---

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Aapki Cropped Image")
        st.image(cropped_img_pil, caption='Yeh hissa process hoga', use_column_width=True)

    with col2:
        st.subheader("Extracted Print (Transparent)")
        st.image(png_image_rgba, caption='Background hatane ke baad', use_column_width=True)

        _, buf = cv2.imencode('.png', png_image_bgra)
        st.download_button(
            label="🖼️ Sirf Print Download Karein (PNG)",
            data=buf.tobytes(),
            file_name="extracted_print.png",
            mime="image/png"
        )
        
    st.divider() # Ek line daal di taaki steps alag dikhein

    # --- NAYA SECTION: MOCKUP ---
    st.header("4. (Optional) Mockup par Lagayein")
    mockup_file = st.file_uploader("Apni Mockup image (blank T-shirt, etc.) yahan upload karein", type=["jpg", "jpeg", "png"])

    if mockup_file is not None:
        # Design ko PIL format mein convert karna (paste karne ke liye)
        design_pil = Image.fromarray(png_image_rgba)
        
        # Mockup ko PIL format mein kholna
        mockup_pil = Image.open(mockup_file).convert("RGBA")

        st.write("Design ka size aur position adjust karein:")
        
        m_col1, m_col2 = st.columns([1, 2]) # Pehla column chhota (sliders), doosra bada (image)

        with m_col1:
            # Design ka size adjust karne ke liye slider
            max_width = mockup_pil.width
            default_width = max_width // 3
            design_width = st.slider("Design Ki Width", 50, max_width, default_width)
            
            # Aspect ratio maintain karte hue height calculate karna
            w_percent = (design_width / float(design_pil.width))
            h_size = int((float(design_pil.height) * float(w_percent)))
            
            # Design ko resize karna
            try:
                resized_design = design_pil.resize((design_width, h_size), Image.LANCZOS)
            except ValueError:
                # Agar height 0 ho jaaye toh
                st.error("Width bahut chhoti hai.")
                resized_design = design_pil # Error hone par original design use karein
            
            # Position adjust karne ke liye sliders
            max_x = mockup_pil.width - design_width
            max_y = mockup_pil.height - h_size
            
            x_pos = st.slider("Design X Position (Left/Right)", 0, max_x, max_x // 3)
            y_pos = st.slider("Design Y Position (Up/Down)", 0, max_y, max_y // 3)

        with m_col2:
            st.subheader("Final Mockup Result")
            
            # Mockup ki ek copy banayein
            final_mockup = mockup_pil.copy()
            
            # Design ko mockup par paste karein
            # Teesra argument (resized_design) zaroori hai, 
            # yeh PIL ko batata hai ki design ka alpha channel (transparency) istemal karna hai
            final_mockup.paste(resized_design, (x_pos, y_pos), resized_design)
            
            # Final image dikhayein
            st.image(final_mockup, caption='Aapka final mockup', use_column_width=True)
            
            # Final mockup ko download karne ke liye bytes mein convert karein
            buf = io.BytesIO()
            final_mockup.save(buf, format="PNG")
            byte_data = buf.getvalue()

            st.download_button(
                label="🚀 Final Mockup Download Karein (PNG)",
                data=byte_data,
                file_name="final_mockup.png",
                mime="image/png"
            )

else:
    st.info("Kripya shuru karne ke liye ek image file upload karein.")
