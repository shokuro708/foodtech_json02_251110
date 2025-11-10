---
name: tech-longlist-orchestrator-json
description: 技術調査リストExcelファイルを自動分割し、複数のtech-longlist-pipeline-jsonエージェントを並列起動して分散処理を実行。各エージェントが個別のJSONファイルを生成し、完了後の結果を収集・整理して出力する。大規模な技術調査リスト（50件以上）を効率的に処理し、処理時間を大幅に短縮する。
---

# Tech Longlist Orchestrator-json

複数のtech-longlist-pipeline-jsonエージェントを並列制御し、大規模技術調査リストを分散処理するオーケストレーター。

## Overview

このスキルは、大規模な技術調査リスト（50件以上推奨）を最適な数のエージェントに自動分割し、並列実行を制御する。各エージェントが独立してパイプライン（JSON作成→検証→修正）を実行し、完了後に結果をディレクトリ単位で整理して出力する。

### Key Features
- ✅ 調査対象数に応じた最適エージェント数の自動判定
- ✅ Excel自動分割とエージェント専用ファイル生成
- ✅ 複数エージェントの並列起動と進捗監視
- ✅ データ競合を回避する独立実行制御（各エージェントは専用ディレクトリに出力）
- ✅ 結果の自動収集と品質検証
- ✅ JSON形式での個別出力とディレクトリ整理
- ✅ 統合レポート生成

## Performance Benefits

| 調査対象数 | 単一エージェント | オーケストレーター（4並列） | 処理時間削減 |
|-----------|----------------|------------------------|------------|
| 12件 | 約15分 | 約5分 | 66%削減 |
| 50件 | 約60分 | 約18分 | 70%削減 |
| 100件 | 約120分 | 約35分 | 71%削減 |
| 200件 | 約240分 | 約70分 | 71%削減 |

## Workflow

### Phase 0: 初期化と分析

**入力**: 調査リストExcelファイル（例: 調査リスト.xlsx）

**処理内容**:
1. Excelファイルの読み込みと検証
2. 調査対象数のカウント
3. 最適エージェント数の決定
   - 1-11件: 1エージェント（オーケストレーション不要）
   - 12-24件: 2エージェント
   - 25-49件: 3エージェント
   - 50-99件: 4エージェント
   - 100件以上: 5-8エージェント（システムリソースに応じて調整）
4. 作業ディレクトリ構造の準備

```
work_dir/
├── input/
│   ├── 調査リスト_エージェント1.xlsx
│   ├── 調査リスト_エージェント2.xlsx
│   ├── 調査リスト_エージェント3.xlsx
│   └── 調査リスト_エージェント4.xlsx
├── output/
│   ├── agent_1/
│   │   ├── 001_Company_Name.json
│   │   ├── 002_Company_Name.json
│   │   ├── ...
│   │   ├── 001_Company_Name_verified.json
│   │   ├── 002_Company_Name_verified.json
│   │   └── ...
│   ├── agent_2/
│   │   ├── 026_Company_Name.json
│   │   └── ...
│   ├── agent_3/
│   │   ├── 051_Company_Name.json
│   │   └── ...
│   └── agent_4/
│       ├── 076_Company_Name.json
│       └── ...
├── final_output/
│   ├── 001_Company_Name_verified.json
│   ├── 002_Company_Name_verified.json
│   ├── ...
│   └── 100_Company_Name_verified.json
└── logs/
```

### Phase 1: データ分割

**処理内容**:
1. Pythonスクリプトを使用してExcelファイルを分割
2. 各エージェント用のExcelファイル生成
3. 分割データの検証（行数、列構造の確認）
4. メタデータの記録（各エージェントの担当範囲）

**分割戦略**:
- 均等分割: 調査対象数 ÷ エージェント数
- 端数処理: 最後のエージェントに割り当て
- ID範囲の記録: 各エージェントが処理するID範囲を記録

**出力**:
- 調査リスト_エージェント1.xlsx (ID: 1-25)
- 調査リスト_エージェント2.xlsx (ID: 26-50)
- 調査リスト_エージェント3.xlsx (ID: 51-75)
- 調査リスト_エージェント4.xlsx (ID: 76-100)

### Phase 2: 並列エージェント起動

**処理内容**:
1. 複数のtech-longlist-pipelineエージェントを並列起動
2. 各エージェントに専用の入出力ディレクトリを割り当て
3. エージェント起動パラメータの設定
   - input_file: 調査リスト_エージェントN.xlsx
   - output_dir: work_dir/output/agent_N/
   - agent_id: N
4. 並列実行制御（Taskツールを使用）

