# Vision Frontend Simulator 구현 계획

## 1. 프로젝트 목적

이 프로젝트는 카메라와 GPU 사이에 위치할 Vision Frontend Gate 또는 NPX Gate의 효과를 소프트웨어로 먼저 검증하기 위한 시뮬레이션 프로젝트이다.

최종 목표는 실제 하드웨어, 보드, 칩 구현 전에 다음 질문에 답하는 것이다.

> 전체 프레임을 매번 GPU에 넣는 방식보다, 전처리 게이트가 필요한 ROI만 선별해 GPU에 전달하는 방식이 객체 탐지 성능을 유지하면서 GPU 사용량을 줄일 수 있는가?

초기 단계에서는 실제 NPX 하드웨어나 SNN 모델을 구현하지 않고, rule-based 영상처리로 ROI Gate를 에뮬레이션한다.

## 2. 현재 구현 우선순위

현재 우선순위는 `Phase 1. Rule-based ROI Gate 검증`이다.

Phase 1에서는 다음을 구현한다.

- Dataset video 또는 image sequence loader
- Full-frame YOLOv8 baseline
- Rule-based ROI Gate emulator
- ROI crop 생성
- ROI crop 기반 YOLOv8 inference
- detection 좌표 복원
- workload, recall, ROI 품질 비교 리포트
- ROI 및 detection 시각화

Phase 2 이후의 SNN, 멀티카메라, GPU 최적화, 하드웨어 스펙 도출은 Phase 1 결과를 기준으로 진행한다.

## 3. 구현 체크리스트

체크박스는 실제 구현과 최소 동작 확인이 끝났을 때 갱신한다. 단순 파일 생성만으로 완료 처리하지 않고, 해당 단계의 산출물이 생성되거나 다음 단계에서 사용할 수 있는 인터페이스가 준비되었을 때 완료로 본다.

### Phase 1. Rule-based ROI Gate 검증

- [x] Task 1. 프로젝트 스캐폴딩
  - [x] 기본 디렉터리 생성
  - [x] config 파일 기본값 작성
  - [x] 공통 schema 정의
  - [x] 실행 스크립트 입출력 경로 통일
- [ ] Task 2. Dataset Stream Loader
  - [ ] video loader 구현
  - [ ] image sequence loader 구현
  - [ ] `FramePacket` 생성
  - [ ] annotation loader 확장 지점 준비
- [ ] Task 3. Rule-based ROI Gate Emulator
  - [ ] gray 변환 및 resize
  - [ ] frame difference
  - [ ] ON/OFF event-like map 생성
  - [ ] threshold 기반 motion map
  - [ ] morphology 및 small component filtering
  - [ ] connected component 기반 ROI 후보 생성
  - [ ] ROI merge
  - [ ] ROI margin 및 원본 좌표 변환
  - [ ] temporal hold
  - [ ] periodic full-frame trigger
  - [ ] ROI 과다/대면적 full-frame fallback
- [ ] Task 4. ROI Metadata 저장
  - [ ] ROI metadata schema 확정
  - [ ] JSONL writer 구현
  - [ ] frame별 trigger type 기록
  - [ ] crop inference/evaluation에서 재사용 가능한 형식 확인
- [ ] Task 5. Full-frame YOLO Baseline
  - [ ] YOLOv8n full-frame inference 구현
  - [ ] detection JSONL 저장
  - [ ] latency 측정
  - [ ] workload metric 기록
- [ ] Task 6. ROI YOLO Inference
  - [ ] ROI crop 생성
  - [ ] crop YOLO inference 구현
  - [ ] crop detection 좌표 원본 좌표로 복원
  - [ ] periodic full-frame check 결과 병합
- [ ] Task 7. Evaluation
  - [ ] recall 유지율 계산
  - [ ] ROI containment rate 계산
  - [ ] YOLO 호출 수 감소율 계산
  - [ ] YOLO 입력 픽셀 면적 감소율 계산
  - [ ] 평균 ROI 수와 평균 ROI 면적 계산
  - [ ] gate latency 계산
  - [ ] comparison report 생성
- [ ] Task 8. Visualization
  - [ ] ROI overlay 이미지 생성
  - [ ] full-frame detection과 ROI-gated detection 비교 시각화
  - [ ] 실패 사례 저장

### Phase 2 이후

