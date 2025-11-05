import streamlit as st
from PIL import Image, ImageChops
import io
import pillow_heif # HEIC फाइलों को पढ़ने के लिए

def hex_to_rgb(hex_code):
    hex_code = hex_code.lstrip('#')
    if len(hex_code) != 6:
        st.error("Invalid Hex Code! Please use #RRGGBB format.")
        return None
    try:
        return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        st.error("Invalid Hex Code!")
        return None

def colorize_mockup(image, hex_code):
    image = image.convert("RGBA")
    r, g, b, a = image.split()
    
    rgb_image = Image.merge("RGB", (r, g, b))
    gray_mask = rgb_image.convert("L")
    
    shadows_rgb = gray_mask.convert("RGB")

    target_rgb = hex_to_rgb(hex_code)
    if target_rgb is None:
        return None
        
    color_img = Image.new("RGB", image.size, target_rgb)
    
    colored_mockup_rgb = ImageChops.multiply(color_img, shadows_rgb)
    
    colored_mockup_rgb.putalpha(a)
    return colored_mockup_rgb

st.set_page_config(layout="wide")
st.title("👕 T-Shirt Mockup Generator")
st.write("This app changes your white t-shirt mockup to any color and applies your design.")

col1, col2 = st.columns(2)

with col1:
    st.header("1. Upload Your Files")
    mockup_file = st.file_uploader("White T-Shirt Mockup", type=["png", "jpg", "jpeg"])
    
    # --- अपडेट: अब HEIC/HEIF फाइलें भी लेगा ---
    print_file = st.file_uploader("Design/Print (Transparent PNG is best!)", type=["png", "heic", "heif"])
    
    st.header("2. Choose Color")
    hex_code = st.text_input("Hex Code for T-Shirt", "#9E9E16")

if st.button("🚀 Generate!"):
    if mockup_file and print_file and hex_code:
        with st.spinner("Generating mockup..."):
            try:
                base_mockup = Image.open(mockup_file)
                
                # --- अपडेट: HEIC फाइल को हैंडल करने का लॉजिक ---
                if print_file.type == "image/heic" or print_file.type == "image/heif":
                    heif_file = pillow_heif.read_heif(print_file)
                    print_design = Image.frombytes(
                        heif_file.mode, 
                        heif_file.size, 
                        heif_file.data,
                        "raw",
                    )
                else:
                    print_design = Image.open(print_file)
                
                colored_base = colorize_mockup(base_mockup, hex_code)
                
                if colored_base:
                    base_w, base_h = colored_base.size
                    ratio = (base_w * 0.4) / print_design.width
                    new_h = int(print_design.height * ratio)
                    print_resized = print_design.resize((int(base_w * 0.4), new_h), Image.LANCZOS)
                    
                    print_w, print_h = print_resized.size
                    
                    offset_x = (base_w - print_w) // 2
                    offset_y = int(base_h * 0.35)
                    
                    final_image = colored_base.copy()
                    
                    # --- !!! मुख्य अपडेट: क्रैश को रोकना !!! ---
                    # हम चेक करेंगे कि इमेज 'RGBA' (ट्रांसपेरेंट) है या 'RGB' (फ्लैट)
                    if print_resized.mode == 'RGBA':
                        # यह सही तरीका है - सिर्फ ट्रांसपेरेंट हिस्से पेस्ट होंगे
                        final_image.paste(print_resized, (offset_x, offset_y), print_resized.split()[3])
                    else:
                        # यह फ्लैट इमेज है (जैसे आपकी गुलाबी टी-शर्ट)
                        # यह क्रैश नहीं होगा, लेकिन यह पूरा रेक्टेंगल चिपका देगा
                        st.warning("⚠️ Warning: Your design image is not transparent. Pasting the whole image box.")
                        final_image.paste(print_resized, (offset_x, offset_y))
                    # --- अपडेट खत्म ---

                    with col2:
                        st.header("🎉 Your New Mockup")
                        st.image(final_image, caption="Generated Mockup", use_column_width=True)
                        
                        buf = io.BytesIO()
                        final_image.save(buf, format="PNG")
                        st.download_button(
                            label="Download Image",
                            data=buf.getvalue(),
                            file_name=f"mockup_{hex_code}.png",
                            mime="image/png"
                        )
                        
            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        st.warning("⚠️ Please upload both files and enter a hex code.")
