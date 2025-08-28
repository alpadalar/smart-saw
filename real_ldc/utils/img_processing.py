import os

import cv2
import numpy as np
import torch
import kornia as kn

# Kare çizmek için kenar uzunluğunu belirleyin
side_length = 300  # Örneğin 50 piksel


# Kare çizimi için center noktası ve kenar uzunluğunu kullanarak köşe noktalarını hesaplayın
def draw_centered_square(image, center_x, center_y, side_length, color=(0, 255, 0), thickness=2):
    top_left_x = center_x - side_length // 2
    top_left_y = center_y - side_length // 2
    bottom_right_x = center_x + side_length // 2
    bottom_right_y = center_y + side_length // 2

    top_left = (top_left_x, top_left_y)
    bottom_right = (bottom_right_x, bottom_right_y)

    cv2.rectangle(image, top_left, bottom_right, color, thickness)


def image_normalization(img, img_min=0, img_max=255,
                        epsilon=1e-12):
    """This is a typical image normalization function
    where the minimum and maximum of the image is needed
    source: https://en.wikipedia.org/wiki/Normalization_(image_processing)

    :param img: an image could be gray scale or color
    :param img_min:  for default is 0
    :param img_max: for default is 255

    :return: a normalized image, if max is 255 the dtype is uint8
    """

    img = np.float32(img)
    # whenever an inconsistent image
    img = (img - np.min(img)) * (img_max - img_min) / \
          ((np.max(img) - np.min(img)) + epsilon) + img_min
    return img


def count_parameters(model=None):
    if model is not None:
        return sum(p.numel() for p in model.parameters() if p.requires_grad)
    else:
        print("Error counting model parameters line 32 img_processing.py")
        raise NotImplementedError


