from PIL import Image
import cv2
import numpy as np
import os
import requests
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import face_recognition

def authenticate():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)
    return drive

def get_images(drive, folder_link):
    images = []

    def search_in_folder(folder_id):
        query = f"'{folder_id}' in parents and trashed=false"
        file_list = drive.ListFile({'q': query}).GetList()

        for file in file_list:
            if file['mimeType'] in ['image/jpeg', 'image/png']:
                images.append(file)

            if file['mimeType'] == 'application/vnd.google-apps.folder':
                search_in_folder(file['id'])

    folder_id = folder_link.split('/')[-1]
    search_in_folder(folder_id)
    return images

def process_image(file):
    try:
        print(f"Processing image: {file['title']}")
        file.GetContentFile('temp.jpg')  # Download the image to a temporary file
        img_array = face_recognition.load_image_file('temp.jpg')
        face_locations = face_recognition.face_locations(img_array)

        if len(face_locations) > 0:
            print(f"Face locations found in image: {file['title']}")
            my_image = face_recognition.load_image_file('face.jpeg')
            my_face_encoding = face_recognition.face_encodings(my_image)[0]
            face_encodings = face_recognition.face_encodings(img_array, face_locations)

            for face_encoding, face_location in zip(face_encodings, face_locations):
                match = face_recognition.compare_faces([my_face_encoding], face_encoding)
                if match[0]:
                    print(f"Face match found in image: {file['title']}")
                    image_name = file['title']
                    image_name = image_name.replace(" ", "_")  # Replace spaces with underscores
                    image_name = os.path.join("with_me", image_name)  # Create full path to save image
                    Image.open('temp.jpg').save(image_name)
                    break
                else:
                    print(f"No match found in image: {file['title']}")
        else:
            print(f"No face locations found in image: {file['title']}")

        os.remove('temp.jpg')  # Remove the temporary file after processing
    except Exception as e:
        print(f"Error processing image {file['title']}: {e}")
        os.remove('temp.jpg')  # Remove the temporary file on error

if __name__ == "__main__":
    if not os.path.exists("with_me"):
        os.makedirs("with_me")

    drive = authenticate()
    folder_link = "https://drive.google.com/drive/folders/1yE5zvrfcWKbFxAulWnkTj02EJBcHGtR-"
    images = get_images(drive, folder_link)

    if images:
        print(f"Found {len(images)} images in the folder.")

        reference_face_image_path = "face.jpeg"

        for file in images:
            process_image(file)
    else:
        print("No images in the folder.")
