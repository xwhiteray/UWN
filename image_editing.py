from PIL import Image, ImageDraw, ImageFont
import qrcode
import os

def wrap_text(text, font, max_width):
    lines = []
    words = text.split()
    line = ''
    for word in words:
        test_line = f"{line} {word}".strip()
        line_width, _ = font.getsize(test_line)
        if line_width <= max_width:
            line = test_line
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines

def truncate_text(text, font, max_width):
    ellipsis = '...'
    ellipsis_width, _ = font.getsize(ellipsis)
    current_text = ''
    for char in text:
        test_text = current_text + char
        test_width, _ = font.getsize(test_text)
        if test_width + ellipsis_width <= max_width:
            current_text = test_text
        else:
            return current_text + ellipsis
    return current_text

def generate_ticket_image(id, qr_data, buyer_name, seller_name, seat_label):
    """
    Generates a ticket image with specified details and returns the path to the saved image.

    :param id: Unique identifier used for naming the saved image file.
    :param qr_data: Text data to encode in the QR code.
    :param buyer_name: Name of the ticket buyer.
    :param seller_name: Name of the seller.
    :param seat_label: Seat label (e.g., "A1", "B4").
    :return: Path to the saved image file.
    """
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Construct absolute paths
        image_path = os.path.join(script_dir, 'ticketyellow.png')
        font_path = os.path.join(script_dir, 'Aileron-Light.otf')
        
        
        # Open an existing image
        image = Image.open(image_path)
        
        # Convert image to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Create an ImageDraw object
        draw = ImageDraw.Draw(image)
        
        # Use a TrueType font
        font = ImageFont.truetype(font_path, size=28)
        
        # Verify image dimensions
        image_width, image_height = image.size
        
        colors = (0, 0, 0)
        
        # Define maximum text width
        max_text_width = 300  # Adjust this value based on your image
        
        # Starting positions
        x_position = 660
        y_positions = [50, 85, 120]
        
        # Adjust the order of texts as per your request
        # New order: buyer_name, seller_name, seat_label
        texts = [buyer_name, seller_name, seat_label]
        
        # Add text to the image
        for idx, text in enumerate(texts):
            y_position = y_positions[idx]
            if idx == 2:  # If it's the last text (seat_label), wrap text to new lines
                lines = wrap_text(text, font, max_text_width)
                for line in lines:
                    draw.text((x_position, y_position), line, fill=colors, font=font)
                    line_height = font.getsize(line)[1]
                    y_position += line_height  # Move to next line
            else:
                # For other texts, truncate with ellipsis if necessary
                truncated_text = truncate_text(text, font, max_text_width)
                draw.text((x_position, y_position), truncated_text, fill=colors, font=font)
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,  # Controls the size of the QR code (1-40)
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,  # Controls how many pixels each "box" of the QR code is
            border=1,    # Controls how many boxes thick the border should be
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="#f2eddb").convert('RGB')
        
        # Resize QR code image if necessary
        qr_size = 250  # Desired size of the QR code
        qr_img = qr_img.resize((qr_size, qr_size), Image.ANTIALIAS)
        
        # Position to paste the QR code on the main image
        qr_x = image_width - qr_size - 80  # Adjust 190 as needed for margin
        qr_y = image_height - qr_size - 130  # Adjust 140 as needed for margin
        
        # Paste the QR code onto the main image
        image.paste(qr_img, (qr_x, qr_y))

        # Define the output directory
        output_dir = 'ticket'

        # Create the directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        output_filename = os.path.join(output_dir, f'{id}.png')

        # Save the edited image
        image.save(output_filename)
        
        print("Text and QR code added to the image successfully.")
        
        return output_filename
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

generate_ticket_image('12983928328', 'hello world', 'Lendy AWDAWDA WADASDA DAADADAWDWD', 'Lana', 'C20')