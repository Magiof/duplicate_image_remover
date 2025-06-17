#!/usr/bin/env python3
"""
YOLO 학습용 이미지 중복 제거 도구 사용 예시
"""

import os
import tempfile
import shutil
from duplicate_image_remover import DuplicateImageRemover

def create_sample_images():
    """
    테스트용 샘플 이미지들을 생성합니다.
    실제 사용시에는 이 함수는 필요하지 않습니다.
    """
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        print("PIL(Pillow) 라이브러리가 필요합니다: pip install Pillow")
        return None
    
    # 임시 디렉토리 생성
    temp_dir = tempfile.mkdtemp(prefix="yolo_images_")
    print(f"📁 샘플 이미지 디렉토리: {temp_dir}")
    
    # 서브 디렉토리 생성
    train_dir = os.path.join(temp_dir, "train")
    val_dir = os.path.join(temp_dir, "val")
    os.makedirs(train_dir, exist_ok=True)
    os.makedirs(val_dir, exist_ok=True)
    
    # 기본 이미지 생성 (640x640, YOLO 표준 크기)
    base_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    
    # 다양한 이미지 생성
    images_to_create = [
        # 원본 이미지들
        ("original_1.jpg", base_image),
        ("original_2.jpg", np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)),
        
        # 유사한 이미지들 (원본에 약간의 노이즈 추가)
        ("similar_1.jpg", np.clip(base_image + np.random.randint(-10, 10, (640, 640, 3)), 0, 255)),
        ("similar_2.jpg", np.clip(base_image + np.random.randint(-5, 5, (640, 640, 3)), 0, 255)),
        ("similar_3.jpg", np.clip(base_image + np.random.randint(-15, 15, (640, 640, 3)), 0, 255)),
        
        # 완전히 다른 이미지
        ("different_1.jpg", np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)),
    ]
    
    # train 디렉토리에 이미지 저장
    for filename, img_array in images_to_create:
        img = Image.fromarray(img_array.astype(np.uint8))
        img.save(os.path.join(train_dir, filename))
    
    # val 디렉토리에도 몇개 복사 (중복 테스트용)
    shutil.copy2(os.path.join(train_dir, "original_1.jpg"), 
                 os.path.join(val_dir, "val_original_1.jpg"))
    shutil.copy2(os.path.join(train_dir, "similar_1.jpg"), 
                 os.path.join(val_dir, "val_similar_1.jpg"))
    
    print(f"✅ {len(images_to_create) + 2}개의 샘플 이미지가 생성되었습니다.")
    return temp_dir

def example_analysis_only():
    """
    예시 1: 분석만 수행 (삭제하지 않음)
    """
    print("\n" + "="*60)
    print("📊 예시 1: 중복 이미지 분석만 수행")
    print("="*60)
    
    # 샘플 이미지 생성
    image_dir = create_sample_images()
    if not image_dir:
        return
    
    try:
        # DuplicateImageRemover 인스턴스 생성
        remover = DuplicateImageRemover(method='phash', threshold=10)
        
        # 중복 분석 수행
        result = remover.process_duplicates(image_dir, delete=False)
        
        if result["status"] == "success":
            print(f"\n✨ 분석 완료! {result['total_to_remove']}개 파일이 중복으로 발견되었습니다.")
        
    finally:
        # 임시 디렉토리 정리
        shutil.rmtree(image_dir)
        print(f"🧹 임시 파일 정리 완료")

def example_with_backup():
    """
    예시 2: 백업과 함께 실제 삭제 수행
    """
    print("\n" + "="*60)
    print("🗑️  예시 2: 백업과 함께 중복 이미지 삭제")
    print("="*60)
    
    # 샘플 이미지 생성
    image_dir = create_sample_images()
    if not image_dir:
        return
    
    backup_dir = os.path.join(os.path.dirname(image_dir), "backup")
    
    try:
        # DuplicateImageRemover 인스턴스 생성
        remover = DuplicateImageRemover(method='phash', threshold=8)
        
        print(f"📁 이미지 디렉토리: {image_dir}")
        print(f"💾 백업 디렉토리: {backup_dir}")
        
        # 삭제 전 파일 개수 확인
        before_count = len(remover.find_all_images(image_dir))
        print(f"🔢 삭제 전 이미지 개수: {before_count}")
        
        # 중복 삭제 수행
        result = remover.process_duplicates(image_dir, delete=True, backup_dir=backup_dir)
        
        # 삭제 후 파일 개수 확인
        after_count = len(remover.find_all_images(image_dir))
        print(f"🔢 삭제 후 이미지 개수: {after_count}")
        
        if result["status"] == "success":
            print(f"\n✨ 삭제 완료! {result['deleted']}개 파일이 삭제되었습니다.")
            print(f"💾 백업된 파일: {len(os.listdir(backup_dir)) if os.path.exists(backup_dir) else 0}개")
        
    finally:
        # 임시 디렉토리 정리
        shutil.rmtree(image_dir)
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        print(f"🧹 임시 파일 정리 완료")

def example_different_methods():
    """
    예시 3: 다양한 중복 탐지 방법 비교
    """
    print("\n" + "="*60)
    print("🔍 예시 3: 다양한 중복 탐지 방법 비교")
    print("="*60)
    
    # 샘플 이미지 생성
    image_dir = create_sample_images()
    if not image_dir:
        return
    
    methods = ['phash', 'dhash', 'ahash']  # CNN은 시간이 오래 걸려서 제외
    
    try:
        for method in methods:
            print(f"\n🔎 {method.upper()} 방법으로 분석 중...")
            
            remover = DuplicateImageRemover(method=method, threshold=10)
            result = remover.process_duplicates(image_dir, delete=False)
            
            if result["status"] == "success":
                print(f"   📊 {method}: {result['duplicate_groups']}개 그룹, {result['total_to_remove']}개 삭제 대상")
            else:
                print(f"   ❌ {method}: 중복 이미지 없음")
    
    finally:
        # 임시 디렉토리 정리
        shutil.rmtree(image_dir)
        print(f"\n🧹 임시 파일 정리 완료")

def main():
    """
    모든 예시 실행
    """
    print("🚀 YOLO 학습용 이미지 중복 제거 도구 예시")
    print("이 예시는 샘플 이미지를 생성하여 동작을 보여줍니다.")
    print("실제 사용시에는 duplicate_image_remover.py를 직접 사용하세요.")
    
    try:
        # 예시 1: 분석만
        example_analysis_only()
        
        # 예시 2: 백업과 함께 삭제
        example_with_backup()
        
        # 예시 3: 다양한 방법 비교
        example_different_methods()
        
        print("\n" + "="*60)
        print("✅ 모든 예시가 완료되었습니다!")
        print("💡 실제 사용법:")
        print("   python duplicate_image_remover.py /path/to/your/images")
        print("   python duplicate_image_remover.py /path/to/your/images --delete --backup ./backup")
        print("="*60)
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 