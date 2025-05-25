import requests
import time


def mathpix_pdf_to_tex_zip(pdf_file, app_id, app_key, output_zip=None):
    url = 'https://api.mathpix.com/v3/pdf'
    headers = {'app_id': app_id, 'app_key': app_key}

    with open(pdf_file, 'rb') as file:
        files = {'file': file}
        response = requests.post(url, files=files, headers=headers)
        response_data = response.json()

        if response.status_code != 200 or 'pdf_id' not in response_data:
            raise RuntimeError(f"Error uploading PDF: {response_data.get('error', 'Unknown error')}")
        pdf_id = response_data['pdf_id']
        print(f"PDF uploaded successfully. PDF ID: {pdf_id}")

    status_url = f"{url}/{pdf_id}"
    while True:
        status_response = requests.get(status_url, headers=headers)
        status_data = status_response.json()
        status = status_data.get('status')
        if status == 'completed':
            print("PDF conversion completed.")
            break
        elif status == 'error':
            raise RuntimeError(f"Error during processing: {status_data.get('error')}")
        else:
            print("Processing... please wait.")
            time.sleep(5)

    tex_zip_url = f"{url}/{pdf_id}.tex"
    zip_response = requests.get(tex_zip_url, headers=headers)

    if zip_response.status_code == 200:
        zip_filename = output_zip if output_zip else f"{pdf_id}.tex.zip"
        with open(zip_filename, "wb") as f:
            f.write(zip_response.content)
        print(f"LaTeX zip file saved as {zip_filename}")
        return zip_filename
    else:
        raise RuntimeError(f"Failed to download LaTeX zip: {zip_response.status_code}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 5:
        print("Usage: python mathpix.py input.pdf app_id app_key output.zip")
    else:
        mathpix_pdf_to_tex_zip(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
