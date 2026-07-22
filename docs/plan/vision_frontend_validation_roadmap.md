# Vision Frontend Simulator 검증 단계 계획

## 0. 검증 목표

본 문서는 `vision-frontend-simulator` 프로젝트의 단계별 검증 계획을 정리한 문서이다.

프로젝트의 최종 목표는 **카메라와 GPU 사이에 위치하는 Vision Frontend Gate가 전체 프레임 기반 GPU 추론 대비 연산량을 줄이면서도 객체 탐지 성능을 유지할 수 있는지** 검증하는 것이다.

초기에는 실제 NPX 하드웨어나 SNN 모델 없이 rule-based ROI gate로 시작하고, 이후 SNN 기반 ROI proposal, 멀티카메라 시뮬레이션, GPU 파이프라인 최적화, 하드웨어 요구사항 도출 단계로 확장한다.

---

## 1. 전체 검증 로드맵

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

---

# Phase 1. Rule-based ROI Gate 검증

## 목적

Vision Frontend Gate 구조 자체가 GPU workload를 줄일 가능성이 있는지 검증한다.

이 단계에서는 SNN 모델을 학습하지 않고, 단순 영상처리 기반으로 ROI를 생성한다.

## 핵심 질문

> 전체 프레임을 YOLOv8로 처리하는 방식 대비, 움직임 기반 ROI crop만 YOLOv8에 입력했을 때 객체 탐지 recall을 유지하면서 연산량을 줄일 수 있는가?

## 구현 범위

- Dataset frame loader
- Full-frame YOLOv8 baseline
- Gray 변환
- Resize
- Frame Difference
- Threshold 기반 motion map
- Noise filtering
- Connected component 기반 ROI 생성
- ROI merge
- Temporal hold
- Periodic full-frame check
- ROI crop 생성
- ROI crop 기반 YOLOv8 inference
- 원본 좌표계로 detection 결과 복원
- 비교 리포트 생성

## 비교군

```text
A. Full-frame YOLOv8
B. Rule-based ROI Gate + ROI YOLOv8
C. Rule-based ROI Gate + ROI YOLOv8 + Periodic Full-frame Check
```

## 주요 데이터셋

- OD-VIRAT Tiny
- VIRAT 일부 시퀀스

## 주요 지표

- Object Recall 유지율
- ROI Containment Rate
- YOLO 호출 수 감소율
- YOLO 입력 픽셀 면적 감소율
- 평균 ROI 개수
- 평균 ROI 면적
- 처리 시간
- Gate latency

## 최소 성공 기준

```text
Object Recall 유지율 >= 95%
ROI Containment Rate >= 98%
YOLO 입력 면적 감소율 >= 50%
평균 ROI 수 <= 3
평균 ROI 면적 <= 전체 프레임의 30%
```

## 산출물

- Full-frame baseline 결과
- ROI-gated inference 결과
- workload reduction report
- ROI visualization
- 실패 사례 목록

## 다음 단계 진입 조건

```text
Object Recall 유지율 >= 98%
YOLO workload reduction >= 50%
Rule-based 방식의 한계 사례가 명확히 수집됨
```

한계 사례 예시:

- 조명 변화
- 그림자
- 나뭇잎 / 비 / 눈
- 압축 노이즈
- 정지 객체 누락
- 작은 객체 누락
- ROI 과다 생성

---

# Phase 2. SNN Tile Eventness Model 검증

## 목적

Rule-based ROI 생성기를 SNN 기반 ROI proposal 모델로 대체하여, 단순 motion detection보다 더 좋은 ROI 품질과 낮은 false wake-up을 달성할 수 있는지 검증한다.

## 핵심 질문

> SNN이 ON/OFF event-like tensor를 입력받아 GPU가 봐야 할 tile 또는 ROI를 더 정확하게 선별할 수 있는가?

## 구현 범위

- Event-like tensor 생성
- ON/OFF event map 생성
- Timestep buffer 구성
- Tile label 생성
- SNN Tile Eventness Model 구현
- SNN 학습 파이프라인
- SNN heatmap 기반 ROI 생성
- Rule-based ROI와 SNN ROI 비교

## SNN 입력