**エージェント起動コマンド例**:
```python
# 各エージェントに以下を実行依頼
Task(
    description=f"tech-longlist-pipeline実行 (Agent {i})",
    prompt=f"""
    調査リスト_エージェント{i}.xlsxファイルを使用して、
    技術ロングリスト作成パイプライン（作成→検証→修正）を実行してください。

    ファイルパス: work_dir/input/調査リスト_エージェント{i}.xlsx
    出力先: work_dir/output/agent_{i}/

    完全なパイプラインを実行:
    1. 技術ロングリスト作成
    2. 検証レポート生成
    3. 修正版作成
    """,
    subagent_type="tech-longlist-pipeline"
)
```

### Phase 3: 進捗監視

**処理内容**:
1. 各エージェントの実行状態を監視
2. 出力ファイルの存在確認
   - {ID}_{組織名}.json（作成済み）
   - {ID}_{組織名}_verified.json（検証済み）
   - verification_report_YYYYMMDD.md
3. エラー検出と記録
4. 完了通知の受信

**監視項目**:
- エージェント実行状態: running / completed / failed
- 処理済み件数: 各エージェントの進捗（JSONファイル数でカウント）
- エラーログ: 失敗した調査対象の記録
- 推定残り時間: 全体の完了予測

### Phase 4: 結果収集と整理

**処理内容**:
1. 全エージェントの完了を確認
2. 各エージェントの出力JSONファイルを収集
3. ファイルの整理とコピー（元のID順に`final_output/`ディレクトリへ）
4. 重複チェック（同じIDのJSONファイルが複数存在しないか）
5. 最終ディレクトリへの統合

**統合Python処理**:
```python
import json
import glob
import shutil
from pathlib import Path

# 各エージェントの検証済みJSONファイルを収集
output_dir = Path('work_dir/output')
final_dir = Path('work_dir/final_output')
final_dir.mkdir(parents=True, exist_ok=True)

# 全エージェントの検証済みJSONを収集
verified_files = []
for agent_dir in sorted(output_dir.glob('agent_*')):
    agent_files = list(agent_dir.glob('*_verified.json'))
    verified_files.extend(agent_files)

print(f"収集ファイル数: {len(verified_files)}件")

# ファイル名でソート（ID順）
verified_files.sort(key=lambda x: x.name)

# final_output/へコピー
for src_file in verified_files:
    dst_file = final_dir / src_file.name
    shutil.copy2(src_file, dst_file)
    print(f"コピー完了: {src_file.name}")

# 重複チェック
file_ids = [f.name.split('_')[0] for f in verified_files]
duplicates = [id for id in file_ids if file_ids.count(id) > 1]
if duplicates:
    print(f"警告: 重複ID検出 - {set(duplicates)}")

print(f"\n統合完了: {final_dir}")
print(f"総件数: {len(verified_files)}件")
```

**出力ディレクトリ**:
- `work_dir/final_output/`: 全エージェントの検証済みJSONファイルを格納

### Phase 5: 品質検証と統合レポート生成

**処理内容**:
1. 統合データの品質チェック
   - 件数検証: 元の調査リスト件数と一致するか
   - ID重複チェック: 同じIDのJSONファイルが複数存在しないか
   - 必須項目チェック: 各JSONファイル内のタイトル、概要などの存在確認
2. 各エージェントの検証レポートを統合
3. 全体統計の計算（各JSONの検証結果から集計）
4. 統合レポート生成

**統合レポート内容**:

