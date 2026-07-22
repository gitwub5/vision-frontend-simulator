# NPX Gate 1차 검증 계획

## 0. 목적

본 문서는 NPX 기반 비전 게이트 구조의 1차 검증을 위한 구현 계획이다.

1차 검증의 목적은 실제 NPX 하드웨어나 SNN 학습 모델을 완성하는 것이 아니라, **NPX가 담당할 전처리·ROI Gate 기능을 소프트웨어로 시뮬레이션했을 때 GPU 추론량을 줄일 수 있는지** 확인하는 것이다.

핵심 검증 질문은 다음과 같다.

> 전체 프레임을 매번 YOLOv8로 처리하는 방식 대비, NPX Gate가 생성한 ROI crop만 YOLOv8에 넣었을 때 객체 탐지 성능을 유지하면서 GPU 추론량을 줄일 수 있는가?

---

## 1. 검증 컨셉

### 1.1 Baseline 구조

```text
Dataset Video / Image Sequence
        ↓
Full-frame YOLOv8
        ↓
Detection Result
```

모든 프레임을 YOLOv8에 입력한다.

측정 항목:

- 전체 프레임 YOLO 호출 수
- 전체 처리 시간
- 객체 탐지 recall
- mAP 또는 detection metric
- GPU 사용량 또는 추론 시간

---

### 1.2 NPX Gate 구조

```text
Dataset Video / Image Sequence
        ↓
Camera Stream Simulator
        ↓
NPX Gate Emulator
- gray 변환
- resize
- frame difference
- threshold
- noise filtering
- ROI 후보 생성
- ROI merge
- temporal hold
- periodic full-frame check
        ↓
ROI Crop Generator
        ↓
YOLOv8 Inference
        ↓
Detection Result
```

NPX Gate Emulator가 전체 프레임에서 움직임 기반 ROI를 생성하고, YOLOv8은 해당 ROI crop만 추론한다.

---

## 2. 1차 검증에서 NPX가 수행해야 하는 기능

1차 검증에서 NPX는 실제 SNN 모델을 사용하지 않는다.  
대신 rule-based video processing으로 NPX의 ROI Gate 역할을 흉내 낸다.

### 2.1 Frame Input Receiver

역할:

- dataset frame을 카메라 입력처럼 순차적으로 수신
- frame_id, timestamp, camera_id 관리

입력:

```text
frame
frame_id
timestamp
camera_id
```

초기 구현 방식:

```text
OpenCV VideoCapture 또는 image sequence loader
```

---

### 2.2 Low-resolution Analysis Frame 생성

역할:

- 원본 프레임을 NPX 분석용 저해상도 프레임으로 변환

처리:

```text
original frame
→ gray conversion
→ resize
→ analysis frame
```

권장 설정:

```text
analysis_size = 256x144
fallback_size = 128x128
color = gray 8-bit
```

원본 프레임은 ROI crop 생성을 위해 별도로 유지한다.

---

### 2.3 Frame Difference

역할:

- 현재 프레임과 이전 프레임의 차이로 움직임 후보를 찾음

처리:

```text
diff = abs(gray_t - gray_t-1)
```

출력:

```text
diff_map
```

---

### 2.4 Event-like Map 생성

역할:

- 향후 SNN 입력으로 확장할 수 있도록 ON/OFF event-like map 생성

처리:

```text
delta = gray_t - gray_t-1

ON  = delta > threshold_on
OFF = delta < -threshold_off
motion = abs(delta) > threshold_motion
```

1차 검증에서는 motion_map만 사용해도 된다.  
다만 2차 SNN 확장을 고려해 ON/OFF map 생성 코드는 분리해둔다.

---

### 2.5 Noise Filtering

역할:

- 압축 노이즈, 작은 픽셀 변화, 센서 노이즈 제거

처리 후보:

- threshold
- morphology open / close
- small connected component removal
- minimum area filter

권장 파라미터:

```text
min_area_ratio = 0.001 ~ 0.005
kernel_size = 3 or 5
```

---

### 2.6 Motion ROI 후보 생성

역할:

- motion_map에서 활성 영역을 찾아 ROI 후보 생성

처리:

```text
motion_map
→ connected component labeling
→ component bounding box
→ ROI candidate
```

ROI candidate 예시:

```json
{
  "x": 40,
  "y": 20,
  "w": 30,
  "h": 50,
  "score": 0.82,
  "coord_system": "analysis_frame"
}
```

---

### 2.7 ROI Merge

역할:

- 가까운 ROI 후보들을 병합하여 GPU 호출 수를 줄임

필요 이유:

- ROI가 너무 많으면 full-frame YOLO 1회보다 ROI YOLO 여러 번이 더 비싸질 수 있음

권장 기준:

```text
max_roi_per_frame = 5
target_avg_roi_per_frame = 1 ~ 3
merge_distance_ratio = 0.05 ~ 0.1
```

---

### 2.8 Temporal Hold

역할:

- 한 번 발생한 ROI를 일정 시간 유지

필요 이유:

- 사람이 잠깐 멈추면 frame difference에서는 ROI가 사라질 수 있음
- GPU 추론과 tracking이 끊기지 않게 해야 함

권장 설정:

```text
hold_frames = 10 ~ 30
hold_time = 0.5 ~ 1.0 sec
```

---

### 2.9 Periodic Full-frame Check

역할:

- ROI 기반 처리만으로 놓칠 수 있는 정지 객체를 보완

처리:

```text
every N frames:
    send full frame to YOLOv8
otherwise:
    send ROI crops only
```

권장 설정:

```text
full_frame_interval = 30 ~ 90 frames
```

---

### 2.10 원본 좌표 변환

역할:

- analysis frame 기준 ROI를 원본 프레임 좌표로 변환

처리:

```text
scale_x = original_width / analysis_width
scale_y = original_height / analysis_height

x_original = x_analysis * scale_x
y_original = y_analysis * scale_y
w_original = w_analysis * scale_x
h_original = h_analysis * scale_y
```

---

### 2.11 ROI Margin 추가

역할:

- 저해상도 ROI 오차 보정
- 객체 일부 잘림 방지
- YOLO가 주변 context를 볼 수 있게 함

권장 설정:

```text
margin_ratio = 0.2 ~ 0.3
```

처리:

```text
expanded_roi = add_margin(original_roi, margin_ratio)
expanded_roi = clip_to_frame_boundary(expanded_roi)
```

---

### 2.12 ROI Metadata 생성

역할:

- GPU 추론 결과를 원본 프레임 기준으로 복원하기 위한 메타데이터 생성

예시:

```json
{
  "camera_id": "cam_01",
  "frame_id": 1024,
  "timestamp": 1780000000.123,
  "roi_id": "cam01_f1024_roi01",
  "original_frame_size": [1920, 1080],
  "roi_xywh": [640, 320, 420, 560],
  "event_type": "motion_candidate",
  "confidence": 0.82,
  "source": "rule_based_npx_gate"
}
```

---

### 2.13 ROI Crop 생성

역할:

- 원본 프레임에서 ROI crop 이미지를 생성하여 YOLOv8 입력으로 전달

처리:

```text
original frame
→ crop by roi_xywh
→ letterbox resize
→ YOLOv8 input
```

YOLOv8 결과 좌표는 crop 기준으로 나오므로, 이후 원본 좌표로 복원해야 한다.

---

### 2.14 GPU Trigger 판단

역할:

- 해당 프레임에서 GPU 추론을 수행할지 결정

GPU 호출 조건:

```text
1. 현재 프레임에 ROI가 있음
2. temporal hold 중인 ROI가 있음
3. periodic full-frame check 시점임
```

---

## 3. 1차에서 구현하지 않는 것

아래 항목은 1차 검증 범위에서 제외한다.

