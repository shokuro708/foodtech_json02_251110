#!/usr/bin/env python3
"""
JSON統合スクリプト - tech-longlist-orchestrator-json用

複数エージェントが生成した技術ロングリストJSONファイルを収集・整理する。
"""

import json
import glob
import shutil
import os
from pathlib import Path
from datetime import datetime


def collect_json_files(output_dir='work_dir/output', final_dir='work_dir/final_output'):
    """
    各エージェントの検証済みJSONファイルを収集・整理

    Args:
        output_dir (str): エージェント出力ディレクトリ
        final_dir (str): 最終出力ディレクトリ

    Returns:
        list: 収集したファイルのリスト
        dict: 収集統計情報
    """
    print(f"\n{'='*60}")
    print(f"JSON収集処理開始")
    print(f"{'='*60}")

    output_path = Path(output_dir)
    final_path = Path(final_dir)
    final_path.mkdir(parents=True, exist_ok=True)

    # 各エージェントの検証済みJSONファイルを検索
    print(f"検索ディレクトリ: {output_dir}")
    print(f"出力ディレクトリ: {final_dir}\n")

    verified_files = []
    agent_stats = []

    # agent_*ディレクトリを走査
    agent_dirs = sorted(output_path.glob('agent_*'))

    if not agent_dirs:
        print(f"❌ エラー: agent_*ディレクトリが見つかりません")
        raise FileNotFoundError(f"agent_*ディレクトリが見つかりません: {output_dir}")

    print(f"検出エージェント数: {len(agent_dirs)}個\n")
    print(f"{'='*60}")

    for agent_dir in agent_dirs:
        agent_num = agent_dir.name.replace('agent_', '')
        agent_files = list(agent_dir.glob('*_verified.json'))

        if agent_files:
            verified_files.extend(agent_files)

            # エージェント統計情報
            agent_stats.append({
                'agent_id': agent_num,
                'directory': str(agent_dir),
                'file_count': len(agent_files),
                'files': [f.name for f in agent_files]
            })

            print(f"Agent {agent_num}: {len(agent_files):3d}件 | {agent_dir}")
        else:
            print(f"⚠️  Agent {agent_num}: 検証済みJSONファイルなし | {agent_dir}")

    if not verified_files:
        print(f"\n❌ エラー: 検証済みJSONファイルが見つかりません")
        print(f"検索パターン: {output_dir}/agent_*/*_verified.json")
        raise FileNotFoundError(f"検証済みJSONファイルが見つかりません")

    print(f"\n{'='*60}")
    print(f"収集ファイル数: {len(verified_files)}件")
    print(f"{'='*60}\n")

    # ファイル名でソート（ID順）
    verified_files.sort(key=lambda x: x.name)

    return verified_files, agent_stats


