import fitz  # PyMuPDF
import streamlit as st
from PIL import Image
import io

# Page setup
st.set_page_config(
    page_title="Goodluck Engineering — PDF Stamper",
    page_icon="🖊️",
    layout="wide"
)

st.title("🖊️ Automated PDF Stamp & Signature Tool")
st.caption("Apply Goodluck Engineering stamp and authorized signature across multi-page PDF quotations completely offline.")

# Sidebar Controls
st.sidebar.header("1. Document & Stamp Upload")
uploaded_pdf = st.sidebar.file_uploader("Upload Quotation PDF", type=["pdf"])
uploaded_stamp = st.sidebar.file_uploader("Upload Stamp/Sign PNG (Transparent)", type=["png"])

st.sidebar.markdown("---")
st.sidebar.header("2. Stamp Placement Settings")

# Position Preset Selector
position_mode = st.sidebar.selectbox(
    "Stamp Position Target",
    ["Bottom Right", "Bottom Left", "Top Right", "Top Left", "Manual Pixel Coordinates"]
)

# Dimension Controls
scale_factor = st.sidebar.slider("Stamp Scale (%)", min_value=5, max_value=40, value=15, step=1)
margin_x = st.sidebar.number_input("Horizontal Margin (pts)", min_value=0, max_value=300, value=30)
margin_y = st.sidebar.number_input("Vertical Margin (pts)", min_value=0, max_value=300, value=30)

# Manual Coordinate Overrides (Visible only if selected)
if position_mode == "Manual Pixel Coordinates":
    manual_x = st.sidebar.number_input("Exact X Position (pts)", min_value=0, value=450)
    manual_y = st.sidebar.number_input("Exact Y Position (pts)", min_value=0, value=750)
else:
    manual_x, manual_y = None, None

def calculate_stamp_box(page_width, page_height, stamp_aspect_ratio, scale_pct, mode, m_x, m_y, man_x, man_y):
    """Calculates fitz.Rect coordinates for stamp insertion based on page bounds."""
    # Base reference width (Standard A4 width = 595.27 points)
    stamp_width = page_width * (scale_pct / 100.0)
    stamp_height = stamp_width / stamp_aspect_ratio

    if mode == "Manual Pixel Coordinates":
        pos_x = min(man_x, page_width - stamp_width)
        pos_y = min(man_y, page_height - stamp_height)
    elif mode == "Bottom Right":
        pos_x = page_width - stamp_width - m_x
        pos_y = page_height - stamp_height - m_y
    elif mode == "Bottom Left":
        pos_x = m_x
        pos_y = page_height - stamp_height - m_y
    elif mode == "Top Right":
        pos_x = page_width - stamp_width - m_x
        pos_y = m_y
    elif mode == "Top Left":
        pos_x = m_x
        pos_y = m_y

    return fitz.Rect(pos_x, pos_y, pos_x + stamp_width, pos_y + stamp_height)

# Main Processing Logic
if uploaded_pdf and uploaded_stamp:
    # Read files into bytes
    pdf_bytes = uploaded_pdf.read()
    stamp_bytes = uploaded_stamp.read()

    # Get Stamp Aspect Ratio using PIL
    stamp_img = Image.open(io.BytesIO(stamp_bytes))
    stamp_w, stamp_h = stamp_img.size
    aspect_ratio = stamp_w / float(stamp_h)

    # Open PDF Document
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(doc)

    st.success(f"Loaded **{uploaded_pdf.name}** ({total_pages} Pages)")

    # Render First Page Preview
    st.subheader("👁️ First Page Visual Preview")
    st.caption("Verify stamp position and scaling before applying across all pages.")

    first_page = doc[0]
    page_w = first_page.rect.width
    page_h = first_page.rect.height

    # Compute preview bounding box
    preview_rect = calculate_stamp_box(
        page_w, page_h, aspect_ratio, scale_factor, position_mode, margin_x, margin_y, manual_x, manual_y
    )

    # Create temporary doc for rendering visual preview
    preview_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    p1 = preview_doc[0]
    p1.wrap_contents()
    p1.insert_image(preview_rect, stream=stamp_bytes)

    # Convert preview page to image pixmap
    pix = p1.get_pixmap(dpi=150)
    preview_img_bytes = pix.tobytes("png")
    
    st.image(preview_img_bytes, caption="Page 1 Placement Preview", use_container_width=True)
    preview_doc.close()

    st.markdown("---")

    # Action Button to Stamp Entire PDF
    if st.button(f"🖊️ Apply Stamp & Signature across all {total_pages} Pages", type="primary"):
        progress_bar = st.progress(0)
        
        # Iterate over all pages and insert image
        for idx, page in enumerate(doc):
            page.wrap_contents()
            w = page.rect.width
            h = page.rect.height
            
            rect = calculate_stamp_box(
                w, h, aspect_ratio, scale_factor, position_mode, margin_x, margin_y, manual_x, manual_y
            )
            page.insert_image(rect, stream=stamp_bytes)
            
            # Update progress
            progress_bar.progress((idx + 1) / total_pages)

        # Output stamped PDF to memory buffer
        output_buffer = io.BytesIO()
        doc.save(output_buffer, garbage=4, deflate=True)
        doc.close()
        output_data = output_buffer.getvalue()

        st.success("✅ Stamping Complete!")
        
        # Download Button
        output_filename = f"Stamped_{uploaded_pdf.name}"
        st.download_button(
            label="📥 Download Signed Quotation PDF",
            data=output_data,
            file_name=output_filename,
            mime="application/pdf"
        )
else:
    st.info("👈 Please upload both a **Quotation PDF** and a **Stamp/Signature PNG** in the sidebar to begin.")