- SNN 모델 학습
- NPX 하드웨어 RTL 구현
- 실제 MIPI / GigE Vision / RTSP 입력
- 실제 DVS event stream 처리
- PCIe / 10GbE / DMA 연동
- DeepStream 통합
- GPU model routing
- Pose / Action Recognition
- Multi-camera production scheduler

---

## 4. 추천 데이터셋

### 4.1 1순위: OD-VIRAT Tiny 또는 VIRAT

사용 목적:

- 고정형 감시 카메라 환경 검증
- 사람/차량 중심 ROI 생성 검증
- full-frame YOLO 대비 ROI crop YOLO 효과 비교

추천 이유:

- 산업 안전·감시 카메라 시나리오와 유사
- 객체 bounding box 기반 평가 가능
- 너무 큰 데이터셋보다 초기 검증에 적절

---

### 4.2 대안: VIRAT 일부 시퀀스만 사용

OD-VIRAT Tiny 확보가 어렵다면 VIRAT 원본 영상 중 일부 시퀀스만 사용한다.

초기에는 전체 데이터셋을 모두 쓰지 않고, 다음 조건의 영상만 고른다.

- 고정 카메라
- 사람 또는 차량이 등장
- 배경 변화가 너무 극단적이지 않음
- annotation 확보 가능

---

## 5. GPU 모델

### 5.1 기본 모델

```text
YOLOv8n
```

사용 목적:

- 빠른 baseline
- ROI crop 추론 파이프라인 검증
- 실험 반복 속도 확보

---

### 5.2 비교 모델

```text
YOLOv8s
```

사용 목적:

- 정확도 기준 비교
- ROI crop으로 인한 성능 손실 확인

---

## 6. 평가 지표

### 6.1 Detection 성능

- Full-frame YOLO 대비 object recall 유지율
- mAP 또는 class별 AP
- 사람/차량 class recall
- False negative 증가량

권장 최소 기준:

```text
object recall >= full-frame baseline의 95 ~ 98%
```

---

### 6.2 ROI 품질

- ROI Containment Rate
- 평균 ROI 개수
- 평균 ROI 면적
- ROI가 실제 객체를 포함하지 않는 false ROI 비율
- 정지 객체 누락률

권장 기준:

```text
ROI Containment Rate >= 98%
average ROI count <= 3
average ROI area <= full frame의 30%
```

---

### 6.3 GPU 절감 효과

- YOLO 호출 수 감소율
- YOLO 입력 픽셀 면적 감소율
- 전체 추론 시간 감소율
- GPU utilization 감소율
- 처리 가능한 stream 수 증가 가능성

초기 최소 기준:

```text
YOLO input area reduction >= 50%
YOLO inference workload reduction >= 50%
```

사업화 후보 기준:

```text
YOLO inference workload reduction >= 70%
```

---

### 6.4 Latency

- NPX Gate Emulator 처리 시간
- ROI 생성 시간
- YOLO 추론 시간
- end-to-end 처리 시간

목표:

```text
NPX Gate processing latency <= 10ms per frame
```

---

## 7. 실험 비교군

### A. Full-frame YOLO

```text
all frames
→ full-frame YOLOv8
```

목적:

- 정확도 baseline
- GPU workload baseline

---

### B. Rule-based NPX Gate + ROI YOLO

```text
all frames
→ rule-based NPX Gate
→ ROI crop
→ YOLOv8
```

목적:

- NPX Gate 구조의 1차 가능성 확인

---

### C. Rule-based NPX Gate + ROI YOLO + Periodic Full-frame Check

```text
ROI crop YOLO
+
every N frames full-frame YOLO
```

목적:

- 정지 객체 누락 보완
- recall과 workload trade-off 확인

---

## 8. 권장 프로젝트 구조