def copy_and_analyze_files(verified_files, final_dir, agent_stats):
    """
    JSONファイルをfinal_outputへコピーし、内容を分析

    Args:
        verified_files (list): 検証済みJSONファイルのリスト
        final_dir (str): 最終出力ディレクトリ
        agent_stats (list): エージェント統計情報

    Returns:
        dict: 統計情報
    """
    print(f"{'='*60}")
    print(f"ファイルコピーと分析")
    print(f"{'='*60}\n")

    final_path = Path(final_dir)
    collected = []
    score_stats = []
    errors = []

    for src_file in verified_files:
        dst_file = final_path / src_file.name

        try:
            # ファイルコピー
            shutil.copy2(src_file, dst_file)

            # JSON内容読み込み
            with open(src_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 検証結果抽出
            verification = data.get('検証結果', {})
            score = verification.get('総合スコア', 'N/A')
            grade = verification.get('評価', 'N/A')

            # 基本情報抽出
            basic_info = data.get('基本情報', {})
            org_info = data.get('組織情報', {})

            file_id = basic_info.get('ID', 'Unknown')
            title = basic_info.get('タイトル', 'No Title')[:50]
            company = org_info.get('組織名', 'Unknown')

            # 統計情報記録
            score_stats.append({
                'id': file_id,
                'file': src_file.name,
                'score': score,
                'grade': grade,
                'company': company,
                'title': title
            })

            print(f"✅ {src_file.name}")
            print(f"   ID: {file_id} | スコア: {score}点 ({grade}) | {company}")

            collected.append(dst_file)

        except json.JSONDecodeError as e:
            error_msg = f"JSONパースエラー: {src_file.name} - {e}"
            print(f"❌ {error_msg}")
            errors.append(error_msg)
        except Exception as e:
            error_msg = f"処理エラー: {src_file.name} - {e}"
            print(f"❌ {error_msg}")
            errors.append(error_msg)

    print(f"\n{'='*60}")
    print(f"コピー完了: {len(collected)}件")
    if errors:
        print(f"⚠️  エラー: {len(errors)}件")
    print(f"{'='*60}\n")

    # 統計情報作成
    stats = {
        'total_files': len(verified_files),
        'collected_files': len(collected),
        'failed_files': len(errors),
        'agent_count': len(agent_stats),
        'agent_stats': agent_stats,
        'score_stats': score_stats,
        'errors': errors,
        'timestamp': datetime.now().isoformat(),
        'output_dir': final_dir
    }

    return stats


def check_duplicates(verified_files):
    """
    重複IDをチェック

    Args:
        verified_files (list): 検証済みJSONファイルのリスト

    Returns:
        dict: 重複情報
    """
    duplicate_info = {
        'has_duplicates': False,
        'duplicate_count': 0,
        'duplicate_ids': []
    }

    # ファイル名からID抽出（{ID}_{組織名}_verified.json形式を想定）
    file_ids = [f.name.split('_')[0] for f in verified_files]

    # 重複検出
    seen = set()
    duplicates = []
    for file_id in file_ids:
        if file_id in seen:
            duplicates.append(file_id)
        seen.add(file_id)

    if duplicates:
        duplicate_info['has_duplicates'] = True
        duplicate_info['duplicate_count'] = len(duplicates)
        duplicate_info['duplicate_ids'] = list(set(duplicates))

        print(f"\n⚠️  警告: 重複ID検出 - {len(duplicates)}件")
        print(f"{'='*60}")

        for dup_id in duplicate_info['duplicate_ids'][:10]:
            dup_files = [f for f in verified_files if f.name.startswith(dup_id + '_')]
            print(f"ID: {dup_id} | 重複数: {len(dup_files)}件")
            for dup_file in dup_files:
                print(f"  - {dup_file.name}")

        if len(duplicate_info['duplicate_ids']) > 10:
            print(f"... 他 {len(duplicate_info['duplicate_ids']) - 10}件の重複ID")

        print(f"{'='*60}\n")

    return duplicate_info


def calculate_quality_stats(score_stats):
    """
    品質統計を計算

    Args:
        score_stats (list): スコア統計情報

    Returns:
        dict: 品質統計
    """
    quality_stats = {
        'total_count': len(score_stats),
        'grade_a': 0,
        'grade_b': 0,
        'grade_c': 0,
        'grade_d': 0,
        'grade_na': 0,
        'avg_score': 0,
        'min_score': None,
        'max_score': None
    }

    # スコアを数値に変換
    numeric_scores = []
    for stat in score_stats:
        score = stat.get('score')
        grade = stat.get('grade', 'N/A')

        # グレード集計
        if grade == 'A':
            quality_stats['grade_a'] += 1
        elif grade == 'B':
            quality_stats['grade_b'] += 1
        elif grade == 'C':
            quality_stats['grade_c'] += 1
        elif grade == 'D':
            quality_stats['grade_d'] += 1
        else:
            quality_stats['grade_na'] += 1

        # スコア集計
        if isinstance(score, (int, float)):
            numeric_scores.append(score)

    # 平均・最小・最大スコア計算
    if numeric_scores:
        quality_stats['avg_score'] = sum(numeric_scores) / len(numeric_scores)
        quality_stats['min_score'] = min(numeric_scores)
        quality_stats['max_score'] = max(numeric_scores)

    return quality_stats


def generate_collection_report(stats, report_file='JSON収集レポート.md'):
    """
    収集レポート生成

    Args:
        stats (dict): 統計情報
        report_file (str): レポートファイル名

    Returns:
        str: レポートファイルパス
    """
    print(f"収集レポート生成中: {report_file}")

    # 品質統計計算
    quality_stats = calculate_quality_stats(stats['score_stats'])

    report_content = f"""# 技術ロングリストJSON収集レポート

## 収集サマリー

- **収集日時**: {stats['timestamp']}
- **総ファイル数**: {stats['total_files']}件
- **収集成功**: {stats['collected_files']}件
- **収集失敗**: {stats['failed_files']}件
- **エージェント数**: {stats['agent_count']}個
- **出力ディレクトリ**: {stats['output_dir']}

## 品質統計

- **平均スコア**: {quality_stats['avg_score']:.1f}点
- **最高スコア**: {quality_stats['max_score']}点
- **最低スコア**: {quality_stats['min_score']}点

### 評価分布

| 評価 | 件数 | 割合 |
|------|------|------|
| A評価 (90点以上) | {quality_stats['grade_a']}件 | {quality_stats['grade_a']/quality_stats['total_count']*100:.1f}% |
| B評価 (80-89点) | {quality_stats['grade_b']}件 | {quality_stats['grade_b']/quality_stats['total_count']*100:.1f}% |
| C評価 (70-79点) | {quality_stats['grade_c']}件 | {quality_stats['grade_c']/quality_stats['total_count']*100:.1f}% |
| D評価 (70点未満) | {quality_stats['grade_d']}件 | {quality_stats['grade_d']/quality_stats['total_count']*100:.1f}% |
| N/A | {quality_stats['grade_na']}件 | {quality_stats['grade_na']/quality_stats['total_count']*100:.1f}% |

## エージェント別統計

| Agent | 収集ファイル数 | ディレクトリ |
|-------|--------------|-------------|
"""

    for agent in stats['agent_stats']:
        report_content += f"| Agent {agent['agent_id']} | {agent['file_count']}件 | {agent['directory']} |\n"

    # エラー情報
    if stats['errors']:
        report_content += f"\n## ⚠️ エラー情報\n\n"
        report_content += f"- **エラー件数**: {len(stats['errors'])}件\n\n"

        report_content += "### エラー詳細\n\n"
        for i, error in enumerate(stats['errors'][:20], 1):
            report_content += f"{i}. {error}\n"

        if len(stats['errors']) > 20:
            report_content += f"\n... 他 {len(stats['errors']) - 20}件のエラー\n"

    # 低スコア項目
    low_score_items = [s for s in stats['score_stats'] if isinstance(s['score'], (int, float)) and s['score'] < 70]
    if low_score_items:
        report_content += f"\n## 要注意項目 (70点未満)\n\n"
        report_content += f"- **要注意件数**: {len(low_score_items)}件\n\n"

        report_content += "| ID | スコア | 評価 | 組織名 | ファイル |\n"
        report_content += "|-------|--------|------|--------|----------|\n"

        for item in sorted(low_score_items, key=lambda x: x['score'])[:10]:
            report_content += f"| {item['id']} | {item['score']}点 | {item['grade']} | {item['company']} | {item['file']} |\n"

        if len(low_score_items) > 10:
            report_content += f"\n... 他 {len(low_score_items) - 10}件の要注意項目\n"

    report_content += f"\n## 推奨次ステップ\n\n"
    report_content += f"1. 収集ファイル確認: {stats['output_dir']}\n"

    if stats['errors']:
        report_content += f"2. エラーファイル調査: 上記のエラー詳細を確認\n"

    if low_score_items:
        report_content += f"3. 低スコア項目レビュー: 70点未満の項目を人手で確認\n"

    report_content += f"\n## 収集ファイル一覧\n\n"

    # ファイル一覧（ID順でソート）
    sorted_scores = sorted(stats['score_stats'], key=lambda x: x['id'])

    report_content += "| ID | スコア | 評価 | 組織名 | タイトル | ファイル |\n"
    report_content += "|----|--------|------|--------|----------|----------|\n"

    for item in sorted_scores:
        score_str = f"{item['score']}点" if isinstance(item['score'], (int, float)) else str(item['score'])
        report_content += f"| {item['id']} | {score_str} | {item['grade']} | {item['company'][:20]} | {item['title'][:30]} | {item['file']} |\n"

    report_content += f"\n---\n生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

    # ファイル出力
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)

    print(f"✅ レポート生成完了: {report_file}\n")

    return report_file


