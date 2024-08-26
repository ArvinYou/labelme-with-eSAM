import imgviz
import numpy as np
import onnxruntime as ort
import skimage

from labelme.logger import logger
from PyQt5.QtWidgets import QMessageBox

class MessageBox:
    def __init__(self):
        pass

    def showMessageBox(self, title, message):
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec_()


msg_box = MessageBox()

def get_available_providers(cuda_num=0):
    check_list = ort.get_available_providers()
    try:
        import torch
        if 'CUDAExecutionProvider' in check_list:
            logger.info(f"CUDA {cuda_num} is available and can be used.")
            providers = [('CUDAExecutionProvider', {'device_id': cuda_num})]
            # msg_box.showMessageBox(
            #     "Info", f"GPU {cuda_num} is available and will be used.\nInference device switched to {torch.cuda.get_device_name(cuda_num)} in Everything mode."
            # )
            return providers
    except ImportError as e:
        msg_box.showMessageBox(
            "ImportError", f"Failed to import torch: {e}"
        )
        logger.error(f"ImportError: {e}")
        return ['CPUExecutionProvider']
    except Exception as e:
        msg_box.showMessageBox(
            "Error", f"Error checking GPU availability: {e}"
        )
        logger.error(f"Error checking GPU availability: {e}")
    
    msg_box.showMessageBox(
        "Warning", "CUDAExecutionProvider is not available, using CPUExecutionProvider."
    )
    return ['CPUExecutionProvider']


def set_providers(mode): 
    if mode == 0:
        msg_box.showMessageBox(
            "Info", "CPU Mode Selected: CPUExecutionProvider is available and will be used."
        )
        return ['CPUExecutionProvider']
    return get_available_providers(mode - 1)

def getAiInferenceOption():
    return ort.get_available_providers()

def _get_contour_length(contour):
    contour_start = contour
    contour_end = np.r_[contour[1:], contour[0:1]]
    return np.linalg.norm(contour_end - contour_start, axis=1).sum()

def compute_polygon_from_mask(mask):
    contours = skimage.measure.find_contours(np.pad(mask, pad_width=1))
    if len(contours) == 0:
        msg_box.showMessageBox(
            "Warning","No contour found, so returning empty polygon."
        )  
        return np.empty((0, 2), dtype=np.float32)

    contour = max(contours, key=_get_contour_length)
    POLYGON_APPROX_TOLERANCE = 0.08
    polygon = skimage.measure.approximate_polygon(
        coords=contour,
        tolerance=np.ptp(contour, axis=0).max() * POLYGON_APPROX_TOLERANCE,
    )
    polygon = np.clip(polygon, (0, 0), (mask.shape[0] - 1, mask.shape[1] - 1))
    polygon = polygon[:-1]  # drop last point that is duplicate of first point

    if 0:
        import PIL.Image

        image_pil = PIL.Image.fromarray(imgviz.gray2rgb(imgviz.bool2ubyte(mask)))
        imgviz.draw.line_(image_pil, yx=polygon, fill=(0, 255, 0))
        for point in polygon:
            imgviz.draw.circle_(image_pil, center=point, diameter=10, fill=(0, 255, 0))
        imgviz.io.imsave("contour.jpg", np.asarray(image_pil))

    return polygon[:, ::-1]  # yx -> xy

def compute_multipolygon_from_mask(mask):
    # Find contours in the mask
    contours = skimage.measure.find_contours(np.pad(mask, pad_width=1))
    if len(contours) == 0:
        logger.warning("No contour found, so returning empty polygon!")
        return np.empty((0, 2), dtype=np.float32)
    
    polygons = []
    
    for contour in contours:
        POLYGON_APPROX_TOLERANCE = 0.08
        polygon = skimage.measure.approximate_polygon(
            coords=contour,
            tolerance=np.ptp(contour, axis=0).max() * POLYGON_APPROX_TOLERANCE,
        )
        polygon = np.clip(polygon, (0, 0), (mask.shape[0] - 1, mask.shape[1] - 1))
        polygon = polygon[:-1]  # drop last point that is duplicate of first point
        polygons.append(polygon[:, ::-1])  # yx -> xy

    if 0:
        import PIL.Image

        image_pil = PIL.Image.fromarray(imgviz.gray2rgb(imgviz.bool2ubyte(mask)))
        imgviz.draw.line_(image_pil, yx=polygon, fill=(0, 255, 0))
        for point in polygon:
            imgviz.draw.circle_(image_pil, center=point, diameter=10, fill=(0, 255, 0))
        imgviz.io.imsave("contour.jpg", np.asarray(image_pil))

    return polygons

 