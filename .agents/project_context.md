# Agent Project Context

이 파일은 Codex 또는 다른 자동화 agent가 이 프로젝트에서 작업을 시작하기 전에 확인해야 할 문서와 판단 기준을 정리한다.

## 반드시 먼저 읽을 문서

1. `README.md`
   - 프로젝트 목적, 현재 Phase, 협업자가 알아야 할 요약을 확인한다.

2. `docs/plan/phase1_implementation_plan.md`
   - Phase 1 구현 체크리스트, 작업 단위, R&R, config 초안, metadata schema를 확인한다.

3. `docs/plan/phase1_validation_plan.md`
   - Phase 1의 세부 기능 요구사항, ROI Gate 동작, 평가 지표를 확인한다.

4. `docs/plan/vision_frontend_validation_roadmap.md`
   - Phase 1 이후 SNN, 멀티카메라, GPU 최적화, 하드웨어 spec 도출 방향을 확인한다.

## 문서 역할

- `README.md`: 팀원이 처음 보는 프로젝트 소개 문서
- `docs/plan/phase1_implementation_plan.md`: Phase 1 구현 현황과 협업 기준
- `docs/plan/phase1_validation_plan.md`: Phase 1 상세 설계와 검증 기준
- `docs/plan/`: 다음 Phase 계획과 세부 검증 문서를 정리하는 위치
- `docs/plan/vision_frontend_validation_roadmap.md`: 장기 로드맵과 단계별 성공 기준

## 현재 우선순위

현재 구현 우선순위는 Phase 1이다.

```text
Rule-based ROI Gate 검증
```

Phase 1에서는 실제 NPX 하드웨어, SNN 학습, RTSP, DeepStream, TensorRT를 구현하지 않는다. 먼저 software emulator로 ROI Gate의 효과를 검증한다.

## 작업 원칙

- 기존 문서의 검증 기준과 충돌하는 구현을 하지 않는다.
- 실험 결과에 영향을 주는 threshold, ROI policy, model config는 config 파일로 관리한다.
- ROI metadata schema는 inference, evaluation, visualization이 공유하는 계약으로 취급한다.
- 대용량 데이터셋, 모델 weight, 실험 output은 Git에 포함하지 않는다.
- Phase 2 이후 기능은 Phase 1 결과가 나온 뒤 확장한다.