def main():
    """メイン処理"""
    import sys

    if len(sys.argv) < 2:
        output_dir = 'work_dir/output'
        final_dir = 'work_dir/final_output'
    elif len(sys.argv) == 2:
        output_dir = sys.argv[1]
        final_dir = 'work_dir/final_output'
    else:
        output_dir = sys.argv[1]
        final_dir = sys.argv[2]

    print(f"使用方法: python merge_results.py [output_dir] [final_dir]")
    print(f"\n現在の設定:")
    print(f"  エージェント出力ディレクトリ: {output_dir}")
    print(f"  最終出力ディレクトリ: {final_dir}\n")

    try:
        # JSONファイル収集
        verified_files, agent_stats = collect_json_files(output_dir, final_dir)

        # 重複チェック
        duplicate_info = check_duplicates(verified_files)

        # ファイルコピーと分析
        stats = copy_and_analyze_files(verified_files, final_dir, agent_stats)

        # 重複情報を統計に追加
        stats['duplicate_info'] = duplicate_info

        # レポート生成
        report_file = generate_collection_report(stats)

        # サマリー表示
        print(f"{'='*60}")
        print(f"収集完了サマリー")
        print(f"{'='*60}")
        print(f"総ファイル数: {stats['total_files']}件")
        print(f"収集成功: {stats['collected_files']}件")
        print(f"収集失敗: {stats['failed_files']}件")
        print(f"エージェント数: {stats['agent_count']}個")

        if duplicate_info['has_duplicates']:
            print(f"⚠️  重複ID: {duplicate_info['duplicate_count']}件")
        else:
            print(f"✅ 重複なし")

        print(f"{'='*60}\n")

        print("✅ JSON収集処理が正常に完了しました\n")
        return 0

    except Exception as e:
        print(f"\n❌ 致命的エラー: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