- [ ] Phase 2. SNN Tile Eventness Model 검증
- [ ] Phase 3. Multi-camera Simulation
- [ ] Phase 4. GPU Pipeline Optimization
- [ ] Phase 5. Hardware-oriented Spec 도출
- [ ] Phase 6. 실제 Edge Pipeline PoC
- [ ] Phase 7. 사업화 기준 검증

## 4. Phase 1 검증 질문

핵심 질문은 다음과 같다.

> Full-frame YOLOv8 대비, motion 기반 ROI crop만 YOLOv8에 입력했을 때 객체 탐지 recall을 유지하면서 GPU inference workload를 줄일 수 있는가?

Phase 1에서는 세 가지 비교군을 둔다.

```text
A. Full-frame YOLOv8
B. Rule-based ROI Gate + ROI YOLOv8
C. Rule-based ROI Gate + ROI YOLOv8 + Periodic Full-frame Check
```

## 5. 구현 순서

### [x] Task 1. 프로젝트 스캐폴딩

목표:

- 디렉터리 구조 생성
- config 기본값 작성
- 공통 데이터 구조 정의
- 실행 스크립트의 입출력 경로 통일

예상 산출물:

```text
configs/
data_loader/
npx_emulator/
gpu_inference/
evaluation/
experiments/
outputs/
```

### [ ] Task 2. Dataset Stream Loader

목표:

- OpenCV 기반 video loader 구현
- image sequence loader 구현
- `frame_id`, `timestamp`, `camera_id`, `frame`을 포함한 frame packet 생성
- 추후 annotation loader를 붙일 수 있는 구조 유지

초기에는 OD-VIRAT Tiny 또는 VIRAT 일부 시퀀스를 대상으로 한다.

### [ ] Task 3. Rule-based ROI Gate Emulator

목표:

- gray 변환
- low-resolution analysis frame 생성
- frame difference
- ON/OFF event-like map 생성 코드 분리
- threshold 기반 motion map 생성
- morphology 기반 noise filtering
- connected component 기반 ROI 후보 생성
- ROI merge
- ROI margin 추가
- 원본 좌표계 변환
- temporal hold
- periodic full-frame trigger

중요한 설계 원칙:

- Phase 1에서는 `motion_map`만 사용해도 되지만, Phase 2 SNN 확장을 위해 `on_event`, `off_event`, `motion_map` 생성 코드는 분리한다.
- ROI가 너무 많거나 전체 면적이 너무 크면 full-frame fallback이 가능해야 한다.

### [ ] Task 4. ROI Metadata 저장

목표:

- frame별 ROI 결과를 JSONL로 저장
- crop inference와 평가 코드가 동일한 metadata를 사용하도록 한다.

예상 출력:

```text
outputs/roi_metadata/rule_roi.jsonl
```

권장 metadata 필드:

```json
{
  "camera_id": "cam_01",
  "frame_id": 1024,
  "timestamp": 1780000000.123,
  "roi_id": "cam_01_f1024_roi_01",
  "original_frame_size": [1920, 1080],
  "analysis_frame_size": [256, 144],
  "roi_xywh": [640, 320, 420, 560],
  "score": 0.82,
  "source": "rule_based_roi_gate",
  "trigger_type": "roi"
}
```

### [ ] Task 5. Full-frame YOLO Baseline

목표:

- YOLOv8n으로 전체 프레임 inference 수행
- frame별 detection 결과 저장
- inference latency 측정
- YOLO 호출 수와 입력 픽셀 면적 기록

예상 출력:

```text
outputs/detections/full_frame.jsonl
outputs/reports/full_frame_metrics.json
```

초기에는 full-frame YOLO 결과를 pseudo baseline으로 사용한다. Dataset annotation이 준비되면 GT 기반 metric을 추가한다.

### [ ] Task 6. ROI YOLO Inference

목표:

- ROI metadata 기준으로 원본 frame에서 crop 생성
- ROI crop을 YOLOv8에 입력
- crop 좌표계 detection을 원본 좌표계로 복원
- periodic full-frame check 결과와 병합 가능하게 설계

예상 출력:

```text
outputs/detections/roi_yolo.jsonl
outputs/reports/roi_yolo_metrics.json
```

### [ ] Task 7. Evaluation

목표:

- Full-frame baseline과 ROI-gated 결과 비교
- recall 유지율 계산
- ROI containment rate 계산
- YOLO 호출 수 감소율 계산
- YOLO 입력 픽셀 면적 감소율 계산
- 평균 ROI 개수와 평균 ROI 면적 계산
- Gate latency 측정

예상 출력:

```text
outputs/reports/comparison_report.json
outputs/reports/comparison_report.md
```

