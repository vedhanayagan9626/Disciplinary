import qrcode  # Ensure the qrcode library is installed: pip install qrcode[pil] or use segno
import os
from io import BytesIO
import base64

def generate_student_qr_code(student_id, register_number, output_path='static/qrcodes'):
    """
    Generate a QR code for a student that links to their points page
    Returns the filename and base64 encoded image
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    # Create the URL that will be encoded in the QR code
    qr_url = f"/api/student/{student_id}/qrcode"
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)
    
    # Create QR code image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save the image
    filename = f"student_{student_id}_{register_number}.png"
    filepath = os.path.join(output_path, filename)
    img.save(filepath)
    
    # Also create base64 version for immediate download
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return filename, img_str