```text
vision-frontend-simulator/
├── README.md
├── configs/
│   ├── dataset.yaml
│   ├── npx_gate.yaml
│   └── yolo.yaml
│
├── data_loader/
│   ├── dataset_stream.py
│   └── annotation_loader.py
│
├── npx_emulator/
│   ├── preprocess.py
│   ├── event_encoder.py
│   ├── motion_detector.py
│   ├── roi_generator.py
│   ├── temporal_hold.py
│   └── metadata.py
│
├── gpu_inference/
│   ├── yolo_full_frame.py
│   ├── yolo_roi.py
│   └── coordinate_restore.py
│
├── evaluation/
│   ├── detection_metrics.py
│   ├── roi_containment.py
│   ├── workload_metrics.py
│   └── latency_metrics.py
│
├── experiments/
│   ├── run_full_frame_baseline.py
│   ├── run_rule_roi_baseline.py
│   └── compare_results.py
│
└── outputs/
    ├── detections/
    ├── roi_metadata/
    ├── visualizations/
    └── reports/
```

---

## 9. Codex / Agent 작업 단위

### Task 1. 프로젝트 스캐폴딩 생성

목표:

- 위 프로젝트 구조 생성
- config 파일 기본값 작성
- README 초안 작성

---

### Task 2. Dataset Stream Loader 구현

목표:

- video 또는 image sequence를 frame 단위로 읽기
- frame_id, timestamp 생성
- annotation loader와 연결할 수 있게 설계

---

### Task 3. Full-frame YOLO Baseline 구현

목표:

- YOLOv8n으로 전체 프레임 추론
- detection 결과 저장
- 처리 시간 측정

출력:

```text
outputs/detections/full_frame.jsonl
outputs/reports/full_frame_metrics.json
```

---

### Task 4. Rule-based NPX Gate Emulator 구현

목표:

- gray 변환
- resize
- frame difference
- threshold
- morphology
- connected component
- ROI merge
- temporal hold
- periodic full-frame check

출력:

```text
outputs/roi_metadata/rule_roi.jsonl
```

---

### Task 5. ROI Crop YOLO 구현

목표:

- ROI metadata 기반 crop 생성
- YOLOv8 추론
- crop 좌표를 원본 좌표로 복원
- detection 결과 저장

출력:

```text
outputs/detections/roi_yolo.jsonl
```

---

### Task 6. 평가 코드 구현

목표:

- full-frame baseline과 ROI-gated 결과 비교
- recall 유지율 계산
- ROI containment 계산
- workload reduction 계산
- latency 계산

출력:

```text
outputs/reports/comparison_report.json
outputs/reports/comparison_report.md
```

---

### Task 7. 시각화 구현

목표:

- 원본 프레임 위에 ROI box와 YOLO 결과 표시
- full-frame 결과와 ROI-gated 결과 비교 이미지 또는 영상 생성

출력:

```text
outputs/visualizations/
```

---

## 10. 1차 성공 기준

### 최소 성공 기준

```text
Object Recall 유지율 >= 95%
ROI Containment Rate >= 98%
YOLO 입력 면적 감소율 >= 50%
평균 ROI 수 <= 3
평균 ROI 면적 <= 전체 프레임의 30%
```

---

### 다음 단계 진행 기준

다음 조건을 만족하면 SNN 기반 2차 검증으로 넘어간다.

```text
Object Recall 유지율 >= 98%
YOLO workload reduction >= 50%
Rule-based ROI의 한계 사례가 명확히 수집됨
```

한계 사례 예시:

- 조명 변화로 인한 false ROI
- 그림자 / 나뭇잎 / 비 / 압축 노이즈
- 정지 객체 누락
- 작은 객체 누락
- ROI 과다 생성

---

# 이후 검증 계획

## Phase 1. Rule-based NPX Gate 검증

목표:

- NPX Gate 구조 자체의 가능성 확인
- ROI crop 기반 YOLO가 full-frame YOLO 대비 workload를 줄일 수 있는지 검증

주요 구현:

- frame difference 기반 ROI
- temporal hold
- periodic full-frame check
- YOLOv8n/s baseline
- ROI containment / recall / workload 평가