```text
T x C x H x W

T = 4 ~ 8 timesteps
C = 2 channels: ON event, OFF event
H, W = 128x128 또는 256x144
```

## SNN 출력

```text
tile objectness heatmap
예: 16x9 또는 16x16
```

각 tile은 GPU가 봐야 할 가능성을 나타낸다.

## 학습 라벨 생성

기존 detection annotation을 tile label로 변환한다.

```text
GT bounding box와 겹치는 tile = positive
GT bounding box와 겹치지 않는 tile = negative
```

객체 class가 있는 경우 다음과 같이 확장 가능하다.

```text
person bbox  -> person-like tile
vehicle bbox -> vehicle-like tile
```

## Loss 후보

- Focal Loss
- Weighted Binary Cross Entropy
- Dice Loss 보조항

## 비교군

```text
A. Rule-based ROI Gate
B. SNN Tile Eventness ROI Gate
```

## 주요 지표

- ROI Containment Rate
- Object Recall 유지율
- False Wake-up 감소율
- 평균 ROI 면적
- 평균 ROI 개수
- GPU workload reduction
- SNN inference latency

## 성공 기준

```text
Rule-based ROI 대비 false wake-up 30~50% 이상 감소
ROI Containment Rate >= 98%
Object Recall 유지율 >= 98%
GPU workload reduction >= 50%
```

## 산출물

- 학습된 SNN ROI proposal 모델
- SNN heatmap visualization
- Rule-based vs SNN ROI 비교 리포트
- false wake-up 감소 분석
- 실패 사례 분석

---

# Phase 3. Multi-camera Simulation

## 목적

Vision Frontend Gate가 여러 카메라 스트림 환경에서 GPU당 처리 가능한 카메라 수를 늘릴 수 있는지 검증한다.

## 핵심 질문

> 여러 카메라가 동시에 입력될 때, ROI Gate를 사용하면 동일 GPU에서 더 많은 stream을 처리할 수 있는가?

## 구현 범위

- Multi-stream replay
- Camera ID 관리
- Stream별 ROI Gate 실행
- GPU inference queue 구성
- Full-frame multi-camera baseline
- ROI-gated multi-camera 비교
- Stream별 latency / throughput 측정

## 입력 구성

```text
camera_01: VIRAT sequence A
camera_02: VIRAT sequence B
camera_03: VIRAT sequence C
...
```

또는 동일 영상을 시간 offset을 다르게 주어 다중 카메라처럼 replay한다.

## 비교군

```text
A. N개 stream full-frame YOLOv8
B. N개 stream ROI-gated YOLOv8
C. N개 stream ROI-gated YOLOv8 + periodic full-frame check
```

## 주요 지표

- GPU 한 대 기준 처리 가능한 stream 수
- 평균 FPS
- stream별 E2E latency
- GPU utilization
- GPU inference queue length
- Object Recall 유지율
- workload reduction

## 성공 기준

```text
동일 GPU에서 처리 가능한 camera stream 수 1.5배 이상 증가
사업화 후보 기준: 2배 이상 증가
Object Recall 유지율 >= 95~98%
```

## 산출물

- Multi-camera benchmark report
- Stream count vs FPS graph
- Stream count vs GPU utilization graph
- ROI Gate 적용 전후 비교 리포트

---

# Phase 4. GPU Pipeline Optimization

## 목적

ROI crop이 여러 개 발생할 때 GPU에 효율적으로 입력하는 구조를 검증한다.

ROI 기반 처리는 ROI가 많아지면 full-frame 1회 추론보다 비효율적일 수 있다. 이 단계에서는 ROI batching, packing, dynamic scheduling을 검토한다.

## 핵심 질문

> ROI crop 여러 개를 GPU에 넣을 때, 어떤 방식이 가장 효율적인가?

## 구현 범위

- ROI batching
- ROI packing
- Dynamic batch size
- ROI resize 최적화
- ROI 개수 제한 정책
- Full-frame fallback 정책
- TensorRT 적용 검토
- DeepStream 연동 검토

## 최적화 후보

### 1. ROI Batching

```text
여러 ROI crop
→ batch tensor
→ YOLOv8 batch inference
```

### 2. ROI Packing

