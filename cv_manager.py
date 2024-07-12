import cv2
import math
import numpy as np
from PyQt5.QtGui import *

class CVManager:
    def loadImage(self, image_path):
        """
        Load an image from a given path using OpenCV.
        """
        return cv2.imread(image_path)

    def saveImage(self, image_path, image,is_filtered):
        """
        Save an image to a given path using OpenCV.
        """
        if not is_filtered:
            image = cv2.cvtColor(image,cv2.COLOR_RGB2BGR)
        return cv2.imwrite(image_path, image)

    def resizeImage(self, image, dim):
        """
        Resize an image to the specified dimensions using OpenCV.
        """
        return cv2.resize(image, (dim[0], dim[1]))

    def toQImage(self, image, image_effect=None):
        """
        Convert an OpenCV image to a QImage with optional image effect.
        """
        image = self.apply_filter(image, image_effect)
        height, width = image.shape[:2]
        if image_effect in ('grey','sketch'):
            bytes_per_line = width
            qimage = QImage(image.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
        else:
            bytes_per_line = width * image.shape[2]
            qimage = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        return qimage

    def toIcon(self, image):
        """
        Convert a QImage to a QIcon.
        """
        image = self.toQImage(image)
        return QIcon(QPixmap(image))

    def apply_filter(self, image, image_effect):
        """
        Apply image effects such as grey, invert, cartoon, blur, or sketch using OpenCV.
        """
        # Grey
        if image_effect == 'grey':
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Invert
        elif image_effect == 'invert':
            return 255 - cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # Cartoon
        elif image_effect == 'cartoon':
            grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            grey = cv2.medianBlur(grey, 1)
            outline = cv2.adaptiveThreshold(grey, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
            color = cv2.bilateralFilter(image, 9, 300, 300)
            cartoon_image = cv2.bitwise_and(color, color, mask=outline)
            return cv2.cvtColor(cartoon_image, cv2.COLOR_BGR2RGB)
        # Blur
        elif image_effect is not None and 'blur' in image_effect:
            blur_size = int(image_effect.split(' ')[1])
            grey = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            return  cv2.GaussianBlur(grey, (blur_size*21-((blur_size-1)*1), blur_size*21-((blur_size-1)*1)), 0)
        # Sketch
        elif image_effect == 'sketch':
            grey_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            inverted = 255 - grey_image
            blured = cv2.GaussianBlur(inverted, (211, 211), 0)
            inverted_back = 255 - blured
            return cv2.divide(grey_image, inverted_back, scale=256)
        else:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image

    def rotateImage(self, image, side):
        """
        Rotate the image clockwise or counterclockwise using OpenCV.
        """
        if side == 'left':
            image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
            return image
        elif side == 'right':
            return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)

    def flipImage(self, image, side):
        """
        Flip the image vertically or horizontally using OpenCV.
        """
        if side == 'v':
            return cv2.flip(image, 0)
        elif side == 'h':
            return cv2.flip(image, 1)

    def cropImage(self, image, start_pos, current_pos):
        """
        Crop the image based on the selected region using OpenCV.
        """
        return image[min(start_pos[1], current_pos[1]) + 3:max(current_pos[1], start_pos[1]) - 3,
                min(start_pos[0], current_pos[0]) + 3:max(current_pos[0], start_pos[0]) - 3]

    def drawImage(self, image, start_pos, current_pos, cropped_image, bounderies):
        """
        Draw an image onto the canvas at the specified position using OpenCV.
        """
        # Adjust coordinates for out-of-bound positions
        x = 0 if start_pos[0] <= 0 or current_pos[0] <= 0 else min(start_pos[0], current_pos[0]) + 3
        x = bounderies[0] - cropped_image.shape[1] if current_pos[0] >= bounderies[0] or start_pos[0] >= bounderies[0] else x
        x_gap = x + cropped_image.shape[1] if current_pos[0] >= bounderies[0] or start_pos[0] >= bounderies[0] else x + cropped_image.shape[1]
        y = 0 if start_pos[1] <= 0 or current_pos[1] <= 0 else min(start_pos[1], current_pos[1]) + 3
        y = bounderies[1] - cropped_image.shape[0] if current_pos[1] >= bounderies[1] or start_pos[1] >= bounderies[1] else y
        y_gap = y + cropped_image.shape[0] if current_pos[1] >= bounderies[1] or start_pos[1] >= bounderies[1] else y + cropped_image.shape[0]

        # Paste the cropped image onto the canvas
        image[y:y_gap, x:x_gap] = cropped_image
        return image

    def moveRect(self, image, start_pos, current_pos, rect):
        """
        Move a rectangular region within the image.
        """
        for y in range(rect[0][1] + 1, rect[1][1] - 1):
            for x in range(rect[0][0] - 1, rect[1][0] + 1)[::-1]:
                image[y][x - 2] = image[y][x]
        return image

    def drawLine(self, image, prev_point, dest_point, color, thickness):
        """
        Draw a line between two points on the image using OpenCV.
        """
        cv2.line(image, prev_point, dest_point, color, thickness, cv2.LINE_AA)

    def drawDashRect(self, image, start_pos, current_pos, color, from_center=None):
        """
        Draw a dashed rectangle on the image.
        """
        x_gap, y_gap = self.getGap(start_pos, current_pos)
        x_dir, y_dir = self.getDirection(start_pos, current_pos)
        if not from_center:
            top_left = start_pos
            top_right = (current_pos[0], start_pos[1])
            bottom_left = (start_pos[0], current_pos[1])
            bottom_right = current_pos
        else:
            x_dst = (from_center[1][0] - from_center[0][0])
            y_dst = (from_center[1][1] - from_center[0][1])
            top_left = (start_pos[0] + x_dst, start_pos[1] + y_dst)
            top_right = (current_pos[0] + x_dst, start_pos[1] + y_dst)
            bottom_left = (start_pos[0] + x_dst, current_pos[1] + y_dst)
            bottom_right = (current_pos[0] + x_dst, current_pos[1] + y_dst)
        dst = 10
        for i in range(math.ceil(abs(x_gap) // dst)):
            cv2.line(image, (top_left[0] + (dst * i * x_dir), top_left[1]),
                     (top_left[0] + (dst // 3 + (dst * i)) * x_dir, top_left[1]), color, 1, cv2.LINE_AA)
            cv2.line(image, (bottom_left[0] + (dst * i * x_dir), bottom_left[1]),
                     (bottom_left[0] + (dst // 3 + (dst * i)) * x_dir, bottom_left[1]), color, 1, cv2.LINE_AA)
        for i in range(math.ceil(abs(y_gap) // dst)):
            cv2.line(image, (top_right[0], top_right[1] + (dst * i * y_dir)),
                     (top_right[0], top_right[1] + (dst // 3 + (dst * i)) * y_dir), color, 1, cv2.LINE_AA)
            cv2.line(image, (top_left[0], top_left[1] + (dst * i * y_dir)),
                     (top_left[0], top_left[1] + (dst // 3 + (dst * i)) * y_dir), color, 1, cv2.LINE_AA)
        return (top_left, bottom_right)

    def drawElipse(self, image, start_pos, current_pos, color, thickness, fill_color, is_filled):
        """
        Draw an ellipse on the image.
        """
        x_mid, y_mid = self.getMid(start_pos, current_pos)
        x_gap, y_gap = self.getGap(start_pos, current_pos)
        radius = (abs(x_gap // 2), abs(y_gap // 2))
        if is_filled:
            cv2.ellipse(image, (x_mid, y_mid), radius, 0, 0, 360, fill_color, -1)
        cv2.ellipse(image, (x_mid, y_mid), radius, 0, 0, 360, color, thickness)

    def drawTriangle(self, image, start_pos, current_pos, color, thickness, fill_color, is_filled=False):
        """
        Draw a triangle on the image.
        """
        top = ((start_pos[0] + current_pos[0]) // 2, start_pos[1])
        base_left = (start_pos[0], current_pos[1])
        base_right = current_pos
        if not self.getYDirection(start_pos[1], current_pos[1]):
            top = [(start_pos[0] + current_pos[0]) // 2, current_pos[1]]
            base_left = [start_pos[0], start_pos[1]]
            base_right = [current_pos[0], start_pos[1]]
        pts = np.array([top, base_left, base_right], np.int32)
        pts = pts.reshape((-1, 1, 2))
        if is_filled:
            cv2.fillPoly(image, [pts], fill_color)
        cv2.polylines(image, [pts], True, color, thickness)

    def drawRectangle(self, image, start_pos, current_pos, color, thickness, fill_color=False, is_filled=False):
        """
        Draw a rectangle on the image.
        """
        if is_filled:
            cv2.rectangle(image, start_pos, current_pos, fill_color, -1, cv2.LINE_AA)
        cv2.rectangle(image, start_pos, current_pos, color, thickness, cv2.LINE_AA)

    def drawPentagon(self, image, start_pos, current_pos, color, thickness, fill_color, is_filled):
        """
        Draw a pentagon on the image.
        """
        x_mid, y_mid = self.getMid(start_pos, current_pos)
        x_gap, y_gap = self.getGap(start_pos, current_pos)

        pt1 = (x_mid, start_pos[1])
        pt2 = (start_pos[0], start_pos[1] - y_gap // 4)
        pt3 = (start_pos[0] - (x_gap // 4), current_pos[1])
        pt4 = (current_pos[0] + (x_gap // 4), current_pos[1])
        pt5 = (current_pos[0], start_pos[1] - ((y_gap // 4) * 3))
        if not self.getYDirection(start_pos[1], current_pos[1]):
            pt1 = (x_mid, current_pos[1])
            pt2 = (start_pos[0], start_pos[1] + y_gap // 4)
            pt3 = (start_pos[0] - (x_gap // 4), start_pos[1])
            pt4 = (current_pos[0] + (x_gap // 4), start_pos[1])
            pt5 = (current_pos[0], start_pos[1] + ((y_gap // 4) * 3))
        pts = np.array([pt1, pt2, pt3, pt4, pt5], np.int32)
        pts = pts.reshape((-1, 1, 2))
        if is_filled:
            cv2.fillPoly(image, [pts], fill_color)
        cv2.polylines(image, [pts], True, color, thickness)

    def drawHexagon(self, image, start_pos, current_pos, color, thickness, fill_color, is_filled):
        """
        Draw a hexagon on the image.
        """
        x_mid, y_mid = self.getMid(start_pos, current_pos)
        x_gap, y_gap = self.getGap(start_pos, current_pos)

        pt1 = (x_mid, start_pos[1])
        pt2 = (start_pos[0], start_pos[1] - y_gap // 4)
        pt3 = (start_pos[0], start_pos[1] - ((y_gap // 4) * 3))
        pt4 = (x_mid, current_pos[1])
        pt5 = (current_pos[0], start_pos[1] - ((y_gap // 4) * 3))
        pt6 = (current_pos[0], start_pos[1] - y_gap // 4)

        pts = np.array([pt1, pt2, pt3, pt4, pt5, pt6], np.int32)
        pts = pts.reshape((-1, 1, 2))
        if is_filled:
            cv2.fillPoly(image, [pts], fill_color)
        cv2.polylines(image, [pts], True, color, thickness)

    def drawDiamond(self, image, start_pos, current_pos, color, thickness, fill_color, is_filled):
        """
        Draw a diamond shape on the image.
        """
        x_mid, y_mid = self.getMid(start_pos, current_pos)

        top = (x_mid, start_pos[1])
        left = (start_pos[0], y_mid)
        right = (current_pos[0], y_mid)
        bottom = (x_mid, current_pos[1])

        pts = np.array([top, right, bottom, left], np.int32)
        pts = pts.reshape((-1, 1, 2))
        if is_filled:
            cv2.fillPoly(image, [pts], fill_color)
        cv2.polylines(image, [pts], True, color, thickness)

    def getYDirection(self, y1, y2):
        """
        Get the direction of the y-coordinate.
        """
        return True if y1 < y2 else False

    def getMid(self, start_pos, current_pos):
        """
        Get the midpoint between two points.
        """
        x_mid = (current_pos[0] + start_pos[0]) // 2
        y_mid = (current_pos[1] + start_pos[1]) // 2
        return x_mid, y_mid

    def getGap(self, start_pos, current_pos):
        """
        Get the gap between two points.
        """
        x_gap = start_pos[0] - current_pos[0]
        y_gap = start_pos[1] - current_pos[1]
        return x_gap, y_gap

    def getDirection(self, start_pos, current_pos):
        """
        Get the direction between two points.
        """
        x_dir = 1 if start_pos[0] < current_pos[0] else -1
        y_dir = 1 if start_pos[1] < current_pos[1] else -1
        return x_dir, y_dir

    # def drawCircle(self,image,prev_point,dest_point,color,thickness):
    #     x_shift = 1 if prev_point[0] < dest_point[0] else -1
    #     y_shift = 1 if prev_point[1] < dest_point[1] else -1
    #     radius = abs(prev_point[0]//2-dest_point[0]//2)
    #     center = (prev_point[0]+radius*x_shift,prev_point[1]+radius*y_shift)
    #     cv2.circle(image, center, radius, color, thickness,cv2.LINE_AA)