결과물:

- 1차 비교 리포트
- 실패 사례 모음
- SNN으로 개선해야 할 요구사항 정의

---

## Phase 2. SNN Tile Eventness Model 검증

목표:

- rule-based ROI 생성기를 SNN 기반 ROI proposal 모델로 대체
- 단순 motion detection 대비 false wake-up 감소 여부 확인

SNN 입력:

```text
T x C x H x W
T = 4 ~ 8 timesteps
C = 2 channels: ON / OFF event map
H, W = 128x128 또는 256x144
```

SNN 출력:

```text
tile objectness heatmap
예: 16x9 또는 16x16
```

학습 라벨:

- dataset bounding box를 tile heatmap label로 변환
- GT box와 겹치는 tile은 positive
- 나머지는 negative

Loss:

```text
Focal Loss 또는 weighted BCE
```

비교군:

```text
rule-based ROI
vs
SNN ROI
```

주요 평가:

- ROI containment
- false wake-up 감소율
- recall 유지율
- ROI 면적 감소
- GPU workload reduction

---

## Phase 3. Multi-camera Simulation

목표:

- NPX Gate가 GPU당 처리 가능한 카메라 수를 늘릴 수 있는지 검증

구현:

- 여러 dataset video를 동시에 stream처럼 replay
- GPU-only multi-stream baseline 측정
- NPX-gated multi-stream 처리량 측정

평가:

- GPU 한 대 기준 처리 가능한 stream 수
- 평균 FPS
- latency
- GPU utilization
- detection recall 유지율

성공 기준:

```text
동일 GPU에서 처리 가능한 camera stream 수 1.5배 이상 증가
사업화 후보 기준: 2배 이상 증가
```

---

## Phase 4. GPU Pipeline Optimization

목표:

- ROI crop 여러 개를 GPU에 효율적으로 넣는 구조 검증

구현 후보:

- ROI batching
- ROI packing
- dynamic batch size
- crop resize 최적화
- TensorRT 적용
- DeepStream 연동 검토

평가:

- ROI 개수 증가 시 성능 저하 여부
- full-frame 1회 추론 대비 ROI N개 추론 비용
- batch / packing 적용 효과

---

## Phase 5. Hardware-oriented NPX Spec 도출

목표:

- 소프트웨어 검증 결과를 바탕으로 실제 NPX가 가져야 할 최소 사양 도출

정리할 항목:

- 입력 해상도
- FPS
- 지원 카메라 수
- NPX latency
- ROI metadata format
- event encoder 요구사항
- on-chip memory 요구량
- 외부 메모리 대역폭
- GPU 연결 방식
- 예상 전력
- 지원 인터페이스 후보

---

## Phase 6. 실제 Edge Pipeline PoC

목표:

- 실제 카메라 또는 RTSP stream을 사용한 end-to-end 검증

구성:

```text
RTSP / GigE Camera
→ NPX Gate Emulator or FPGA prototype
→ Jetson / GPU Server
→ YOLOv8 TensorRT
→ Result dashboard
```

평가:

- 실제 카메라 입력에서 ROI 품질
- 조명 변화 / 노이즈 / 압축 artifact 대응
- 실시간성
- GPU 사용량 절감
- 운영 안정성

---

## Phase 7. 사업화 기준 검증

목표:

- 고객 관점의 수치로 NPX Gate 가치 검증

핵심 KPI:

```text
Critical Event Recall >= 99%
ROI Containment Rate >= 99%
GPU inference workload reduction >= 70%
동일 GPU당 camera 수 2배 이상 증가
NPX Gate latency <= 10ms
False wake-up reduction vs rule baseline >= 70%
```

최종 판단:

- NPX Gate가 단순 motion detector보다 충분히 좋은가?
- 기존 edge NPU / GPU-only 구조보다 비용 이점이 있는가?
- 실제 산업 안전 / 감시 카메라 환경에서 적용 가능한가?
