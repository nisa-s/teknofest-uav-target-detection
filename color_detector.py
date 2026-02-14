#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np

class ColorDetector(Node):
    def __init__(self):
        super().__init__('color_detector')
        self.bridge = CvBridge()
        
        self.subscription = self.create_subscription(
            Image,
            '/camera/image',
            self.image_callback,
            10
        )
        
        self.get_logger().info('🎯 Hedef Tespit Sistemi Başlatıldı!')
    
    def image_callback(self, msg):
        # ROS Image -> OpenCV
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        
        # KIRMIZI MASK (iki aralık)
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)
        
        # MAVİ MASK
        lower_blue = np.array([100, 100, 100])
        upper_blue = np.array([130, 255, 255])
        mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
        
        # Hedefleri tespit et
        red_center = self.find_target(mask_red, cv_image, (0, 0, 255), "KIRMIZI 4x4m")
        blue_center = self.find_target(mask_blue, cv_image, (255, 0, 0), "MAVI 2x2m")
        
        # Görselleştirme
        cv2.imshow('Hedef Tespiti', cv_image)
        cv2.imshow('Kirmizi Mask', mask_red)
        cv2.imshow('Mavi Mask', mask_blue)
        cv2.waitKey(1)
        
        # Sonuçları yayınla
        if red_center:
            self.get_logger().info(f'🔴 KIRMIZI HEDEF: {red_center}')
        if blue_center:
            self.get_logger().info(f'🔵 MAVI HEDEF: {blue_center}')
    
    def find_target(self, mask, image, color, name):
        # Kontur bulma
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) == 0:
            return None
        
        # En büyük konturu al
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)
        
        # Minimum alan kontrolü
        if area < 1000:
            return None
        
        # Merkez hesapla
        M = cv2.moments(largest)
        if M["m00"] == 0:
            return None
        
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        
        # Çiz
        cv2.drawContours(image, [largest], -1, color, 3)
        cv2.circle(image, (cx, cy), 10, color, -1)
        cv2.putText(image, name, (cx-80, cy-20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        cv2.putText(image, f'({cx}, {cy})', (cx-50, cy+30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        return (cx, cy)

def main(args=None):
    rclpy.init(args=args)
    node = ColorDetector()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