```text
여러 ROI crop
→ 하나의 canvas에 packing
→ YOLOv8 1회 inference
→ detection 결과를 각 ROI 좌표로 복원
```

### 3. Dynamic Policy

```text
ROI 수가 적음 -> ROI crop inference
ROI 수가 많음 -> full-frame inference
ROI가 너무 큼 -> full-frame inference
```

## 주요 지표

- ROI 개수별 latency
- ROI 개수별 GPU utilization
- ROI batching 효과
- ROI packing 효과
- Full-frame 대비 이득이 사라지는 ROI 개수
- Recall 유지율

## 성공 기준

```text
ROI 수 1~3개 구간에서 full-frame 대비 latency 또는 workload 감소
ROI 수 증가 시 full-frame fallback 기준 정의
GPU inference pipeline overhead 정량화
```

## 산출물

- ROI batching benchmark
- ROI packing benchmark
- ROI/full-frame switching policy
- GPU pipeline optimization report

---

# Phase 5. Hardware-oriented NPX Spec 도출

## 목적

소프트웨어 시뮬레이션 결과를 바탕으로 실제 Vision Frontend / NPX Gate가 가져야 할 최소 하드웨어 요구사항을 도출한다.

## 핵심 질문

> 실제 하드웨어로 구현하려면 어떤 입력 처리량, 메모리, latency, 인터페이스가 필요한가?

## 정리 항목

### 입력 처리 요구사항

- 입력 해상도
- 분석 해상도
- FPS
- 지원 카메라 수
- 입력 포맷
- event map 생성 방식

### 처리 성능 요구사항

- Gate latency
- ROI generation latency
- SNN inference latency
- 지원 timestep 수
- tile heatmap 출력 해상도

### 메모리 요구사항

- frame buffer 크기
- previous frame buffer 크기
- event buffer 크기
- ROI metadata buffer
- multi-camera queue

### 인터페이스 요구사항

- 카메라 입력 인터페이스 후보
  - RTSP / Ethernet
  - GigE Vision
  - USB3 Vision
  - MIPI CSI-2
  - GMSL / FPD-Link
- GPU 연결 인터페이스 후보
  - PCIe
  - 10GbE
  - shared memory
  - DMA-BUF
  - DeepStream metadata

### 전력 목표

- camera당 gate 처리 전력
- 8ch / 16ch gateway 전력
- GPU 절감 대비 NPX 추가 전력

## 성공 기준

```text
8ch 이상 처리 가능한 최소 사양 도출
Gate latency <= 10ms 목표 설정
GPU workload reduction 50~70% 달성을 위한 하드웨어 조건 정리
```

## 산출물

- Hardware requirement draft
- ROI metadata schema
- Event tensor format
- Interface requirement document
- Minimum viable NPX Gate spec

---

# Phase 6. 실제 Edge Pipeline PoC

## 목적

실제 카메라 또는 RTSP stream을 사용해 end-to-end Vision Frontend Gate 구조를 검증한다.

## 핵심 질문

> 실제 카메라 입력에서도 dataset simulation과 유사한 GPU 절감 효과가 나타나는가?

## 구성 후보

```text
RTSP / GigE Camera
        ↓
Vision Frontend Gate Emulator
        ↓
Jetson / GPU Server
        ↓
YOLOv8 TensorRT
        ↓
Result Dashboard
```

## 구현 범위

- RTSP stream input
- 실시간 frame processing
- ROI Gate 실시간 동작
- GPU YOLOv8 TensorRT inference
- 결과 시각화
- 로그 저장
- latency 측정

## 주요 검증 환경

- 실내 고정 카메라
- 복도 / 출입구
- 창고형 공간
- 산업 안전 유사 장면

## 주요 지표

- 실시간 FPS
- E2E latency
- ROI 품질
- false trigger
- GPU 사용량
- 이벤트 누락
- 환경 변화 대응

## 성공 기준

```text
실제 RTSP 입력에서 ROI Gate 실시간 동작
Object Recall 유지율 >= 95%
GPU workload reduction >= 50%
E2E latency <= 300ms
```

## 산출물

- 실시간 PoC demo
- RTSP input benchmark
- 실제 환경 실패 사례
- 개선 요구사항

