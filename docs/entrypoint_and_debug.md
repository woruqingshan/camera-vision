# main.py 入口与调试模式

本工程面向 MaixCAM2 的实际运行方式是：**上传整个文件夹，然后只运行根目录 `main.py`**。

不要依赖从 IDE 中分别运行 `tools/*.py`。这些工具文件仍然保留，但推荐通过 `configs/app_config.py` 中的 `RUN_MODE` 选择调试功能。

## 1. 入口文件

固定入口：

```bash
cd /root/camera_vision_firmware_maixcam2
python main.py
```

`main.py` 内部会读取：

```python
# configs/app_config.py
RUN_MODE = "vision"
```

然后自动分发到不同功能。

## 2. RUN_MODE 可选值

| RUN_MODE | 功能 | 什么时候使用 |
|---|---|---|
| `test_display` | 测试屏幕显示 | 第一次上板，确认 display 可用 |
| `test_camera` | 测试相机采图 | 确认摄像头能打开、画面方向正确 |
| `test_uart` | 测试 UART 输出 | 用电脑串口助手确认 `@T` 消息可收到 |
| `test_protocol` | 测试协议格式 | 不需要硬件，检查 `@T` 文本帧格式 |
| `test_detector` | 测试靶纸检测 | 看屏幕 overlay，调黑框检测参数 |
| `calibrate_setpoint` | 辅助激光 setpoint 标定 | 激光装好后记录靶心像素坐标 |
| `vision` | 正式视觉输出主循环 | 与 TI Bridge 联调/比赛运行 |

## 3. 修改方式

只改这一行：

```python
# configs/app_config.py
RUN_MODE = "test_camera"
```

保存后重新运行：

```bash
python main.py
```

## 4. 推荐调试顺序

1. `test_display`
2. `test_camera`
3. `test_protocol`
4. `test_uart`
5. `test_detector`
6. `vision`
7. `calibrate_setpoint`，激光装好后再做
8. 回到 `vision`

## 5. 为什么这样设计

MaixCAM2 实际部署时通常是上传一个工程文件夹，然后从根目录运行主入口。为了避免多个脚本入口导致路径、导入、工作目录不一致，本工程使用单一 `main.py` 作为固定入口，通过 `RUN_MODE` 选择功能。