```markdown
# 技術ロングリスト オーケストレーション実行レポート

## 実行サマリー

- **元データ**: 調査リスト.xlsx
- **調査対象総数**: 100件
- **起動エージェント数**: 4エージェント
- **処理時間**: 35分12秒
- **成功率**: 98% (98/100件)

## エージェント別実行結果

### Agent 1 (ID: 1-25)
- 処理件数: 25件
- 成功: 25件
- 失敗: 0件
- 処理時間: 33分45秒
- 平均事実性スコア: 85.2点

### Agent 2 (ID: 26-50)
- 処理件数: 25件
- 成功: 24件
- 失敗: 1件 (ID: 38 - 公式サイトアクセス不可)
- 処理時間: 35分12秒
- 平均事実性スコア: 83.8点

### Agent 3 (ID: 51-75)
- 処理件数: 25件
- 成功: 25件
- 失敗: 0件
- 処理時間: 34分18秒
- 平均事実性スコア: 86.5点

### Agent 4 (ID: 76-100)
- 処理件数: 25件
- 成功: 24件
- 失敗: 1件 (ID: 92 - 情報ソース不十分)
- 処理時間: 32分55秒
- 平均事実性スコア: 84.7点

## 品質統計

- **全体平均事実性スコア**: 85.1点 (B評価)
- **A評価 (90点以上)**: 32件 (32%)
- **B評価 (80-89点)**: 48件 (48%)
- **C評価 (70-79点)**: 16件 (16%)
- **D評価 (70点未満)**: 2件 (2%) - 要再調査

## 処理効率

- **単一エージェント想定時間**: 約120分
- **実際の処理時間**: 35分12秒
- **時間削減率**: 71%
- **並列効率**: 85% (理想的な75分に対して)

## 失敗・要注意項目

### 失敗 (2件)
1. ID: 38 - 企業名XYZ - 公式サイトアクセス不可
2. ID: 92 - 企業名ABC - 情報ソース不十分（1件のみ）

### 要注意 (D評価: 2件)
1. ID: 15 - 事実性スコア 68点 - 情報ソースの信頼性要確認
2. ID: 77 - 事実性スコア 67点 - 概要内容に推測が含まれる可能性

## 推奨次ステップ

1. **失敗項目の再調査**: ID 38, 92を手動調査またはキーワード変更して再実行
2. **要注意項目のレビュー**: ID 15, 77の内容を人手で確認
3. **統合ファイルの確認**: 技術ロングリスト_最終統合版.xlsxを開いて最終確認

## 生成ファイル

### 最終成果物
- **work_dir/final_output/** - 全エージェントの検証済みJSONファイルを格納したディレクトリ
  - 001_Company_Name_verified.json
  - 002_Company_Name_verified.json
  - ...
  - 100_Company_Name_verified.json

### エージェント別出力
- work_dir/output/agent_1/
  - 001_Company_Name.json, 001_Company_Name_verified.json
  - 002_Company_Name.json, 002_Company_Name_verified.json
  - ...
- work_dir/output/agent_2/
  - 026_Company_Name.json, 026_Company_Name_verified.json
  - ...
- work_dir/output/agent_3/
  - 051_Company_Name.json, 051_Company_Name_verified.json
  - ...
- work_dir/output/agent_4/
  - 076_Company_Name.json, 076_Company_Name_verified.json
  - ...

### 検証レポート
- work_dir/output/agent_1/verification_report_YYYYMMDD.md
- work_dir/output/agent_2/verification_report_YYYYMMDD.md
- work_dir/output/agent_3/verification_report_YYYYMMDD.md
- work_dir/output/agent_4/verification_report_YYYYMMDD.md

---
生成日時: 2025-01-06 14:30:45
```

## Error Handling & Recovery

### エージェント失敗時の対応

**単一エージェント失敗**:
1. 失敗したエージェントのログを確認
2. 該当範囲のみを再実行
3. 他のエージェントの結果は保持

**複数エージェント失敗**:
1. 共通の原因を分析（ネットワーク、APIレート制限など）
2. 待機後に一括再実行
3. エージェント数を削減して再試行

**部分失敗（一部調査対象のみ失敗）**:
1. 成功分は統合に含める
2. 失敗分はリストアップ
3. ユーザーに手動調査または再実行を提案

## Resource Management

### システムリソース考慮事項

**メモリ使用量**:
- 1エージェント: 約500MB
- 4エージェント並列: 約2GB
- 推奨メモリ: 4GB以上

**ネットワーク負荷**:
- WEB検索API制限を考慮
- エージェント間でレート制限を分散
- 必要に応じてリクエスト間隔を調整

**ディスク容量**:
- 作業ディレクトリ: 約100MB
- ログファイル: 約20MB
- 推奨空き容量: 500MB以上

## Usage Examples

### 基本的な使用方法

```
ユーザー: 調査リスト.xlsxをオーケストレーターで調査して
```

**実行内容**:
1. 調査リスト.xlsxを読み込み
2. 最適エージェント数を自動判定
3. データ分割と並列実行
4. 結果統合とレポート生成

### エージェント数を指定する場合

```
ユーザー: 調査リスト.xlsxを6エージェントで並列調査して
```

**実行内容**:
1. 6エージェントを起動（システムリソースが許容する場合）
2. データを6分割して処理
3. 結果を統合

### 失敗分の再実行

```
ユーザー: ID 38, 92だけ再調査して
```

**実行内容**:
1. 失敗したID専用のExcelファイルを生成
2. 単一エージェントで再実行
3. 既存の統合ファイルに結果をマージ

## Technical Implementation

### Required Python Packages

```python
pandas >= 1.5.0  # Excelファイル分割用
openpyxl >= 3.1.0  # Excelファイル読み書き用
```

### Excel分割スクリプト

ファイル名: `split_excel.py`

