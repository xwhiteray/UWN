from PIL import Image, ImageDraw, ImageFont, ImageOps
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

def classify_seat(seat):
    # imam_rows = ['A']
    # vvip_rows = ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
    # special_rows = ['J', 'K', 'L', 'M', 'N', 'O', 'P']
    # last_row = ['R', 'Q']

    imamRows = ['A']
    vvipRows = ['B', 'C', 'D', 'E', 'F', 'G']
    specialRows = ['H', 'I', 'J', 'K']
    lastRow = ['L', 'M', 'N']
    moreRow = ['O', 'P', 'Q', 'R']

    # Extract row letter and seat number
    row_letter = ''.join(filter(str.isalpha, seat))
    seat_number = int(''.join(filter(str.isdigit, seat)))
    
    # Default seat class
    seat_class = 'blue'
    
    # Determine seat class based on row and seat number
    if row_letter in imamRows:
        if 8 <= seat_number <= 20:
            seat_class = 'red'
        else:
            seat_class = 'blue'
    elif row_letter in vvipRows:
        if 6 <= seat_number <= 25:
            seat_class = 'red'
        else:
            seat_class = 'blue'
    elif row_letter in specialRows:
        if 6 <= seat_number <= 25:
            seat_class = 'yellow'
        else:
            seat_class = 'blue'
    elif row_letter in lastRow:
        if 6 <= seat_number <= 25:
            seat_class = 'green'
        else:
            seat_class = 'blue'
    elif row_letter in moreRow:
        seat_class = 'blue'
    
    return seat_class

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

        seat_class = classify_seat(seat_label)
        fill_colors = seat_class

        if(seat_class == "blue"):
            fill_colors = (12,192,223)
        elif(seat_class == "green"):
            fill_colors = (0,214,28)
        elif(seat_class == "yellow"):
            fill_colors = (239,223,15)

        # Construct absolute paths
        image_path = os.path.join(script_dir, f'{seat_class}.png')
        font_path = os.path.join(script_dir, 'Poppins-Regular.ttf')
        
        
        # Open an existing image
        image = Image.open(image_path)
        
        # Convert image to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Create an ImageDraw object
        draw = ImageDraw.Draw(image)
        
        # Use a TrueType font
        font = ImageFont.truetype(font_path, size=45)
        
        # Verify image dimensions
        image_width, image_height = image.size
        
        colors = "white"
        
        # Define maximum text width
        max_text_width = 500  # Adjust this value based on your image
        
        # Starting positions
        x_position = 40
        y_positions = [1670, 1750, 1850]
        
        # Adjust the order of texts as per your request
        # New order: buyer_name, seller_name, seat_label
        texts = [buyer_name, ("SEAT : " + seat_label), seller_name]
        
        # Add text to the image
        for idx, text in enumerate(texts):
            y_position = y_positions[idx]
            if idx == 2:  # If it's the last text (seat_label), wrap text to new lines
                # lines = wrap_text(text, font, max_text_width)
                # for line in lines:
                #     draw.text((x_position, y_position), line, fill=colors, font=font)
                #     line_height = font.getsize(line)[1]
                #     y_position += line_height  # Move to next line
                truncated_text = truncate_text(text, font, max_text_width)
                draw.text((x_position, y_position), truncated_text, fill=colors, font=font)
            else:
                # For other texts, truncate with ellipsis if necessary
                truncated_text = truncate_text(text, ImageFont.truetype(font_path, size=50), max_text_width)
                draw.text((x_position, y_position), truncated_text, fill=colors, font=ImageFont.truetype(font_path, size=50))
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=None,  # Controls the size of the QR code (1-40)
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,  # Controls how many pixels each "box" of the QR code is
            border=2,    # Controls how many boxes thick the border should be
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color=fill_colors).convert('RGB')
        
        # Resize QR code image if necessary
        qr_size = 380  # Desired size of the QR code
        qr_img = qr_img.resize((qr_size, qr_size), Image.ANTIALIAS)

        # qr_with_border = ImageOps.expand(qr_img, border=10, fill="black")
        
        # Position to paste the QR code on the main image
        qr_x = image_width - qr_size - 25  # Adjust 190 as needed for margin
        qr_y = image_height - qr_size - 20  # Adjust 140 as needed for margin
        
        # Paste the QR code onto the main image
        image.paste(qr_img, (qr_x, qr_y))

        # text_width, text_height = draw.textsize(seat_label, font=ImageFont.truetype(font_path, size=55))

        # text_position = (qr_x+(qr_img.width / 2)-(text_width/3), qr_y+(qr_img.height / 2)-(text_height/3))

        # draw.rectangle(
        #     [text_position[0]-8, text_position[1],
        #     text_position[0] + text_width, text_position[1] + text_height],
        #     fill=fill_colors
        # )
        # draw.text(text_position, seat_label, font=ImageFont.truetype(font_path, size=45), fill="black")

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

generate_ticket_image('12983928328', 'hello world', 'Lendy AWDAWDA WADASDA DAADADAWDWD', 'PIC : Lendy AWDAWDA WADASDA DAADADAWDWD', 'L6')