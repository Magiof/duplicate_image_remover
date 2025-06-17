# 🖼️ 이미지 중복 제거 도구

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![imagededup](https://img.shields.io/badge/powered%20by-imagededup-orange.svg)](https://github.com/idealo/imagededup)

비디오 프레임에서 추출한 **120만개 대용량 이미지**에서도 효율적으로 중복을 찾아 제거하는 고성능 도구입니다. 
**95% 유사도 기본 설정**으로 정확한 중복 탐지를 수행하며, **실시간 진행률 표시**와 **자동 결과 저장** 기능을 제공합니다.

## ✨ 주요 특징

### 🚀 **고성능 처리**
- **대용량 지원**: 120만개+ 이미지 처리 가능
- **실시간 진행률**: tqdm 기반 시각적 진행률 표시
- **멀티코어 활용**: AMD Ryzen 최적화 성능
- **메모리 효율**: 24GB RAM에서 안정적 동작

### 🎯 **정확한 중복 탐지**
- **95% 유사도 기본**: threshold=3으로 최적화
- **5가지 알고리즘**: PHash, DHash, AHash, WHash, CNN
- **지능형 그룹화**: 연결된 중복들을 자동으로 그룹화
- **대표 이미지 보존**: 최고 화질 이미지 자동 선정

### 📊 **완벽한 결과 관리**
- **자동 파일 저장**: JSON, CSV, TXT 형식으로 결과 저장
- **상세 분석**: 그룹별 중복 정보와 절약 용량 계산
- **안전한 백업**: 삭제 전 자동 백업 지원
- **복원 가능**: 삭제 목록 CSV로 실수 복구 지원

## 🚀 빠른 시작

### 1. 설치
```bash
# 필수 라이브러리 설치
pip install imagededup tqdm

# 또는 requirements.txt 사용
pip install -r requirements.txt
```

### 2. 기본 사용 (95% 유사도)
```bash
# 분석만 수행 (삭제하지 않음)
python duplicate_image_remover.py "C:/your/image/folder"

# 실제 삭제 + 백업
python duplicate_image_remover.py "C:/your/image/folder" --delete --backup "./backup"
```

### 3. 실행 결과
```
🚀 중복 이미지 분석 시작...
   • 디렉토리: C:/your/image/folder
   • 방법: PHASH
   • 임계값: 3 (95% 유사도)
   • 삭제 모드: 아니오

🔍 이미지 파일 검색 중...
📂 파일 스캔: 100%|████████████| 1.2M/1.2M [02:15<00:00, 8.9kfiles/s] found=1200000
✅ 총 1,200,000개 이미지 파일 발견

🔍 PHASH 방법으로 이미지 해시 생성 중...
✅ 총 1,200,000개 이미지 인코딩 완료 (8542.3초 소요)

🔄 중복 이미지 탐지 중... (임계값: 3, 95% 유사도 기준)
✅ 중복 탐지 완료 (2847.1초 소요)
📊 발견된 중복: 15,420개 그룹, 184,500개 중복 이미지

📊 중복 분석 결과:
   • 전체 이미지: 1,200,000개
   • 중복 그룹: 15,420개
   • 중복 이미지: 184,500개
   • 삭제 대상: 169,080개
   • 보존 이미지: 1,030,920개

💾 절약 가능 용량: 847.2 GB

📄 상세 결과 저장: duplicate_analysis_20241219_143022.json
📊 삭제 대상 목록: duplicates_to_remove_20241219_143022.csv
📋 요약 보고서: duplicate_summary_20241219_143022.txt

🎉 작업 완료!
```

## 📋 생성되는 결과 파일들

### 📄 `duplicate_analysis_YYYYMMDD_HHMMSS.json`
전체 분석 결과의 상세 데이터 (프로그램에서 재사용 가능)

### 📊 `duplicates_to_remove_YYYYMMDD_HHMMSS.csv`
삭제 대상 이미지 목록 (Excel에서 열기 가능)
```csv
그룹ID,대표이미지,삭제대상이미지,파일크기(bytes)
1,frame_001.jpg,C:/images/frame_002.jpg,2847392
1,frame_001.jpg,C:/images/frame_003.jpg,2835748
```

### 📋 `duplicate_summary_YYYYMMDD_HHMMSS.txt`
사람이 읽기 쉬운 요약 보고서
```
🖼️ 이미지 중복 분석 결과 요약
==================================================

분석 일시: 2024-12-19 14:30:22
방법: phash
임계값: 3

📊 통계:
   • 전체 이미지: 1,200,000개
   • 중복 그룹: 15,420개
   • 중복 이미지: 184,500개
   • 삭제 대상: 169,080개
   • 보존 이미지: 1,030,920개

💾 절약 가능 용량: 847.20 GB
```

## ⚙️ 고급 설정

### 📊 유사도 임계값 (Threshold) 설정

| Threshold | 유사도 | 설명 | 추천 용도 |
|-----------|---------|------|----------|
| **1** | **98.4%** | 매우 엄격 | 거의 동일한 이미지만 |
| **2** | **96.9%** | 엄격 | 약간의 압축/리사이즈 허용 |
| **3** | **95.3%** | **기본 (권장)** | **균형잡힌 정확도** |
| **5** | **92.2%** | 관대 | 조명/각도 변화 허용 |
| **10** | **84.4%** | 매우 관대 | 많은 변화 허용 |

### 🔧 다양한 처리 방법

```bash
# 97% 유사도로 더 엄격하게
python duplicate_image_remover.py ./images --threshold 2

# 빠른 처리 (DHash)
python duplicate_image_remover.py ./images --method dhash

# 최고 정확도 (느림, GPU 권장)
python duplicate_image_remover.py ./images --method cnn

# 관대한 기준 (92% 유사도)
python duplicate_image_remover.py ./images --threshold 5
```

## 🖥️ 시스템 요구사항 및 성능

### 권장 사양
- **CPU**: 멀티코어 (AMD Ryzen 7+ 또는 Intel i7+)
- **RAM**: 16GB+ (120만개 이미지의 경우 24GB 권장)
- **저장공간**: SSD 권장 (HDD는 2-3배 느림)
- **GPU**: CNN 방법 사용시 NVIDIA CUDA 지원

### 📈 성능 벤치마크 (AMD Ryzen 7 8845HS 기준)

| 이미지 수 | PHash | DHash | CNN |
|-----------|--------|--------|-----|
| **10,000개** | 2분 | 1분 | 4시간 |
| **100,000개** | 20분 | 10분 | 2일 |
| **1,200,000개** | **12-15시간** | **4-8시간** | **😢🤔🤯** |

## 🎯 해시 알고리즘 비교

| 방법 | 속도 | 정확도 | 메모리 | 추천도 | 특징 |
|------|------|--------|--------|--------|------|
| **PHash** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 🥇 **최고** | 시각적 유사성, 회전/크기 강건 |
| **DHash** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 🥈 **대용량용** | 매우 빠름, 색상 변화 강건 |
| **AHash** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 🥉 | 가장 빠름, 단순 비교 |
| **WHash** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | 📊 **분석용** | 웨이블릿 기반, 중간 성능 |
| **CNN** | ⭐ | ⭐⭐⭐⭐⭐ | ⭐ | 🎯 **정밀용** | 최고 정확도, GPU 필요 |

## 💡 사용 팁

### 🎯 **단계별 처리 권장** (대용량 데이터셋)
```bash
# 1단계: 빠른 정리 (DHash)
python duplicate_image_remover.py ./images --method dhash --threshold 3

# 2단계: 정밀 분석 (PHash) - 남은 이미지 대상
python duplicate_image_remover.py ./images --method phash --threshold 2

# 3단계: 최종 검증 (CNN) - 소량 남은 경우
python duplicate_image_remover.py ./images --method cnn
```

### 📊 **메모리 최적화**
```bash
# 시스템 리소스 확인
python -c "
import psutil
print(f'사용 가능 메모리: {psutil.virtual_memory().available / (1024**3):.1f} GB')
print(f'CPU 코어 수: {psutil.cpu_count()} 개')
"
```

### 🔍 **결과 파일 활용**
```python
# JSON 결과 파일 읽기
import json
with open('duplicate_analysis_20241219_143022.json', 'r', encoding='utf-8') as f:
    result = json.load(f)
    print(f"절약 가능 용량: {result['total_to_remove']}개 파일")

# CSV에서 삭제 대상 확인
import pandas as pd
df = pd.read_csv('duplicates_to_remove_20241219_143022.csv')
print(f"총 절약 용량: {df['파일크기(bytes)'].sum() / (1024**3):.2f} GB")
```

## 🛠️ 문제 해결

### ❌ **일반적인 오류들**

#### 1. 메모리 부족
```bash
# 해결: 더 작은 배치로 처리하거나 DHash 사용
python duplicate_image_remover.py ./images --method dhash
```

#### 2. 권한 오류 (Windows)
```bash
# 해결: 관리자 권한으로 PowerShell 실행
pip install --user imagededup
```

#### 3. 진행률 표시 안됨
```bash
# 해결: tqdm 설치
pip install tqdm
```

### 🚨 **응급 복구**
삭제를 잘못했을 경우:
1. `backup` 폴더에서 파일 복원
2. `duplicates_to_remove_*.csv` 파일로 삭제 목록 확인
3. 필요한 파일만 선별적으로 복원

## 📄 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능합니다.

## 🤝 기여하기

- 🐛 **버그 리포트**: Issues에 상세한 오류 정보와 함께 제출
- 💡 **기능 제안**: 새로운 기능 아이디어 공유
- 🔧 **코드 기여**: Pull Request로 개선사항 제출

## 🔗 관련 링크

- 📚 [imagededup 공식 문서](https://idealo.github.io/imagededup/)
- 🎯 [YOLO 공식 사이트](https://ultralytics.com/)
- 📊 [tqdm 진행률 표시](https://github.com/tqdm/tqdm)
- 🖼️ [Pillow 이미지 처리](https://pillow.readthedocs.io/)

---

<div align="center">

**⭐ 도움이 되었다면 스타를 눌러주세요! ⭐**

</div> 