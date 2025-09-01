from __future__ import print_function

import os
import shutil
import time
from datetime import datetime
import cv2

import numpy as np
import torch
from torch.utils.data import DataLoader

from dataset import TestDataset
from modelB4 import LDC
from utils.img_processing import save_image_batch_to_disk, count_parameters


def open_first_available_camera(max_index: int = 3):
    for index in range(max_index + 1):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            return cap
        cap.release()
    return None


def test(checkpoint_path, model, device, output_dir):
    if not os.path.isfile(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_path}")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_txt_file = f"output_filenames_{timestamp}.txt"

    print(f"Restoring weights from: {checkpoint_path}")
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.eval()

    # input-images klasöründen oku
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(base_dir))
    input_dir = os.path.join(project_root, "input-images")
    if not os.path.isdir(input_dir):
        print(f"Error: input directory not found: {input_dir}")
        return

    dataset = TestDataset(
        data_root=input_dir,
        test_data='CLASSIC',
        mean_bgr=[103.939, 116.779, 123.68],
        img_height=512,
        img_width=512,
        test_list=None,
        arg=type('args', (), {'test_img_width': 512, 'test_img_height': 512})
    )
    loader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=0)

    try:
        with torch.no_grad():
            for batch in loader:
                images = batch['images'].to(device)
                file_name = batch['file_names']
                image_shape = batch['image_shape']

                if device.type == 'cuda':
                    torch.cuda.synchronize()
                preds = model(images)
                if device.type == 'cuda':
                    torch.cuda.synchronize()

                save_image_batch_to_disk(preds, output_dir, file_name, output_txt_file, image_shape, source_root=input_dir)
                torch.cuda.empty_cache()

    finally:
        cv2.destroyAllWindows()


def main():
    # Configuration variables
    mean_pixel_values = [103.939, 116.779, 123.68, 137.86]
    test_inf = {
        'img_height': 512,
        'img_width': 512,
        'test_list': None,
        'train_list': None,
        'data_dir': 'data',  # mean_rgb
        'yita': 0.5
    }
    workers = 8
    img_height = 512
    img_width = 512
    # Bu dosyanın dizinini baz alarak yolları oluştur
    base_dir = os.path.dirname(os.path.abspath(__file__))
    checkpoint_path = os.path.join(base_dir, "checkpoints/BIPED/16/16_model.pth")
    output_dir = os.path.join(base_dir, "rsults")  # Tek bir results klasörü
    TEST_DATA = 'CLASSIC'

    print(f"Number of GPUs available: {torch.cuda.device_count()}")
    print(f"Pytorch version: {torch.__version__}")

    # Get computing device
    device = torch.device('cpu' if torch.cuda.device_count() == 0 else 'cuda')

    model = LDC().to(device)

    # Remove path if exists
    shutil.rmtree(output_dir, ignore_errors=True)
    print(f"Output directory: {output_dir}")
    test(checkpoint_path, model, device, output_dir)

    # Count parameters
    num_param = count_parameters(model)
    print('-------------------------------------------------------')
    print('LDC parameters:')
    print(num_param)
    print('-------------------------------------------------------')


if __name__ == '__main__':
    main()