### [ ] Task 8. Visualization

목표:

- 원본 frame 위에 ROI box 표시
- full-frame detection과 ROI-gated detection 비교
- 실패 사례를 이미지 또는 영상으로 저장

예상 출력:

```text
outputs/visualizations/
```

## 6. 권장 프로젝트 구조

```text
vision-frontend-simulator/
├── README.md
├── docs/
│   ├── plan.md
│   ├── npx_gate_phase1_validation_plan.md
│   └── vision_frontend_validation_roadmap.md
├── .agents/
│   └── project_context.md
├── configs/
│   ├── dataset.yaml
│   ├── npx_gate.yaml
│   └── yolo.yaml
├── common/
│   └── schemas.py
├── data_loader/
│   ├── dataset_stream.py
│   └── annotation_loader.py
├── npx_emulator/
│   ├── preprocess.py
│   ├── event_encoder.py
│   ├── motion_detector.py
│   ├── roi_generator.py
│   ├── temporal_hold.py
│   └── metadata.py
├── gpu_inference/
│   ├── yolo_full_frame.py
│   ├── yolo_roi.py
│   └── coordinate_restore.py
├── evaluation/
│   ├── detection_metrics.py
│   ├── roi_containment.py
│   ├── workload_metrics.py
│   └── latency_metrics.py
├── experiments/
│   ├── run_full_frame_baseline.py
│   ├── run_rule_roi_baseline.py
│   └── compare_results.py
└── outputs/
    ├── detections/
    ├── roi_metadata/
    ├── visualizations/
    └── reports/
```

## 7. 초기 Config 기준

### Dataset

```yaml
dataset:
  type: video
  input_path: data/sample.mp4
  camera_id: cam_01
  fps_override: null
  frame_limit: null
```

### NPX Gate

```yaml
npx_gate:
  analysis_width: 256
  analysis_height: 144
  threshold_motion: 25
  threshold_on: 15
  threshold_off: 15
  morphology_kernel_size: 3
  min_area_ratio: 0.001
  merge_distance_ratio: 0.08
  margin_ratio: 0.25
  hold_frames: 15
  full_frame_interval: 60
  max_roi_per_frame: 5
  max_total_roi_area_ratio: 0.5
```

### YOLO

```yaml
yolo:
  model: yolov8n.pt
  image_size: 640
  confidence_threshold: 0.25
  iou_threshold: 0.45
  classes:
    - person
    - car
    - truck
    - bus
```

## 8. Phase 1 성공 기준

최소 성공 기준:

```text
Object Recall 유지율 >= 95%
ROI Containment Rate >= 98%
YOLO 입력 면적 감소율 >= 50%
평균 ROI 수 <= 3
평균 ROI 면적 <= 전체 프레임의 30%
Gate latency <= 10ms/frame
```

다음 단계 진입 기준:

```text
Object Recall 유지율 >= 98%
YOLO workload reduction >= 50%
Rule-based ROI Gate의 한계 사례가 명확히 수집됨
```

## 9. 협업 규칙 초안

- 구현은 Phase 단위로 진행한다.
- Phase 1에서는 하드웨어, SNN, RTSP, DeepStream, TensorRT를 직접 구현하지 않는다.
- 실험 결과는 `outputs/` 아래에 저장하되, 대용량 결과물은 Git에 포함하지 않는다.
- config 값이 실험 결과에 영향을 주므로 report에는 사용한 config snapshot을 함께 남긴다.
- metric 계산 방식이 바뀌면 기존 report와 비교 가능하도록 변경 내용을 문서화한다.
- ROI metadata schema는 GPU inference, evaluation, visualization이 공유하는 계약으로 취급한다.

## 10. 문서 역할

- `README.md`: 프로젝트 소개, 빠른 시작, 협업자가 봐야 할 요약
- `docs/plan.md`: 구현 순서와 현재 작업 기준
- `docs/npx_gate_phase1_validation_plan.md`: Phase 1 세부 검증 계획
- `docs/vision_frontend_validation_roadmap.md`: 전체 장기 로드맵
- `.agents/project_context.md`: Codex 또는 자동화 agent가 먼저 확인할 문서 목록과 작업 원칙

## 11. 다음 작업

바로 다음 구현 작업은 Task 2이다.

```text
1. video loader 최소 동작 검증
2. image sequence loader 최소 동작 검증
3. dataset config 기반 stream factory 구현
4. FramePacket 생성 결과 검증
5. annotation loader 확장 지점 정리
```