---

# Phase 7. 사업화 기준 검증

## 목적

고객 관점에서 Vision Frontend Gate가 실제로 도입 가치가 있는지 판단할 수 있는 수치를 검증한다.

## 핵심 질문

> NPX / Vision Frontend Gate를 추가했을 때, 고객이 GPU 또는 엣지 서버 비용을 줄일 만큼 명확한 이득이 있는가?

## 핵심 KPI

```text
Critical Event Recall >= 99%
ROI Containment Rate >= 99%
GPU inference workload reduction >= 70%
동일 GPU당 camera 수 2배 이상 증가
Gate latency <= 10ms
False wake-up reduction vs rule baseline >= 70%
```

## 비용 관점 지표

- GPU 장치 수 감소
- GPU 사용률 감소
- 전력 감소
- 카메라당 처리 비용 감소
- 동일 GPU에서 처리 가능한 camera 수 증가
- 네트워크 대역폭 감소 가능성
- 저장량 감소 가능성

## 사업화 후보 시장

우선순위가 높은 시장:

- 산업 안전
- 무인 창고
- 출입구 / 금지구역 감시
- 원격 설비 감시
- 물류 센터
- 고정형 CCTV 기반 이벤트 감지

우선순위가 낮은 시장:

- 항상 움직임이 많은 교차로
- 혼잡한 리테일 매장
- 이동형 로봇 카메라
- 초고해상도 결함 검사
- 모든 프레임 분석이 필요한 얼굴 인식

## 최종 판단 기준

```text
1. 단순 motion detection보다 충분히 나은가?
2. 기존 GPU-only 구조보다 비용 이점이 있는가?
3. 기존 edge NPU 구조와 비교해 차별성이 있는가?
4. 실제 고객 환경에서 false trigger를 줄일 수 있는가?
5. GPU당 처리 가능한 camera 수를 최소 2배 이상 늘릴 수 있는가?
```

## 산출물

- Business validation report
- Target market fit analysis
- Minimum product requirement
- Customer PoC scenario
- Go / No-Go decision document

---

# 단계별 요약표

| Phase | 목표 | 핵심 구현 | 성공 기준 |
|---|---|---|---|
| Phase 1 | ROI Gate 구조 가능성 검증 | Rule-based ROI + YOLOv8 | workload 50% 감소, recall 95~98% 유지 |
| Phase 2 | SNN ROI 모델 검증 | Event tensor + SNN heatmap | false wake-up 감소, recall 98% 유지 |
| Phase 3 | 멀티카메라 확장성 검증 | Multi-stream replay | 처리 stream 수 1.5~2배 증가 |
| Phase 4 | GPU 파이프라인 최적화 | batching / packing / fallback | ROI 추론 overhead 최소화 |
| Phase 5 | 하드웨어 요구사항 도출 | spec 정리 | 8ch 이상 처리 사양 도출 |
| Phase 6 | 실제 카메라 PoC | RTSP + TensorRT | 실시간 동작, workload 50% 감소 |
| Phase 7 | 사업화 검증 | 고객 KPI 평가 | GPU workload 70% 감소, camera 수 2배 증가 |

---

# 현재 우선 실행 항목

가장 먼저 구현할 항목은 Phase 1이다.

## Phase 1 작업 순서

```text
1. 프로젝트 스캐폴딩 생성
2. 데이터셋 loader 구현
3. Full-frame YOLOv8 baseline 구현
4. Rule-based ROI Gate 구현
5. ROI crop YOLO 구현
6. 평가 코드 구현
7. 시각화 코드 구현
8. comparison report 생성
```

## Phase 1 완료 후 판단

Phase 1 결과가 다음 조건을 만족하면 Phase 2로 진행한다.

```text
Object Recall 유지율 >= 95~98%
YOLO workload reduction >= 50%
ROI Containment Rate >= 98%
Rule-based ROI의 실패 사례 수집 완료
```

만약 위 조건을 만족하지 못하면, 바로 SNN으로 넘어가기보다 다음을 먼저 조정한다.

- ROI margin
- temporal hold
- periodic full-frame check 주기
- threshold
- morphology filter
- ROI merge 정책
- full-frame fallback 조건