```python
import pandas as pd
import sys
import os
from pathlib import Path

def split_excel_for_agents(input_file, num_agents, output_dir='work_dir/input'):
    """
    Excelファイルを複数エージェント用に分割

    Args:
        input_file: 元のExcelファイルパス
        num_agents: エージェント数
        output_dir: 出力ディレクトリ

    Returns:
        分割ファイルのパスリスト
    """
    # 出力ディレクトリ作成
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Excelファイル読み込み
    df = pd.read_excel(input_file)
    total_rows = len(df)

    print(f"総調査対象数: {total_rows}件")
    print(f"起動エージェント数: {num_agents}エージェント")

    # 各エージェントの担当件数を計算
    chunk_size = total_rows // num_agents
    remainder = total_rows % num_agents

    output_files = []
    start_idx = 0

    for i in range(num_agents):
        # 端数を最初のエージェントに割り当て
        end_idx = start_idx + chunk_size + (1 if i < remainder else 0)

        # データ抽出
        chunk = df.iloc[start_idx:end_idx].copy()

        # ファイル出力
        output_file = os.path.join(output_dir, f'調査リスト_エージェント{i+1}.xlsx')
        chunk.to_excel(output_file, index=False)

        output_files.append(output_file)

        print(f"Agent {i+1}: {len(chunk)}件 (ID: {df.iloc[start_idx]['No']}-{df.iloc[end_idx-1]['No']})")

        start_idx = end_idx

    return output_files

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("使用方法: python split_excel.py <input_file> <num_agents>")
        sys.exit(1)

    input_file = sys.argv[1]
    num_agents = int(sys.argv[2])

    split_excel_for_agents(input_file, num_agents)
```

### JSON収集スクリプト

ファイル名: `collect_results.py`

```python
import json
import glob
import shutil
import os
from pathlib import Path

def collect_agent_results(output_dir='work_dir/output', final_dir='work_dir/final_output'):
    """
    各エージェントの検証済みJSONファイルを収集・整理

    Args:
        output_dir: エージェント出力ディレクトリ
        final_dir: 最終出力ディレクトリ

    Returns:
        収集したファイルのリスト
    """
    output_path = Path(output_dir)
    final_path = Path(final_dir)
    final_path.mkdir(parents=True, exist_ok=True)

    # 各エージェントの検証済みJSONファイルを検索
    verified_files = []
    for agent_dir in sorted(output_path.glob('agent_*')):
        agent_files = list(agent_dir.glob('*_verified.json'))
        verified_files.extend(agent_files)

    if not verified_files:
        raise FileNotFoundError(f"検証済みJSONファイルが見つかりません: {output_dir}/agent_*/*_verified.json")

    print(f"収集ファイル数: {len(verified_files)}件")

    # ファイル名でソート（ID順）
    verified_files.sort(key=lambda x: x.name)

    # final_outputへコピー
    collected = []
    for src_file in verified_files:
        dst_file = final_path / src_file.name
        shutil.copy2(src_file, dst_file)

        # 検証結果の統計情報を読み込み
        with open(src_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            score = data.get('検証結果', {}).get('総合スコア', 'N/A')
            company = data.get('組織情報', {}).get('組織名', 'Unknown')
            print(f"コピー完了: {src_file.name} (スコア: {score}点, 組織: {company})")

        collected.append(dst_file)

    # 重複チェック
    file_ids = [f.name.split('_')[0] for f in verified_files]
    duplicates = [id for id in file_ids if file_ids.count(id) > 1]
    if duplicates:
        print(f"\n警告: 重複ID検出 - {set(duplicates)}")

    print(f"\n収集完了: {final_path}")
    print(f"総件数: {len(collected)}件")

    return collected

if __name__ == '__main__':
    collect_agent_results()
```

## Best Practices

### いつオーケストレーターを使うべきか

**推奨ケース**:
- ✅ 調査対象が50件以上
- ✅ 処理時間を短縮したい
- ✅ システムリソースに余裕がある（メモリ4GB以上）

**推奨しないケース**:
- ❌ 調査対象が12件未満（並列効果が薄い）
- ❌ システムリソースが限られている
- ❌ ネットワーク帯域が狭い

### 最適エージェント数の選択

| 調査対象数 | 推奨エージェント数 | 理由 |
|-----------|-----------------|------|
| 1-11件 | 1 | オーケストレーション不要 |
| 12-24件 | 2 | 最小限の並列化 |
| 25-49件 | 3 | バランス型 |
| 50-99件 | 4 | 標準構成 |
| 100-199件 | 5-6 | 高効率 |
| 200件以上 | 6-8 | 最大効率（要リソース確認） |

## Limitations

1. **同時実行数の制限**: システムリソースにより最大8エージェントまで
2. **ネットワーク制約**: WEB検索APIのレート制限により調整が必要な場合あり
3. **ファイルシステム**: 大量の一時ファイル生成により、ディスク容量が必要
4. **エラー伝播**: 1つのエージェントの致命的エラーが他に影響する可能性

## Future Enhancements

- [ ] 動的エージェント数調整（システムリソースに応じた自動スケーリング）
- [ ] リアルタイム進捗表示（Webダッシュボード）
- [ ] 失敗時の自動リトライ機構
- [ ] 優先度ベースのタスク割り当て
- [ ] クラウド実行対応（AWS Lambda、GCP Cloud Functionsなど）
