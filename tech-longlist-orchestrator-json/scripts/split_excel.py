#!/usr/bin/env python3
"""
Excel分割スクリプト - tech-longlist-orchestrator用

複数エージェント並列処理のため、調査リストExcelファイルを均等に分割する。
"""

import pandas as pd
import sys
import os
from pathlib import Path
from datetime import datetime


def split_excel_for_agents(input_file, num_agents, output_dir='work_dir/input'):
    """
    Excelファイルを複数エージェント用に分割

    Args:
        input_file (str): 元のExcelファイルパス
        num_agents (int): エージェント数
        output_dir (str): 出力ディレクトリ

    Returns:
        list: 分割ファイルのパスリスト
        dict: 分割情報メタデータ
    """
    # 出力ディレクトリ作成
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Excelファイル読み込み
    print(f"\n{'='*60}")
    print(f"Excel分割処理開始")
    print(f"{'='*60}")
    print(f"入力ファイル: {input_file}")

    try:
        df = pd.read_excel(input_file)
    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません - {input_file}")
        sys.exit(1)
    except Exception as e:
        print(f"エラー: Excelファイルの読み込みに失敗 - {e}")
        sys.exit(1)

    total_rows = len(df)

    # エージェント数の妥当性チェック
    if num_agents < 1:
        print(f"エラー: エージェント数は1以上である必要があります")
        sys.exit(1)

    if num_agents > total_rows:
        print(f"警告: エージェント数({num_agents})が調査対象数({total_rows})より多い")
        print(f"エージェント数を{total_rows}に調整します")
        num_agents = total_rows

    print(f"\n総調査対象数: {total_rows}件")
    print(f"起動エージェント数: {num_agents}エージェント")
    print(f"出力ディレクトリ: {output_dir}")
    print(f"\n{'='*60}")

    # 各エージェントの担当件数を計算
    chunk_size = total_rows // num_agents
    remainder = total_rows % num_agents

    output_files = []
    metadata = {
        'total_rows': total_rows,
        'num_agents': num_agents,
        'timestamp': datetime.now().isoformat(),
        'agents': []
    }

    start_idx = 0

    for i in range(num_agents):
        # 端数を最初のエージェントに割り当て
        current_chunk_size = chunk_size + (1 if i < remainder else 0)
        end_idx = start_idx + current_chunk_size

        # データ抽出
        chunk = df.iloc[start_idx:end_idx].copy()

        # ファイル出力
        output_file = os.path.join(output_dir, f'調査リスト_エージェント{i+1}.xlsx')
        chunk.to_excel(output_file, index=False)

        output_files.append(output_file)

        # ID範囲を取得（No列が存在する場合）
        if 'No' in df.columns:
            start_id = df.iloc[start_idx]['No']
            end_id = df.iloc[end_idx-1]['No']
            id_range = f"{start_id}-{end_id}"
        else:
            id_range = f"{start_idx+1}-{end_idx}"

        print(f"Agent {i+1:2d}: {len(chunk):3d}件 | ID範囲: {id_range} | {output_file}")

        # メタデータ記録
        metadata['agents'].append({
            'agent_id': i + 1,
            'file': output_file,
            'row_count': len(chunk),
            'id_range': id_range,
            'start_idx': start_idx,
            'end_idx': end_idx - 1
        })

        start_idx = end_idx

    print(f"{'='*60}")
    print(f"分割完了: {len(output_files)}ファイル生成")
    print(f"{'='*60}\n")

    return output_files, metadata


def validate_split(metadata):
    """
    分割結果の検証

    Args:
        metadata (dict): 分割情報メタデータ

    Returns:
        bool: 検証成功ならTrue
    """
    print(f"\n{'='*60}")
    print(f"分割結果検証")
    print(f"{'='*60}")

    total_rows = metadata['total_rows']
    sum_rows = sum(agent['row_count'] for agent in metadata['agents'])

    print(f"元データ行数: {total_rows}")
    print(f"分割後合計行数: {sum_rows}")

    if total_rows != sum_rows:
        print(f"❌ エラー: 行数が一致しません")
        return False

    # ファイル存在確認
    missing_files = []
    for agent in metadata['agents']:
        if not os.path.exists(agent['file']):
            missing_files.append(agent['file'])

    if missing_files:
        print(f"❌ エラー: 以下のファイルが生成されていません:")
        for file in missing_files:
            print(f"  - {file}")
        return False

    print(f"✅ 検証成功: 全ファイル生成完了、行数一致")
    print(f"{'='*60}\n")

    return True


def main():
    """メイン処理"""
    if len(sys.argv) < 3:
        print("使用方法: python split_excel.py <input_file> <num_agents> [output_dir]")
        print("\n例:")
        print("  python split_excel.py 調査リスト.xlsx 4")
        print("  python split_excel.py 調査リスト.xlsx 4 custom_output/")
        sys.exit(1)

    input_file = sys.argv[1]
    num_agents = int(sys.argv[2])
    output_dir = sys.argv[3] if len(sys.argv) > 3 else 'work_dir/input'

    # 分割実行
    output_files, metadata = split_excel_for_agents(input_file, num_agents, output_dir)

    # 検証
    if validate_split(metadata):
        print("✅ 分割処理が正常に完了しました\n")
        return 0
    else:
        print("❌ 分割処理でエラーが発生しました\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
