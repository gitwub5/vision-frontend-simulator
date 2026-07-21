# Vision Frontend Simulator

Vision Frontend Simulator는 카메라와 GPU 사이에 위치하는 Vision Frontend Gate 또는 NPX Gate의 효과를 소프트웨어로 먼저 검증하기 위한 사내 시뮬레이션 프로젝트입니다.

이 프로젝트의 목적은 실제 하드웨어, 보드, 칩 구현 전에 ROI 기반 전처리 게이트가 GPU inference workload를 줄일 수 있는지 확인하는 것입니다.

## 핵심 검증 질문

> 전체 프레임을 매번 GPU에 넣는 방식 대비, Vision Frontend Gate가 필요한 ROI만 선별해 GPU에 전달하면 객체 탐지 성능을 유지하면서 GPU 사용량을 줄일 수 있는가?

초기 검증에서는 실제 NPX 하드웨어나 SNN 모델을 사용하지 않습니다. 대신 OpenCV 기반 rule-based 영상처리로 ROI Gate를 에뮬레이션하고, YOLOv8 inference workload 감소 효과를 측정합니다.

## 검증 로드맵

```text
Phase 1. Rule-based ROI Gate 검증
    ↓
Phase 2. SNN Tile Eventness Model 검증
    ↓
Phase 3. Multi-camera Simulation
    ↓
Phase 4. GPU Pipeline Optimization
    ↓
Phase 5. Hardware-oriented Spec 도출
    ↓
Phase 6. 실제 Edge Pipeline PoC
    ↓
Phase 7. 사업화 기준 검증
```

현재 우선 구현 범위는 **Phase 1. Rule-based ROI Gate 검증**입니다.

## Phase 1 범위

Phase 1에서는 다음 세 가지 방식을 비교합니다.

```text
A. Full-frame YOLOv8
B. Rule-based ROI Gate + ROI YOLOv8
C. Rule-based ROI Gate + ROI YOLOv8 + Periodic Full-frame Check
```

구현 항목:

- Dataset video 또는 image sequence loader
- Full-frame YOLOv8 baseline
- Gray 변환 및 low-resolution analysis frame 생성
- Frame difference 기반 motion map 생성
- ON/OFF event-like map 생성 구조
- Noise filtering
- Connected component 기반 ROI 생성
- ROI merge
- Temporal hold
- Periodic full-frame check
- ROI crop 생성
- ROI crop 기반 YOLOv8 inference
- Detection 좌표 원본 frame 기준 복원
- Workload, recall, ROI 품질 비교 리포트
- ROI 및 detection 시각화

## 성공 기준

Phase 1의 최소 성공 기준은 다음과 같습니다.

```text
Object Recall 유지율 >= 95%
ROI Containment Rate >= 98%
YOLO 입력 면적 감소율 >= 50%
평균 ROI 수 <= 3
평균 ROI 면적 <= 전체 프레임의 30%
Gate latency <= 10ms/frame
```

Phase 2로 넘어가기 위한 기준은 다음과 같습니다.

```text
Object Recall 유지율 >= 98%
YOLO workload reduction >= 50%
Rule-based ROI Gate의 한계 사례 수집 완료
```

## 권장 프로젝트 구조

```text
vision-frontend-simulator/
├── README.md
├── plan.md
├── requirements.txt
├── docs/
│   ├── npx_gate_phase1_validation_plan.md
│   ├── vision_frontend_validation_roadmap.md
│   └── tasks/
│       ├── task2_dataset_stream_loader.md
│       └── task3_rule_based_roi_gate.md
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
│   ├── gate.py
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
│   ├── inspect_dataset_stream.py
│   └── compare_results.py
├── tests/
│   ├── test_dataset_stream.py
│   └── test_npx_gate.py
└── outputs/
    ├── detections/
    ├── roi_metadata/
    ├── visualizations/
    └── reports/
```

## 주요 산출물

예상 산출물은 다음과 같습니다.

```text
outputs/detections/full_frame.jsonl
outputs/detections/roi_yolo.jsonl
outputs/roi_metadata/rule_roi.jsonl
outputs/reports/full_frame_metrics.json
outputs/reports/roi_yolo_metrics.json
outputs/reports/comparison_report.json
outputs/reports/comparison_report.md
outputs/visualizations/
```

## 초기 데이터셋

우선순위 데이터셋:

- OD-VIRAT Tiny
- VIRAT 일부 시퀀스

초기에는 전체 데이터셋보다 다음 조건을 만족하는 일부 시퀀스부터 사용합니다.

- 고정 카메라
- 사람 또는 차량 등장
- annotation 또는 full-frame YOLO pseudo baseline 확보 가능
- 조명 변화와 배경 변화가 지나치게 극단적이지 않음

## 문서 구성

- `README.md`: 프로젝트 소개와 협업자가 알아야 할 요약
- `plan.md`: 구현 순서와 현재 작업 계획
- `docs/npx_gate_phase1_validation_plan.md`: Phase 1 상세 검증 계획
- `docs/tasks/task2_dataset_stream_loader.md`: Dataset Stream Loader 구현 의도와 사용법
- `docs/tasks/task3_rule_based_roi_gate.md`: Rule-based ROI Gate 구현 의도와 사용법
- `docs/vision_frontend_validation_roadmap.md`: 장기 검증 로드맵
- `.agents/project_context.md`: Codex 또는 자동화 agent가 먼저 확인할 문서 목록과 작업 원칙

## 협업 메모

- Phase 1에서는 SNN, 실제 NPX 하드웨어, RTSP, DeepStream, TensorRT를 구현하지 않습니다.
- 실험 config는 결과 재현성에 직접 영향을 주므로 report에 함께 기록합니다.
- ROI metadata schema는 inference, evaluation, visualization이 공유하는 인터페이스로 관리합니다.
- `outputs/`에는 실험 결과가 저장되며, 대용량 결과물은 Git에 포함하지 않는 방향을 권장합니다.
