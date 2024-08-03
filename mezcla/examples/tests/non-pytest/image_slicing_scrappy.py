from PIL import Image, ImageDraw, ImageFilter
import easyocr
import numpy as np
import os

def remove_borders(image, top=0, bottom=0, left=0, right=0):
    """
    Removes specified pixel borders from the image.
    
    :param image: The input PIL Image object.
    :param top: Number of pixels to remove from the top.
    :param bottom: Number of pixels to remove from the bottom.
    :param left: Number of pixels to remove from the left.
    :param right: Number of pixels to remove from the right.
    :return: The cropped PIL Image object with the specified borders removed.
    """
    img_width, img_height = image.size

    left = max(0, left)
    top = max(0, top)
    right = min(img_width, img_width - right)
    bottom = min(img_height, img_height - bottom)

    if top < bottom and left < right:
        image = image.crop((left, top, right, bottom))

    return image

def remove_text_from_image(image):
    """
    Removes text from the image by blurring detected text regions using EasyOCR.
    
    :param image: The input PIL Image object.
    :return: The PIL Image object with text regions removed.
    """
    reader = easyocr.Reader(['en'])
    img_width, img_height = image.size
    
    # Convert PIL Image to array
    image_array = np.array(image)
    
    # Use EasyOCR to get text bounding boxes
    results = reader.readtext(image_array)
    
    # Create a new image for inpainting
    new_image = image.copy()
    
    # Create a draw object
    draw = ImageDraw.Draw(new_image)
    
    for (bbox, text, prob) in results:
        left, top = int(bbox[0][0]), int(bbox[0][1])
        right, bottom = int(bbox[2][0]), int(bbox[2][1])
        
        # Draw a blurred rectangle over the text region
        text_region = image.crop((left, top, right, bottom))
        blurred_region = text_region.filter(ImageFilter.GaussianBlur(5))
        new_image.paste(blurred_region, (left, top, right, bottom))
    
    return new_image

def slice_image(image, num_rows=3, num_cols=4, output_dir="./sub_images/"):
    """
    Slices the image into a grid of sub-images, removes text from each sub-image, and saves them to the specified directory.
    
    :param image: The input PIL Image object.
    :param num_rows: Number of rows in the grid.
    :param num_cols: Number of columns in the grid.
    :param output_dir: Directory to save the sub-images.
    """
    img_width, img_height = image.size
    sub_img_width = img_width // num_cols
    sub_img_height = img_height // num_rows

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    for row in range(num_rows):
        for col in range(num_cols):
            left = col * sub_img_width
            upper = row * sub_img_height
            right = left + sub_img_width
            lower = upper + sub_img_height
            sub_image = image.crop((left, upper, right, lower))
            
            # Remove text from the sub-image
            sub_image_no_text = remove_text_from_image(sub_image)
            
            sub_image_path = f"{output_dir}sub_image_{row}_{col}.png"
            sub_image_no_text.save(sub_image_path)

    print("Images have been sliced and text removed.")

# Main script
if __name__ == "__main__":
    # Load the image
    image_path = "./vsd-Nevada_attractions-style_Edward_Loper-19jan24.png"
    image = Image.open(image_path)
    
    # Parameters for removing borders
    top = 19
    bottom = 0
    left = 3
    right = 3
    image = remove_borders(image, top=top, bottom=bottom, left=left, right=right)
    image.save("./sub_images/cropped_image.png")
    
    # Slice the image and remove text from each slice
    slice_image(image)