def save_image_batch_to_disk(tensor, output_dir, file_names, output_txt_file,
                             img_shape=None, source_root=None):
    os.makedirs(output_dir, exist_ok=True)
    fuse_name = 'fused'
    av_name = 'avg'
    tensor2 = None
    tmp_img2 = None
    output_dir_f = os.path.join(output_dir, fuse_name)
    output_dir_a = os.path.join(output_dir, av_name)
    os.makedirs(output_dir_f, exist_ok=True)
    os.makedirs(output_dir_a, exist_ok=True)
    # Alt klasörleri oluştur
    os.makedirs(os.path.join(output_dir_f, 'Odakli'), exist_ok=True)
    os.makedirs(os.path.join(output_dir_f, 'Odaksiz'), exist_ok=True)
    os.makedirs(os.path.join(output_dir_f, 'Odakli', 'Hasarli'), exist_ok=True)
    os.makedirs(os.path.join(output_dir_f, 'Odakli', 'Saglam'), exist_ok=True)

    # 255.0 * (1.0 - em_a)
    edge_maps = []
    for i in tensor:
        tmp = torch.sigmoid(i).cpu().detach().numpy()
        edge_maps.append(tmp)
    tensor = np.array(edge_maps)
    # print(f"tensor shape: {tensor.shape}")

    # image_shape güvenli dönüştürme
    safe_shapes = []
    for x in img_shape:
        if hasattr(x, 'cpu'):
            safe_shapes.append(x.cpu().detach().numpy())
        else:
            safe_shapes.append(np.array(x))
    image_shape = safe_shapes
    # (H, W) -> (W, H)
    image_shape = [[y, x] for x, y in zip(image_shape[0], image_shape[1])]

    assert len(image_shape) == len(file_names)

    idx = 0
    for i_shape, file_name in zip(image_shape, file_names):
        tmp = tensor[:, idx, ...]
        tmp2 = tensor2[:, idx, ...] if tensor2 is not None else None
        # tmp = np.transpose(np.squeeze(tmp), [0, 1, 2])
        tmp = np.squeeze(tmp)
        tmp2 = np.squeeze(tmp2) if tensor2 is not None else None

        # Iterate our all 7 NN outputs for a particular image
        preds = []
        fuse_num = tmp.shape[0] - 1
        for i in range(tmp.shape[0]):
            tmp_img = tmp[i]
            tmp_img = np.uint8(image_normalization(tmp_img))
            tmp_img = cv2.bitwise_not(tmp_img)
            # tmp_img[tmp_img < 0.0] = 0.0
            # tmp_img = 255.0 * (1.0 - tmp_img)
            if tmp2 is not None:
                tmp_img2 = tmp2[i]
                tmp_img2 = np.uint8(image_normalization(tmp_img2))
                tmp_img2 = cv2.bitwise_not(tmp_img2)

            # Resize prediction to match input image size
            if not tmp_img.shape[1] == i_shape[0] or not tmp_img.shape[0] == i_shape[1]:
                tmp_img = cv2.resize(tmp_img, (i_shape[0], i_shape[1]))
                tmp_img2 = cv2.resize(tmp_img2, (i_shape[0], i_shape[1])) if tmp2 is not None else None

            if tmp2 is not None:
                tmp_mask = np.logical_and(tmp_img > 128, tmp_img2 < 128)
                tmp_img = np.where(tmp_mask, tmp_img2, tmp_img)
                preds.append(tmp_img)

            else:
                preds.append(tmp_img)

            if i == fuse_num:
                # print('fuse num',tmp.shape[0], fuse_num, i)
                fuse = tmp_img
                fuse = fuse.astype(np.uint8)
                if tmp_img2 is not None:
                    fuse2 = tmp_img2
                    fuse2 = fuse2.astype(np.uint8)
                    # fuse = fuse-fuse2
                    fuse_mask = np.logical_and(fuse > 128, fuse2 < 128)
                    fuse = np.where(fuse_mask, fuse2, fuse)

                    # print(fuse.shape, fuse_mask.shape)

        # Get the mean prediction of all the 7 outputs
        average = np.array(preds, dtype=np.float32)
        average = np.uint8(np.mean(average, axis=0))
        output_file_name_f = os.path.join(output_dir_f, file_name)
        output_file_name_a = os.path.join(output_dir_a, file_name)

        output_file_name_odakli = os.path.join(output_dir_f, "Odakli", file_name)
        output_file_name_odaksiz = os.path.join(output_dir_f, "Odaksiz", file_name)

        output_file_name_hasarli = os.path.join(output_dir_f, "Odakli", "Hasarli", file_name)
        output_file_name_saglam = os.path.join(output_dir_f, "Odakli", "Saglam", file_name)


        if len(fuse.shape) == 3 and fuse.shape[2] == 3:  # Check if fuse is a 3-channel image
            fuse_gray = cv2.cvtColor(fuse, cv2.COLOR_BGR2GRAY)
        else:
            fuse_gray = fuse  # If fuse is already grayscale, no need to convert

        if len(average.shape) == 3 and average.shape[2] == 3:  # Check if average is a 3-channel image
            average_gray = cv2.cvtColor(average, cv2.COLOR_BGR2GRAY)
        else:
            average_gray = average

        # Invert the image
        fuse_gray = cv2.bitwise_not(fuse_gray)
        average_gray = cv2.bitwise_not(average_gray)

        _, binary_fuse = cv2.threshold(fuse_gray, 180, 255, cv2.THRESH_BINARY)
        _, binary_avg = cv2.threshold(average_gray, 180, 255, cv2.THRESH_BINARY)

        y_indices_fuse, x_indices_fuse = np.where(binary_fuse == 255)
        y_indices_avg, x_indices_avg = np.where(binary_avg == 255)

        if len(y_indices_fuse) == 0:
            print("Kenar bulunamadı")
        else:
            # üstten 10 piksel ihmal ediyoruz
            valid_indices = y_indices_fuse > 0
            y_indices_fuse = y_indices_fuse[valid_indices]
            x_indices_fuse = x_indices_fuse[valid_indices]

            topmost_y_fuse = np.min(y_indices_fuse)
            topmost_x_index_fuse = np.argmin(y_indices_fuse)
            topmost_x_fuse = x_indices_fuse[topmost_x_index_fuse]
            cv2.circle(fuse, (topmost_x_fuse, topmost_y_fuse), 5, (0, 0, 255), -1)
            cv2.putText(fuse, "y: " + str(topmost_y_fuse), (topmost_x_fuse, topmost_y_fuse),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            # Kareyi çiz
            # draw_centered_square(fuse, topmost_x_fuse, topmost_y_fuse, side_length)

            # Kaynak görüntü yolu
            base_source = source_root if source_root is not None else 'data'
            source_file_path = os.path.join(base_source, file_name.replace('png', 'jpg'))
            copy_image = cv2.imread(source_file_path)
            # odak noktasına denk gelen görsellerin belirlenmesi işlemi
            if topmost_x_fuse > 30 and topmost_x_fuse < 360:
                #with open(output_txt_file, 'a') as f: #txt ye yazdırma kodları
                  #  f.write(f"{file_name}\n")
                cv2.imwrite(output_file_name_odakli, copy_image)

                #bu kısımda hasarlıları otomatik tespit etme işlemi yapılmaktadır
                print(f"topmost_y_fuse: {topmost_y_fuse}")
                if topmost_y_fuse > 95:
                    cv2.imwrite(output_file_name_hasarli, copy_image)
                else:
                    cv2.imwrite(output_file_name_saglam, copy_image)

            else:
                cv2.imwrite(output_file_name_odaksiz, copy_image)

        if len(y_indices_avg) == 0:
            print("Kenar bulunamadı")
        else:
            # üstten 10 piksel ihmal ediyoruz
            valid_indices = y_indices_fuse > 0
            y_indices_fuse = y_indices_fuse[valid_indices]
            x_indices_fuse = x_indices_fuse[valid_indices]

            topmost_y_avg = np.min(y_indices_avg)
            topmost_x_index_avg = np.argmin(y_indices_avg)
            topmost_x_avg = x_indices_avg[topmost_x_index_avg]
            cv2.circle(average, (topmost_x_avg, topmost_y_avg), 5, (0, 0, 255), -1)
            cv2.putText(average, "y: " + str(topmost_y_avg), (topmost_x_avg, topmost_y_avg),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        cv2.imwrite(output_file_name_f, fuse)
        cv2.imwrite(output_file_name_a, average)

        print(
            f"Image: {file_name} - Fuse: {topmost_x_fuse}, {topmost_y_fuse} - Avg: {topmost_x_avg}, {topmost_y_avg}")

        idx += 1
        return {
            "image_name": file_name,
            "fuse_x": topmost_x_fuse,
            "fuse_y": topmost_y_fuse,
            "avg_x": topmost_x_avg,
            "avg_y": topmost_y_avg
        }
