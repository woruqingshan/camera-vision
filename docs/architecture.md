# Architecture

```text
MaixCAM2
  CameraSource
  BlackBorderDetector
  CenterEstimator
  DebugOverlay
  TiBridgeProtocol
  UartSender
      ↓ @T,seq,found,dx,dy,confidence
TI Bridge
  CameraMsgParser
  TargetFilter
  GimbalTracker
  SafetyGuard
  F32CProtocol
      ↓ F32C binary UART
F32C Gimbal
```

Core rule: MaixCAM2 only produces target observations. It does not send F32C frames and does not implement motor safety.
