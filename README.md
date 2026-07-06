# camera_vision_firmware_maixcam2

MaixCAM2 视觉固件，用于电赛小车的视觉云台系统。

本工程运行在 **MaixCAM2 1GB** 上，负责采集图像、识别靶纸黑色边框、计算目标相对 setpoint 的像素误差 `dx/dy`，并通过 UART 将视觉结果发送给独立 TI Bridge 板。

## 1. 系统定位

完整系统分为三份固件：

```text
MaixCAM2 视觉固件，本工程
  采图 → 识别靶纸 → 计算 dx/dy → UART 输出 @T

TI Bridge Keil 工程
  解析 @T → 滤波 / PD / 安全保护 → F32C 协议输出

底盘 TI 工程
  循迹 → 关键点判断 → 声光提示 → 激光开关
```

本工程 **不直接控制 F32C 电机**，也不控制底盘和激光。

## 2. 默认硬件假设

第一版采用保守默认值：

```text
相机模块：MaixCAM2 1GB
开发语言：MaixPy / Python
图像分辨率：320 x 240
setpoint：图像中心，即 160,120
UART：/dev/ttyS4, 115200 8N1
MaixCAM2 UART 默认引脚：A21 = UART4_TX, A22 = UART4_RX
通信方向：MaixCAM2 TX -> TI Bridge RX，GND 共地
```

MaixCAM2 的 UART 引脚、pinmap 和串口设备按照官方 UART 例程的 MaixCAM2 默认方案填写。若实际板卡或扩展接口不同，请修改：

```text
configs/serial_config.py
```

## 3. 输出协议

默认输出 V2 协议：

```text
@T,seq,found,dx,dy,confidence\n
```

示例：

```text
@T,135,1,12,-8,92
@T,136,0,0,0,0
```

字段含义：

```text
seq        帧序号，0~65535 循环
found      1 表示找到目标，0 表示目标丢失
dx         target_x - setpoint_x
dy         target_y - setpoint_y
confidence 0~100 置信度
```

如果你的 TI Bridge 还没有升级 parser，可以改成旧协议：

```python
# configs/serial_config.py
INCLUDE_SEQUENCE = False
```

旧协议格式为：

```text
@T,found,dx,dy,confidence\n
```

## 4. 上传方式

将整个 `camera_vision_firmware_maixcam2/` 文件夹上传到 MaixCAM2，例如上传到：

```text
/root/camera_vision_firmware_maixcam2/
```

然后在 MaixVision 或板端终端中运行：

```bash
cd /root/camera_vision_firmware_maixcam2
python main.py
```


## 4.5 固定入口：只运行 main.py

本工程已经改成单一入口模式。把整个文件夹上传到 MaixCAM2 后，始终运行根目录：

```bash
cd /root/camera_vision_firmware_maixcam2
python main.py
```

所有调试功能都通过修改 `configs/app_config.py` 中的 `RUN_MODE` 来切换：

```python
RUN_MODE = "vision"
```

可选值：

```text
test_display       测试屏幕
test_camera        测试相机
test_uart          测试 UART 输出
test_protocol      测试 @T 协议格式
test_detector      测试靶纸检测
calibrate_setpoint 激光 setpoint 标定辅助
vision             正式视觉输出主循环
```

详细说明见：

```text
docs/entrypoint_and_debug.md
```

## 5. 分阶段测试方法

不要一上来接 TI Bridge 和 F32C。按下面顺序测试。

### 5.1 测试屏幕显示

```bash
python tools/test_display.py
```

预期：屏幕显示黑底文字和中心十字。

### 5.2 测试相机画面

```bash
python tools/test_camera.py
```

预期：屏幕显示实时相机画面。

如果画面左右/上下颠倒，修改：

```python
# configs/camera_config.py
FLIP_X = True / False
FLIP_Y = True / False
ROTATE_DEG = 0 / 90 / 180 / 270
```

不同 MaixPy 固件对图像旋转/镜像 API 支持可能不同；如果配置不生效，优先在相机安装方向或后续平台适配层中调整。

### 5.3 测试 UART 输出

先将 MaixCAM2 的 TX 接到 USB-TTL 的 RX，GND 共地，在电脑串口助手中打开 115200。

```bash
python tools/test_uart.py
```

预期电脑端看到：

```text
@T,1,1,29,-10,90
@T,2,1,28,-10,90
...
@T,40,0,0,0,0
```

如果收不到数据，检查：

```text
1. TX/RX 是否接反
2. GND 是否共地
3. UART 引脚是否为 A21/A22
4. configs/serial_config.py 中 UART_DEVICE 是否正确
5. pinmap 是否设置成功
```

### 5.4 测试协议格式

```bash
python tools/test_protocol_output.py
```

预期输出 V2 和 legacy 两种协议样例，并能自解析。

### 5.5 测试靶纸检测

```bash
python tools/test_detector.py
```

将靶纸放入画面。预期屏幕出现：

```text
绿色框：黑色边框候选区域
红色十字：检测到的靶心/中心
蓝色十字：setpoint
黄色文字：dx/dy/confidence/fps
```

如果误检或检测不到，优先调：

```text
configs/detector_config.py
BLACK_LAB_THRESHOLD
MIN_AREA_RATIO
MAX_AREA_RATIO
MIN_ASPECT
MAX_ASPECT
```

### 5.6 运行主程序

```bash
python main.py
```

主程序会持续：

```text
采图 → 检测 → 显示 overlay → UART 输出 @T
```

## 6. 与 TI Bridge 联调

第一步不要接 F32C，只接 MaixCAM2 到 TI Bridge：

```text
MaixCAM2 A21 / UART4_TX  →  TI Bridge UART_RX
MaixCAM2 GND             →  TI Bridge GND
```

TI Bridge 串口 parser 应支持：

```text
@T,seq,found,dx,dy,confidence
```

如果 TI Bridge 仍使用旧 parser，则先将：

```python
INCLUDE_SEQUENCE = False
```

之后再升级 TI Bridge 的 `camera_msg_parser.c`。

## 7. 激光 setpoint 标定

第一版默认使用图像中心作为 setpoint。真实激光与相机不一定同轴，后续必须标定。

标定辅助：

```bash
python tools/calibrate_setpoint.py
```

流程：

```text
1. 固定小车和靶纸。
2. 手动调整云台，使激光打中靶心。
3. 观察终端输出的 CALIB_CANDIDATE cx/cy。
4. 将稳定的 cx/cy 写入 configs/calibration_config.py。
5. 设置 USE_IMAGE_CENTER = False。
```

## 8. 当前算法边界

第一版 MVP 使用：

```text
黑色边框阈值检测
blob / bbox 中心估计
图像中心 setpoint
UART ASCII 输出
```

暂不包含：

```text
Homography 靶心反投影
红色同心圆辅助验证
YOLO / NPU 检测
复杂曝光控制
双向通信
```

后续优化请参考 `docs/development_plan.md`。
