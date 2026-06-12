import os
import json
import requests
import base64

from app.utils.settings import secrets as s
from app.utils.logger import get_logger

app_logger = get_logger(__name__)


def ocr_pdf_to_json(pdf_path, output_dir):
    """
    Парсинг pdf в json файл, с учетом картинок, таблиц и двухколоночных страниц.
    Примечание: 1 страница 0.5 рублей
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(pdf_path, "rb") as file:
        encoded_file = base64.b64encode(file.read()).decode('utf-8')

    name = pdf_path.split('/')[-1].split('.')[0]
    response = requests.post(
        f"{s.vsegpt_base_url}/extract_text",
        headers={
            "Authorization": f"Bearer {s.vsegpt_api_key}"
        },
        json={
            "encoded_base64_file": encoded_file,
            "filename": f"{name}.pdf",
            "model": "utils/pdf-ocr-1.0",
            "return_images": True,
        }
    )

    with open(os.path.join(output_dir, f'{name}.json'), "w", encoding='utf8') as f:
        json.dump(response.json(), f, indent=4, ensure_ascii=False)


def handle_images_from_json(input_dir, output_dir):
    app_logger.info(f"Reading JSON file: {input_dir}")
    with open(input_dir, 'r', encoding='utf-8') as f:
        data = json.load(f)

    app_logger.info(f"Total pages: {len(data['pages'])}")

    image_count = 0
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    # Iterate through each page
    for page_idx, page in enumerate(data['pages']):
        page_num = page.get('page_number', str(page_idx))

        if 'images' in page and page['images']:
            app_logger.info(f"Page {page_idx} (page {page_num}) has {len(page['images'])} images")

            # Iterate through each image in the page
            for img_idx, image_info in enumerate(page['images']):
                if 'image_base64' in image_info and 'id' in image_info:
                    try:
                        # Extract the base64 data and image id
                        base64_data = image_info['image_base64']
                        image_id = image_info['id']

                        # Remove the data URI prefix if present
                        if base64_data.startswith('data:image'):
                            # Split at comma and take the second part (actual base64 data)
                            base64_data = base64_data.split(',')[1]

                        # Decode the base64 data
                        image_data = base64.b64decode(base64_data)

                        # Create filename using the pattern: page-{number}-{id}.jpeg
                        # Extract just the ID part if it contains a path
                        clean_id = os.path.basename(image_id)
                        if not clean_id.lower().endswith(('.jpeg', '.jpg')):
                            clean_id = clean_id + '.jpeg'

                        filename = f"page-{page_num}-{clean_id}"
                        file_path = os.path.join(output_dir, filename)
                        app_logger.info(file_path)

                        # Save the image
                        with open(file_path, 'wb') as img_file:
                            img_file.write(image_data)

                        app_logger.info(f"Saved: {filename}")
                        image_count += 1

                    except Exception as e:
                        app_logger.info(f"Error processing image on page {page_idx}, image {img_idx}: {str(e)}")
        else:
            app_logger.info(f"Page {page_idx} (page {page_num}) has no images")
    app_logger.info(f"Total images extracted: {image_count}")
