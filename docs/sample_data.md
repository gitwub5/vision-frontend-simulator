# Sample Data Utility

## 목적

검증용 sample data 준비 절차를 코드로 남겨 팀원이 같은 데이터를 쉽게 받을 수 있게 한다.

원칙:

- 공개 배포 가능한 sample만 자동 다운로드한다.
- 약관 동의, 로그인, 사내 권한이 필요한 데이터는 자동 다운로드하지 않고 준비 방법만 안내한다.
- 원본 데이터는 `data/` 아래에 저장하고 Git에는 포함하지 않는다.

## 사용법

지원 dataset 목록 확인:

```bash
python tools/download_sample_data.py --list
```

공개 VIRAT-Aerial sample 다운로드:

```bash
python tools/download_sample_data.py --dataset virat-aerial-sample
```

이미 받은 파일을 다시 받고 싶으면:

```bash
python tools/download_sample_data.py --dataset virat-aerial-sample --force
```

## 현재 지원 항목

### 자동 다운로드

```text
virat-aerial-sample
```

용도:

- pipeline smoke test
- Dataset loader 확인
- ROI metadata 저장 흐름 확인

주의:

- 항공/이동 카메라 영상이므로 fixed-camera ROI 품질 검증에는 적합하지 않다.
- 실제 Phase 1 성능 검증 지표 판단에는 사용하지 않는다.

### 수동 준비 안내

```text
virat-ground
od-virat-tiny
internal-cctv
```

용도:

- 실제 Phase 1 fixed-camera validation

주의:

- 데이터 사용 약관, 접근 권한, 사내 보안 정책을 먼저 확인한다.
- raw video와 annotation은 Git에 포함하지 않는다.

## VIRAT-Aerial sample

다운로드 위치:

```text
data/virat_aerial/09152008flight2tape3_1.mpg
```

사용 config:

```text
configs/dataset.virat_aerial_sample.yaml
```

실행 예:

```bash
python experiments/inspect_dataset_stream.py \
  --config configs/dataset.virat_aerial_sample.yaml \
  --limit 3
```

```bash
python experiments/run_rule_roi_baseline.py \
  --dataset-config configs/dataset.virat_aerial_sample.yaml \
  --gate-config configs/npx_gate.yaml \
  --limit 30
```
