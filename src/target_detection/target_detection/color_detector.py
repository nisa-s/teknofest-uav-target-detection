#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np
import time

class ColorDetector(Node):
    def __init__(self):
        super().__init__('color_detector')
        
        self.bridge = CvBridge()
        
        # Kamera parametreleri
        self.declare_parameter('image_width', 800)
        self.declare_parameter('image_height', 600)
        self.declare_parameter('camera_fov', 1.3963)  # 80 derece (radyan)
        self.declare_parameter('altitude', 10.0)
        
        self.img_width = self.get_parameter('image_width').value
        self.img_height = self.get_parameter('image_height').value
        self.fov = self.get_parameter('camera_fov').value
        self.altitude = self.get_parameter('altitude').value
        
        # Piksel başına metre hesapla
        self.meters_per_pixel = self.calculate_meters_per_pixel()
        
        # Log throttle için
        self.last_log_time = time.time()
        self.log_interval = 5.0  # 5 saniye
        
        self.subscription = self.create_subscription(
            Image,
            '/camera/image',
            self.image_callback,
            10
        )
        
        self.get_logger().info('Color Detector başlatıldı!')
        self.get_logger().info(f'Yükseklik: {self.altitude}m')
        self.get_logger().info(f'Piksel başına: {self.meters_per_pixel:.4f} metre')
        self.get_logger().info(f'Log aralığı: {self.log_interval} saniye')
    
    def calculate_meters_per_pixel(self):
        """Kamera FOV ve yüksekliğe göre piksel/metre oranını hesapla"""
        ground_width = 2 * self.altitude * np.tan(self.fov / 2)
        meters_per_px = ground_width / self.img_width
        self.get_logger().info(f'Yer genişliği: {ground_width:.2f}m')
        return meters_per_px
    
    def should_log(self):
        """5 saniyede bir log yazılmasına izin ver"""
        current_time = time.time()
        if current_time - self.last_log_time >= self.log_interval:
            self.last_log_time = current_time
            return True
        return False
    
    def image_callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        
        # KIRMIZI MASK - GENİŞ ARALIK
        lower_red1 = np.array([0, 50, 50])
        upper_red1 = np.array([15, 255, 255])
        lower_red2 = np.array([165, 50, 50])
        upper_red2 = np.array([180, 255, 255])
        
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)
        
        # MAVİ MASK - GENİŞ ARALIK
        lower_blue = np.array([90, 100, 100])
        upper_blue = np.array([130, 255, 255])
        mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
        
        # Morfolojik işlemler (noise temizleme)
        kernel = np.ones((5,5), np.uint8)
        mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_CLOSE, kernel)
        mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_OPEN, kernel)
        mask_blue = cv2.morphologyEx(mask_blue, cv2.MORPH_CLOSE, kernel)
        mask_blue = cv2.morphologyEx(mask_blue, cv2.MORPH_OPEN, kernel)
        
        # Hedefleri tespit et VE alan hesapla
        red_info = self.find_target_with_area(mask_red, cv_image, (0, 0, 255), "KIRMIZI")
        blue_info = self.find_target_with_area(mask_blue, cv_image, (255, 0, 0), "MAVI")
        
        # Görselleştirme (her frame)
        cv2.imshow('Hedef Tespiti', cv_image)
        cv2.imshow('Kirmizi Mask', mask_red)
        cv2.imshow('Mavi Mask', mask_blue)
        cv2.waitKey(1)
        
        # Log (5 saniyede bir)
        if self.should_log():
            self.get_logger().info('═' * 80)
            
            if red_info:
                center, area_px, area_m2 = red_info
                EXPECTED_RED = 0.433  # Uluslararası: 1m kenar üçgen
                error = abs(area_m2 - EXPECTED_RED)
                accuracy = (1 - min(error / EXPECTED_RED, 1.0)) * 100
                self.get_logger().info(
                    f'🔴 KIRMIZI (Üçgen 1m) → Merkez: {center}, '
                    f'Alan: {area_m2:.3f} m² ({area_px:.0f} px²) '
                    f'| Beklenen: {EXPECTED_RED:.3f} m² | Hata: ±{error:.3f} m² | Doğruluk: %{accuracy:.1f}'
                )
            else:
                self.get_logger().warn('🔴 KIRMIZI hedef tespit edilemedi')
            
            if blue_info:
                center, area_px, area_m2 = blue_info
                EXPECTED_BLUE = 10.392  # Uluslararası: 2m kenar altıgen
                error = abs(area_m2 - EXPECTED_BLUE)
                accuracy = (1 - min(error / EXPECTED_BLUE, 1.0)) * 100
                self.get_logger().info(
                    f'🔵 MAVI (Altıgen 2m) → Merkez: {center}, '
                    f'Alan: {area_m2:.3f} m² ({area_px:.0f} px²) '
                    f'| Beklenen: {EXPECTED_BLUE:.3f} m² | Hata: ±{error:.3f} m² | Doğruluk: %{accuracy:.1f}'
                )
            else:
                self.get_logger().warn('🔵 MAVI hedef tespit edilemedi')
            
            self.get_logger().info('═' * 80)
    
    def find_target_with_area(self, mask, image, color, name):
        """Hedef merkezi VE alanını hesapla"""
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) == 0:
            return None
        
        # En büyük konturu al
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Alan hesapla (piksel)
        area_pixels = cv2.contourArea(largest_contour)
        
        # Minimum alan kontrolü (küçültüldü)
        if area_pixels < 100:
            return None
        
        # Gerçek alan hesapla (m²)
        area_m2 = area_pixels * (self.meters_per_pixel ** 2)
        
        # Merkez hesapla
        M = cv2.moments(largest_contour)
        if M["m00"] == 0:
            return None
        
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        
        # Görselleştir
        cv2.drawContours(image, [largest_contour], -1, color, 3)
        cv2.circle(image, (cx, cy), 10, color, -1)
        
        # Alan bilgisini ekrana yaz
        text1 = f"{name}"
        text2 = f"{area_m2:.2f} m2"
        cv2.putText(image, text1, (cx-60, cy-30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(image, text2, (cx-60, cy-5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        return ((cx, cy), area_pixels, area_m2)

def main(args=None):
    rclpy.init(args=args)
    node = ColorDetector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
