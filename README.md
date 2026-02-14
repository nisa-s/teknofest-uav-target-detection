# TEKNOFEST UAV Competition - Autonomous Target Detection System
  
  [![ROS2](https://img.shields.io/badge/ROS2-Jazzy-blue)](https://docs.ros.org/)
  [![Python](https://img.shields.io/badge/Python-3.12-green)](https://www.python.org/)
  [![OpenCV](https://img.shields.io/badge/OpenCV-4.x-red)](https://opencv.org/)
  [![Gazebo](https://img.shields.io/badge/Gazebo-Harmonic-orange)](https://gazebosim.org/)
  [![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
</div>

## 🎯 Project Overview

Real-time computer vision system developed for **TEKNOFEST UAV Competition** (Rotary Wing Category). The system detects colored targets (red and blue) using HSV color space analysis and calculates precise centroid coordinates for autonomous payload delivery.

**Competition Task:** Autonomous detection of colored targets and precision payload drop.

### 🎥 Demo Video

[Watch Demo Video](videos/demo.mp4)

---

## 🚁 Features

- ✅ **Real-time Target Detection**: HSV-based color segmentation for red/blue targets
- ✅ **Contour Analysis**: Precise centroid calculation using image moments
- ✅ **ROS 2 Integration**: Distributed communication with topic-based architecture
- ✅ **Gazebo Simulation**: Full 3D environment with gimbal-controlled camera
- ✅ **ArduPilot SITL**: Autonomous flight testing and validation
- ✅ **Visualization**: Live target tracking with OpenCV windows

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| **OS** | Ubuntu 24.04 LTS |
| **Robotics Framework** | ROS 2 Jazzy Jalisco |
| **Simulator** | Gazebo Harmonic |
| **Autopilot** | ArduPilot SITL |
| **Computer Vision** | OpenCV 4.x |
| **Language** | Python 3.12 |
| **Build System** | Colcon |

---

## 📋 System Requirements

- **OS**: Ubuntu 24.04 LTS
- **RAM**: 8 GB minimum (16 GB recommended)
- **Storage**: 20 GB free space
- **GPU**: Optional (for better Gazebo performance)

---

## 🚀 Installation

### 1. Install ROS 2 Jazzy

```bash
# Add ROS 2 repository
sudo apt update && sudo apt install -y software-properties-common
sudo add-apt-repository universe
sudo apt update && sudo apt install curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

# Install ROS 2 Jazzy
sudo apt update
sudo apt install ros-jazzy-desktop -y
```

### 2. Install Dependencies

```bash
# Gazebo Harmonic and ROS-Gazebo bridge
sudo apt install ros-jazzy-ros-gz -y

# Computer vision packages
sudo apt install ros-jazzy-cv-bridge ros-jazzy-image-transport -y

# Python dependencies
pip install opencv-python numpy --break-system-packages
```

### 3. Install ArduPilot SITL

```bash
cd ~
git clone --recurse-submodules https://github.com/ArduPilot/ardupilot.git
cd ardupilot
Tools/environment_install/install-prereqs-ubuntu.sh -y
source ~/.profile
```

### 4. Install ArduPilot-Gazebo Plugin

```bash
cd ~
git clone https://github.com/ArduPilot/ardupilot_gazebo.git
cd ardupilot_gazebo

# Build with clean PATH (avoid MinGW conflicts on WSL)
mkdir build && cd build
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
source /opt/ros/jazzy/setup.bash
cmake .. -DCMAKE_BUILD_TYPE=RelWithDebInfo
make -j4
sudo make install
```

### 5. Clone This Repository

```bash
cd ~
git clone https://github.com/YOUR_USERNAME/teknofest-uav-target-detection.git
cd teknofest-uav-target-detection

# Build ROS 2 workspace
colcon build --packages-select target_detection
source install/setup.bash
```

### 6. Configure Environment

Add to `~/.bashrc`:

```bash
# ArduPilot
export PATH=$PATH:$HOME/ardupilot/Tools/autotest

# Gazebo
export GZ_SIM_SYSTEM_PLUGIN_PATH=$HOME/ardupilot_gazebo/build:$GZ_SIM_SYSTEM_PLUGIN_PATH
export GZ_SIM_RESOURCE_PATH=$HOME/ardupilot_gazebo/models:$HOME/ardupilot_gazebo/worlds:$GZ_SIM_RESOURCE_PATH

# ROS 2
source /opt/ros/jazzy/setup.bash
source ~/teknofest-uav-target-detection/install/setup.bash
```

```bash
source ~/.bashrc
```

---

## 🎮 Usage

### Quick Start (3 Terminals)

**Terminal 1 - Gazebo Simulation:**
```bash
gz sim -v4 -r ~/ardupilot_gazebo/worlds/iris_runway.sdf
```

**Terminal 2 - Camera Bridge:**
```bash
ros2 run ros_gz_bridge parameter_bridge \
  /world/iris_runway/model/iris_with_gimbal/model/gimbal/link/pitch_link/sensor/camera/image@sensor_msgs/msg/Image@gz.msgs.Image \
  --ros-args -r /world/iris_runway/model/iris_with_gimbal/model/gimbal/link/pitch_link/sensor/camera/image:=/camera/image
```

**Terminal 3 - Target Detection:**
```bash
ros2 run target_detection color_detector
```

### With ArduPilot SITL (Optional)

**Terminal 4 - ArduPilot:**
```bash
cd ~/ardupilot
sim_vehicle.py -v ArduCopter -f gazebo-iris --console --map
```

---

## 📊 Technical Details

### HSV Color Thresholds

**Red Target:**
```python
lower_red1 = [0, 40, 40]
upper_red1 = [20, 255, 255]
lower_red2 = [160, 40, 40]
upper_red2 = [180, 255, 255]
```

**Blue Target:**
```python
lower_blue = [105, 80, 80]
upper_blue = [125, 255, 255]
```

### Algorithm Pipeline

1. **Image Acquisition**: Subscribe to `/camera/image` topic
2. **Color Space Conversion**: BGR → HSV
3. **Color Segmentation**: Apply HSV thresholds
4. **Morphological Operations**: Noise filtering
5. **Contour Detection**: Find target boundaries
6. **Centroid Calculation**: Compute center using image moments
7. **Visualization**: Draw contours and markers

### Performance

- **Detection Rate**: 30+ FPS
- **Accuracy**: ±5 pixel precision
- **Latency**: <50ms end-to-end

---

## 🐛 Troubleshooting

### Issue: MinGW PATH Conflict (WSL)

**Error:**
```
error: Only Win32 target is supported!
```

**Solution:**
```bash
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
```

## 📚 Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [Usage Guide](docs/USAGE.md)
- [Full Technical Report](docs/report.pdf)

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Author

**Nisanur ŞEN**  
Software Engineering Student | KOU Storm UAV Team Member

📧 nisssn.03@gmail.com  
🔗 [www.linkedin.com/nisanur-şen](https://www.linkedin.com/in/nisanur-%C5%9Fen/)  

---

<div align="center">
  <b>⭐ If you find this project useful, please consider giving it a star! ⭐</b>
</div>
