#!/usr/bin/env python3
"""
YOLO 학습용 이미지 중복 제거 도구
유사한 이미지들을 찾아서 중복을 제거하는 스크립트
"""

import os
import argparse
import shutil
import json
import csv
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("⚠️  진행률 표시를 위해 tqdm 설치를 권장합니다: pip install tqdm")

try:
    from imagededup.methods import PHash, DHash, AHash, WHash, CNN
    from imagededup.utils import plot_duplicates
except ImportError:
    print("imagededup 라이브러리가 설치되지 않았습니다. 다음 명령어로 설치해주세요:")
    print("pip install imagededup")
    exit(1)

# 지원되는 이미지 확장자
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}

class DuplicateImageRemover:
    def __init__(self, method='phash', threshold=3):
        """
        이미지 중복 제거기 초기화
        
        Args:
            method: 사용할 해싱 방법 ('phash', 'dhash', 'ahash', 'whash', 'cnn')
            threshold: 유사도 임계값 (낮을수록 더 유사한 이미지만 중복으로 판단, 3 = 95% 유사도)
        """
        self.threshold = threshold
        self.method_name = method
        
        # 해싱 방법 선택
        if method == 'phash':
            self.hasher = PHash()
        elif method == 'dhash':
            self.hasher = DHash()
        elif method == 'ahash':
            self.hasher = AHash()
        elif method == 'whash':
            self.hasher = WHash()
        elif method == 'cnn':
            self.hasher = CNN()
        else:
            raise ValueError(f"지원되지 않는 방법: {method}")
    
    def find_all_images(self, root_dir: str) -> List[str]:
        """
        지정된 디렉토리에서 재귀적으로 모든 이미지 파일을 찾는다
        
        Args:
            root_dir: 검색할 루트 디렉토리
            
        Returns:
            이미지 파일 경로 리스트
        """
        print("🔍 이미지 파일 검색 중...")
        image_files = []
        root_path = Path(root_dir)
        
        if not root_path.exists():
            raise FileNotFoundError(f"디렉토리를 찾을 수 없습니다: {root_dir}")
        
        # 모든 파일 경로 수집
        all_files = list(root_path.rglob('*'))
        
        # 진행률 표시와 함께 이미지 파일 필터링
        if TQDM_AVAILABLE:
            with tqdm(all_files, desc="📂 파일 스캔", unit="files") as pbar:
                for file_path in pbar:
                    if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                        image_files.append(str(file_path))
                        pbar.set_postfix(found=len(image_files))
        else:
            # tqdm이 없을 때는 주기적으로 진행상황 출력
            for i, file_path in enumerate(all_files):
                if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    image_files.append(str(file_path))
                
                # 10000개마다 진행상황 출력
                if i % 10000 == 0 and i > 0:
                    print(f"   스캔 중... {i:,}개 파일 확인, {len(image_files):,}개 이미지 발견")
        
        print(f"✅ 총 {len(image_files):,}개 이미지 파일 발견")
        return sorted(image_files)
    
    def find_duplicates(self, image_dir: str) -> Dict[str, List[str]]:
        """
        중복 이미지를 찾는다
        
        Args:
            image_dir: 이미지가 들어있는 디렉토리
            
        Returns:
            중복 이미지 매핑 (키: 대표이미지, 값: 중복이미지 리스트)
        """
        print(f"\n🔍 {self.method_name.upper()} 방법으로 이미지 해시 생성 중...")
        start_time = time.time()
        
        # 이미지 인코딩 생성 (imagededup 내부에서 진행률 표시)
        try:
            encodings = self.hasher.encode_images(image_dir=image_dir)
        except Exception as e:
            print(f"❌ 인코딩 중 오류 발생: {e}")
            raise
        
        encoding_time = time.time() - start_time
        print(f"✅ 총 {len(encodings):,}개 이미지 인코딩 완료 ({encoding_time:.1f}초 소요)")
        
        # 중복 찾기 시작
        print(f"\n🔄 중복 이미지 탐지 중... (임계값: {self.threshold}, 95% 유사도 기준)")
        comparison_start = time.time()
        
        if hasattr(self.hasher, 'find_duplicates') and self.method_name != 'cnn':
            # threshold가 정수인지 확인하고 범위 체크
            threshold_int = int(self.threshold)
            if threshold_int < 0 or threshold_int > 64:
                raise ValueError(f"threshold는 0-64 사이의 정수여야 합니다. 현재 값: {threshold_int}")
            
            duplicates = self.hasher.find_duplicates(
                encoding_map=encodings, 
                max_distance_threshold=threshold_int
            )
        else:
            duplicates = self.hasher.find_duplicates(encoding_map=encodings)
        
        comparison_time = time.time() - comparison_start
        
        # 중복 통계 계산
        total_duplicates = sum(len(dups) for dups in duplicates.values() if dups)
        duplicate_groups = len([k for k, v in duplicates.items() if v])
        
        print(f"✅ 중복 탐지 완료 ({comparison_time:.1f}초 소요)")
        print(f"📊 발견된 중복: {duplicate_groups:,}개 그룹, {total_duplicates:,}개 중복 이미지")
        
        return duplicates
    
    def group_duplicates(self, duplicates: Dict[str, List[str]]) -> List[Set[str]]:
        """
        중복 이미지들을 그룹으로 묶는다
        
        Args:
            duplicates: imagededup에서 반환된 중복 매핑
            
        Returns:
            중복 그룹 리스트 (각 그룹은 중복된 이미지들의 집합)
        """
        # 모든 중복 관계를 그래프로 만들기
        graph = defaultdict(set)
        all_images = set()
        
        for main_image, duplicate_list in duplicates.items():
            if duplicate_list:  # 중복이 있는 경우만
                all_images.add(main_image)
                for dup_image in duplicate_list:
                    all_images.add(dup_image)
                    graph[main_image].add(dup_image)
                    graph[dup_image].add(main_image)
        
        # 연결된 컴포넌트 찾기 (DFS)
        visited = set()
        groups = []
        
        for image in all_images:
            if image not in visited:
                group = set()
                stack = [image]
                
                while stack:
                    current = stack.pop()
                    if current not in visited:
                        visited.add(current)
                        group.add(current)
                        
                        # 연결된 모든 이미지 추가
                        for neighbor in graph[current]:
                            if neighbor not in visited:
                                stack.append(neighbor)
                
                if len(group) > 1:  # 2개 이상인 그룹만 추가
                    groups.append(group)
        
        return groups
    
    def select_representative(self, group: Set[str]) -> str:
        """
        중복 그룹에서 대표 이미지를 선정한다
        파일 크기가 가장 큰 이미지를 대표로 선정 (화질이 좋을 가능성)
        
        Args:
            group: 중복 이미지 그룹
            
        Returns:
            대표 이미지 경로
        """
        best_image = None
        best_size = 0
        
        for image_path in group:
            try:
                file_size = os.path.getsize(image_path)
                if file_size > best_size:
                    best_size = file_size
                    best_image = image_path
            except OSError:
                continue
        
        return best_image or list(group)[0]  # 파일이 없으면 첫 번째 선택
    
    def save_results_to_file(self, result: Dict, output_dir: str = "."):
        """
        결과를 JSON과 CSV 파일로 저장한다
        
        Args:
            result: 처리 결과 딕셔너리
            output_dir: 저장할 디렉토리
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON 파일로 저장 (상세 정보)
        json_filename = f"duplicate_analysis_{timestamp}.json"
        json_path = os.path.join(output_dir, json_filename)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"📄 상세 결과 저장: {json_filename}")
        
        # CSV 파일로 저장 (삭제 대상 목록)
        if result.get("status") == "success" and result.get("groups"):
            csv_filename = f"duplicates_to_remove_{timestamp}.csv"
            csv_path = os.path.join(output_dir, csv_filename)
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['그룹ID', '대표이미지', '삭제대상이미지', '파일크기(bytes)'])
                
                for group in result["groups"]:
                    representative = group["representative"]
                    for duplicate in group["duplicates"]:
                        try:
                            file_size = os.path.getsize(duplicate)
                        except:
                            file_size = 0
                        writer.writerow([
                            group["group_id"],
                            os.path.basename(representative),
                            duplicate,
                            file_size
                        ])
            
            print(f"📊 삭제 대상 목록: {csv_filename}")
        
        # 요약 텍스트 파일 저장
        summary_filename = f"duplicate_summary_{timestamp}.txt"
        summary_path = os.path.join(output_dir, summary_filename)
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("🖼️ 이미지 중복 분석 결과 요약\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"분석 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"방법: {self.method_name}\n")
            f.write(f"임계값: {self.threshold}\n\n")
            
            if result.get("status") == "success":
                f.write(f"📊 통계:\n")
                f.write(f"   • 전체 이미지: {result['total_images']:,}개\n")
                f.write(f"   • 중복 그룹: {result['duplicate_groups']:,}개\n")
                f.write(f"   • 중복 이미지: {result['total_duplicates']:,}개\n")
                f.write(f"   • 삭제 대상: {result['total_to_remove']:,}개\n")
                f.write(f"   • 보존 이미지: {result['remaining_images']:,}개\n\n")
                
                # 용량 절약 계산
                total_saved_size = 0
                for group in result.get("groups", []):
                    for dup_path in group["duplicates"]:
                        try:
                            total_saved_size += os.path.getsize(dup_path)
                        except:
                            pass
                
                if total_saved_size > 0:
                    saved_gb = total_saved_size / (1024**3)
                    f.write(f"💾 절약 가능 용량: {saved_gb:.2f} GB\n\n")
            
            elif result.get("status") == "no_duplicates":
                f.write("✅ 중복 이미지가 발견되지 않았습니다.\n")
        
        print(f"📋 요약 보고서: {summary_filename}")

    def process_duplicates(self, image_dir: str, delete: bool = False, 
                          backup_dir: str = None, save_results: bool = True) -> Dict:
        """
        중복 이미지를 처리한다 (삭제 또는 정보 출력)
        
        Args:
            image_dir: 이미지 디렉토리
            delete: True이면 삭제, False이면 정보만 출력
            backup_dir: 백업 디렉토리 (삭제 전 백업)
            
        Returns:
            처리 결과 정보
        """
        # 모든 이미지 파일 찾기
        all_images = self.find_all_images(image_dir)
        print(f"📂 총 {len(all_images)}개의 이미지 파일을 찾았습니다.")
        
        if len(all_images) == 0:
            print("❌ 이미지 파일을 찾을 수 없습니다.")
            return {"status": "no_images"}
        
        # 중복 찾기
        duplicates = self.find_duplicates(image_dir)
        
        # 중복 그룹 생성
        duplicate_groups = self.group_duplicates(duplicates)
        
        if not duplicate_groups:
            print("✅ 중복 이미지가 발견되지 않았습니다.")
            return {"status": "no_duplicates", "total_images": len(all_images)}
        
        # 결과 정보 수집
        total_duplicates = 0
        total_to_remove = 0
        group_info = []
        
        for i, group in enumerate(duplicate_groups, 1):
            representative = self.select_representative(group)
            to_remove = group - {representative}
            
            group_data = {
                "group_id": i,
                "total_count": len(group),
                "representative": representative,
                "duplicates": list(to_remove),
                "remove_count": len(to_remove)
            }
            group_info.append(group_data)
            
            total_duplicates += len(group)
            total_to_remove += len(to_remove)
        
        # 결과 출력
        print(f"\n📊 중복 분석 결과:")
        print(f"   • 전체 이미지: {len(all_images)}개")
        print(f"   • 중복 그룹: {len(duplicate_groups)}개")
        print(f"   • 중복 이미지: {total_duplicates}개")
        print(f"   • 삭제 대상: {total_to_remove}개")
        print(f"   • 보존 이미지: {len(all_images) - total_to_remove}개")
        
        # 그룹별 상세 정보
        print(f"\n📋 그룹별 상세 정보:")
        for group_data in group_info:
            print(f"   그룹 {group_data['group_id']}: {group_data['total_count']}개 중 {group_data['remove_count']}개 삭제 예정")
            print(f"      대표 이미지: {os.path.basename(group_data['representative'])}")
            if len(group_data['duplicates']) <= 5:
                for dup in group_data['duplicates']:
                    print(f"      삭제 대상: {os.path.basename(dup)}")
            else:
                for dup in group_data['duplicates'][:3]:
                    print(f"      삭제 대상: {os.path.basename(dup)}")
                print(f"      ... 외 {len(group_data['duplicates']) - 3}개")
            print()
        
        # 실제 삭제 수행
        deleted_count = 0
        if delete:
            if backup_dir:
                os.makedirs(backup_dir, exist_ok=True)
                print(f"💾 백업 디렉토리: {backup_dir}")
            
            print(f"\n🗑️  파일 삭제 시작...")
            
            # 삭제할 전체 파일 수 계산
            total_to_delete = sum(len(group_data['duplicates']) for group_data in group_info)
            
            if TQDM_AVAILABLE:
                # tqdm으로 삭제 진행률 표시
                with tqdm(total=total_to_delete, desc="🗑️ 파일 삭제", unit="files") as pbar:
                    for group_data in group_info:
                        for img_path in group_data['duplicates']:
                            try:
                                # 백업
                                if backup_dir:
                                    backup_path = os.path.join(backup_dir, os.path.basename(img_path))
                                    shutil.copy2(img_path, backup_path)
                                
                                # 삭제
                                os.remove(img_path)
                                deleted_count += 1
                                pbar.set_postfix(deleted=deleted_count)
                                pbar.update(1)
                                
                            except Exception as e:
                                pbar.write(f"❌ 삭제 실패 {os.path.basename(img_path)}: {e}")
            else:
                # tqdm 없을 때 주기적 진행률 출력
                for group_data in group_info:
                    for img_path in group_data['duplicates']:
                        try:
                            # 백업
                            if backup_dir:
                                backup_path = os.path.join(backup_dir, os.path.basename(img_path))
                                shutil.copy2(img_path, backup_path)
                            
                            # 삭제
                            os.remove(img_path)
                            deleted_count += 1
                            
                            # 100개마다 진행상황 출력
                            if deleted_count % 100 == 0:
                                print(f"   삭제 진행률: {deleted_count:,}/{total_to_delete:,} ({deleted_count/total_to_delete*100:.1f}%)")
                            
                        except Exception as e:
                            print(f"❌ 삭제 실패 {os.path.basename(img_path)}: {e}")
            
            print(f"\n✅ 삭제 완료: {deleted_count:,}개 파일")
        
        result = {
            "status": "success",
            "total_images": len(all_images),
            "duplicate_groups": len(duplicate_groups),
            "total_duplicates": total_duplicates,
            "total_to_remove": total_to_remove,
            "remaining_images": len(all_images) - total_to_remove,
            "groups": group_info,
            "deleted": deleted_count if delete else 0,
            "analysis_time": datetime.now().isoformat(),
            "method": self.method_name,
            "threshold": self.threshold,
            "source_directory": image_dir
        }
        
        # 결과를 파일로 저장
        if save_results:
            self.save_results_to_file(result)
        
        return result

def main():
    parser = argparse.ArgumentParser(
        description="YOLO 학습용 이미지 중복 제거 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python duplicate_image_remover.py /path/to/images --method phash
  python duplicate_image_remover.py /path/to/images --delete --backup ./backup
  python duplicate_image_remover.py /path/to/images --method cnn --threshold 0.9
        """
    )
    
    parser.add_argument('image_dir', help='이미지가 들어있는 디렉토리 경로')
    parser.add_argument('--delete', action='store_true', 
                       help='중복 이미지를 실제로 삭제 (기본값: False, 정보만 출력)')
    parser.add_argument('--method', choices=['phash', 'dhash', 'ahash', 'whash', 'cnn'],
                       default='phash', help='중복 탐지 방법 (기본값: phash)')
    parser.add_argument('--threshold', type=int, default=3,
                       help='유사도 임계값 (낮을수록 더 엄격, 기본값: 3 = 95%% 유사도)')
    parser.add_argument('--backup', type=str,
                       help='삭제 전 백업할 디렉토리 (--delete와 함께 사용)')
    
    args = parser.parse_args()
    
    # 입력 검증
    if not os.path.exists(args.image_dir):
        print(f"❌ 디렉토리를 찾을 수 없습니다: {args.image_dir}")
        return
    
    if args.delete and not args.backup:
        confirm = input("⚠️  백업 없이 삭제하시겠습니까? 삭제된 파일은 복구할 수 없습니다. (y/N): ")
        if confirm.lower() != 'y':
            print("작업이 취소되었습니다.")
            return
    
    try:
        # 중복 제거기 생성
        remover = DuplicateImageRemover(method=args.method, threshold=args.threshold)
        
        print(f"🚀 중복 이미지 분석 시작...")
        print(f"   • 디렉토리: {args.image_dir}")
        print(f"   • 방법: {args.method}")
        print(f"   • 임계값: {args.threshold}")
        print(f"   • 삭제 모드: {'예' if args.delete else '아니오'}")
        if args.backup:
            print(f"   • 백업 디렉토리: {args.backup}")
        print()
        
        # 처리 실행
        result = remover.process_duplicates(
            image_dir=args.image_dir,
            delete=args.delete,
            backup_dir=args.backup
        )
        
        if result["status"] == "success":
            print(f"\n🎉 작업 완료!")
            if args.delete:
                print(f"   • {result['deleted']}개 파일이 삭제되었습니다.")
                print(f"   • {result['remaining_images']}개 파일이 남아있습니다.")
            else:
                print(f"   • {result['total_to_remove']}개 파일이 삭제 대상입니다.")
                print(f"   • --delete 옵션을 사용하여 실제 삭제를 수행할 수 있습니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 